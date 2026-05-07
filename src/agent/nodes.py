from sqlalchemy.exc import SQLAlchemyError
from langgraph.types import interrupt
from config import settings
from agent.states import AgentState
from agent.status import NodeStatus
from utils.db import (
    get_engine,
    fetch_schema_metadata,
    metadata_to_ddl,
    clone_schema,
    apply_sql_query
)
from agent.classifier.protocol import PromptClassifier, ClassificationStatus
from agent.sql_generation.protocol import SQLGenerator
from agent.evaluation.protocol import SQLReviewer, ReviewStatus
from agent.responses import (
    ClassificationUpdate,
    IntrospectionUpdate,
    SQLGenerationUpdate,
    TestSQLUpdate,
    CriticUpdate,
    HumanReviewUpdate,
    DeployUpdate,
    HumanInterruptResponse,
    HumanReviewPayload
)
from utils.logging import setup_logger


logger = setup_logger(__name__)

def classify_node(state: AgentState, classifier: PromptClassifier):
    logger.info("Classifying user request...")
    user_input = state.user_input
    
    result = classifier.classify(user_input)
    
    if result.status == ClassificationStatus.PROCEED:
        new_status = NodeStatus.CLASSIFIER_PROCEED
    else:
        new_status = NodeStatus.CLASSIFIER_OFF_TOPIC

    update = ClassificationUpdate(
        status=new_status,
        classification_reasoning=result.reasoning,
        classification_message=result.message
    )

    return update

def introspect_db_node(state: AgentState):
    logger.info("Starting introspection...")
    
    engine = get_engine(settings.db_prod.url)

    try:
        metadata = fetch_schema_metadata(engine)
        full_schema = metadata_to_ddl(engine, metadata)
        
        msg = f"Reflected {len(metadata.tables)} tables."
        logger.info(msg)
        update = IntrospectionUpdate(
            status=NodeStatus.SUCCESSFUL_EXTRACTION,
            current_schema=full_schema,
            error_log=None,
            logs=[msg]
        )
        return update
            
    except Exception as e:
        logger.error(f"Introspection failed: {e}")

        update = IntrospectionUpdate(
            status=NodeStatus.FAILED_EXTRACTION,
            error_log=str(e),
            logs=[f"Error: {e}"]
        )

        return update
    finally:
        engine.dispose()

def generate_sql_node(state: AgentState, generator: SQLGenerator):
    current_iteration = state.iterations + 1

    logger.info(f"Generating SQL for: {state.user_input}")

    iterations = state.iterations
    error_log = state.error_log

    retry_msg = f" (Retry {iterations})" if iterations > 0 else ""

    generated_sql = generator.generate(
        current_schema=state.current_schema,
        user_input=state.user_input,
        error_log=error_log
    )
    
    update = SQLGenerationUpdate(
        generated_sql=generated_sql,
        iterations=current_iteration,
        logs=[f"SQL Generated{retry_msg}."]
    )

    return update

def test_sql_node(state: AgentState):
    logger.info("Testing SQL in sandbox...")
    
    prod_engine = get_engine(settings.db_prod.url)
    test_engine = get_engine(settings.db_test.url)
    
    try:
        clone_schema(prod_engine, test_engine)
        
        generated_sql = state.generated_sql
        apply_sql_query(test_engine, generated_sql)

        sandbox_metadata = fetch_schema_metadata(test_engine)
        sandbox_schema = metadata_to_ddl(test_engine, sandbox_metadata)
        
        msg = "Sandbox test passed."
        logger.info(msg)

        update = TestSQLUpdate(
            status=NodeStatus.TEST_SUCCESS,
            sandbox_schema=sandbox_schema,
            error_log=None,
            logs=[msg]
        )

        return update
    
    except SQLAlchemyError as e:
        err_msg = str(e)
        logger.warning(f"SQL Test failed: {err_msg}")

        update = TestSQLUpdate(
            status=NodeStatus.TEST_FAILED_SQL,
            error_log=err_msg,
            logs=[f"Test failed: {err_msg}"]
        )

        return update
    
    except Exception as e:
        err_msg = f"System error during sandbox setup: {e}"
        logger.error(err_msg)
        update = TestSQLUpdate(
            status=NodeStatus.FATAL_SYSTEM_ERROR,
            error_log=err_msg,
            logs=[err_msg]
        )

        return update

    finally:
        prod_engine.dispose()
        test_engine.dispose()

