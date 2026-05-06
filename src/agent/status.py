from enum import Enum

class NodeStatus(str, Enum):
    CLASSIFIER_PROCEED = "classifier_proceed"
    CLASSIFIER_OFF_TOPIC = "classifier_off_topic"
    
    SUCCESSFUL_EXTRACTION = "successful_db_schema_extraction"
    FAILED_EXTRACTION = "failed_db_schema_extraction"

    TEST_SUCCESS = "successful_sandbox_test"
    TEST_FAILED_SQL = "failed_sql_sandbox"

    CRITIC_APPROVED = "critic_approved"
    CRITIC_REJECTED_INTENT = "critic_rejected_intent"
    CRITIC_REJECTED_SAFETY = "critic_rejected_safety"
    CRITIC_FAILED = "critic_system_error"

    HUMAN_APPROVED = "human_approved"
    HUMAN_REJECTED_WITH_FEEDBACK = "human_rejected_with_feedback"
    HUMAN_ABORT = "human_abort"
    
    DEPLOY_SUCCESS = "successful_prod_deploy"
    DEPLOY_FAILED_DATA_CONFLICT = "failed_prod_data_conflict"
    DEPLOY_FAILED_FATAL = "failed_prod_deploy_fatal"
    
    FATAL_SYSTEM_ERROR = "fatal_system_error"

class GraphNode(str, Enum):
    CLASSIFY = "classify"
    INTROSPECT = "introspect"
    GENERATE = "generate"
    TEST = "test"
    CRITIC = "critic"
    HUMAN_REVIEW = "human_review"
    DEPLOY = "deploy"