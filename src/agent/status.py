from enum import Enum

class NodeStatus(str, Enum):
    CLASSIFIER_PROCEED = "classifier_proceed"
    CLASSIFIER_OFF_TOPIC = "classifier_off_topic"

    CRITIC_APPROVED = "critic_approved"
    CRITIC_REJECTED = "critic_rejected"

    HUMAN_APPROVED = "human_approved"
    HUMAN_REJECTED_WITH_FEEDBACK = "human_rejected_with_feedback"
    HUMAN_ABORT = "human_abort"
    
    DEPLOY_SUCCESS = "successful_prod_deploy"
    DEPLOY_FAILED_DATA_CONFLICT = "failed_prod_data_conflict"
    DEPLOY_FAILED_FATAL = "failed_prod_deploy_fatal"
    
    FATAL_SYSTEM_ERROR = "fatal_system_error"

class GraphNode(str, Enum):
    CLASSIFY = "classify"
    AGENT="agent"
    TOOLS="tools"
    HUMAN_REVIEW = "human_review"

class ToolOutcome(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    DATA_CONFLICT = "data_conflict"
    FATAL = "fatal"