def critic_node(state: AgentState, critic: SQLReviewer):
    logger.info("Critic is reviewing the migration...")
    
    review_result = critic.review(
        user_prompt=state.user_input,
        original_schema=state.current_schema,
        sandbox_schema=state.sandbox_schema,
        generated_sql=state.generated_sql
    )
    
    if review_result.status == ReviewStatus.APPROVED:
        summary_text = review_result.summary or review_result.feedback
        msg = f"Critic approved. Summary: {summary_text}"
        logger.info(msg)

        update = CriticUpdate(
            status=NodeStatus.CRITIC_APPROVED,
            migration_summary=summary_text,
            error_log=None,
            logs=[msg]
        )

        return update
        
    elif review_result.status == ReviewStatus.REJECTED_INTENT:
        err_msg = f"CRITIC REJECTED (Intent mismatch): {review_result.feedback}"
        logger.warning(err_msg)

        update = CriticUpdate(
            status=NodeStatus.CRITIC_REJECTED_INTENT,
            error_log=err_msg,
            logs=[err_msg]
        )

        return update
        
    elif review_result.status == ReviewStatus.REJECTED_SAFETY:
        err_msg = f"CRITIC REJECTED (Safety hazard): {review_result.feedback}"
        logger.warning(err_msg)

        update = CriticUpdate(
            status=NodeStatus.CRITIC_REJECTED_SAFETY,
            error_log=err_msg,
            logs=[err_msg]
        )

        return update
    
    else:
        err_msg = f"Critic failed to provide a valid review: {review_result.feedback}"
        logger.error(err_msg)

        update = CriticUpdate(
            status=NodeStatus.CRITIC_FAILED,
            error_log=err_msg,
            logs=[err_msg]
        )

        return update

def human_review_node(state: AgentState):
    payload = HumanReviewPayload(
        sql=state.generated_sql or "",
        original_schema=state.current_schema or "",
        sandbox_schema=state.sandbox_schema or "",
        migration_summary=state.migration_summary,
        iterations_spent=state.iterations,
        is_stalemate=state.iterations >= settings.max_iterations
    )

    raw_answer = interrupt(payload.model_dump())

    answer = HumanInterruptResponse(**raw_answer)

    if answer.action == "approve":
        update = HumanReviewUpdate(
            status=NodeStatus.HUMAN_APPROVED,
            human_feedback=None
        )

        return update
    
    if answer.action == "reject":
        feedback_msg = f"HUMAN REVIEW FAILED: {answer.feedback}"
        
        update = HumanReviewUpdate(
            status=NodeStatus.HUMAN_REJECTED_WITH_FEEDBACK,
            human_feedback=answer.feedback,
            error_log=feedback_msg,
            logs=[feedback_msg],
            iterations=max(0, state.iterations - 1) 
        )

        return update

    return HumanReviewUpdate(status=NodeStatus.HUMAN_ABORT)

def deploy_node(state: AgentState):
    logger.info("Deploying to production...")
    
    prod_engine = get_engine(settings.db_prod.url)
    try:
        apply_sql_query(prod_engine, state.generated_sql)
        logger.info("Deployment simulated successfully.")

        update = DeployUpdate(
            status=NodeStatus.DEPLOY_SUCCESS,
            logs=["Deployed to production."]
        )

        return update
    
    except SQLAlchemyError as e:
        # Error while applying sql-query to the prod db
        err_msg = str(e)
        logger.error(f"CRITICAL SQL DATA ERROR during deployment: {err_msg}")

        extended_error_log = (
            f"SYNTAX OK, BUT DATA CONFLICT: Your query successfully passed the Sandbox test "
            f"(the syntax and schema are correct), but FAILED during Production deployment "
            f"due to existing data. Production Error: {err_msg}. "
            f"Please adjust the query to handle existing rows safely."
        )

        update = DeployUpdate(
            status=NodeStatus.DEPLOY_FAILED_DATA_CONFLICT, 
            error_log=extended_error_log,
            logs=[f"Prod Data Error: {err_msg}"]
        )

        return update

    except Exception as e:
        logger.error(f"CRITICAL ERROR during deployment: {e}")

        update = DeployUpdate(
            status=NodeStatus.DEPLOY_FAILED_FATAL,
            error_log=str(e)
        )

        return update
    
    finally:
        prod_engine.dispose()
