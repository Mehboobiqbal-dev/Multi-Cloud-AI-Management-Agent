# Schemas package initialization

# Import all schemas for easier access
from schemas.base import (
    BaseSchema, 
    BaseResponseSchema, 
    PaginatedResponseSchema, 
    ErrorResponseSchema,
    TokenSchema,
    PaginationQuerySchema,
    SortQuerySchema
)

from schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDB,
    User,
    UserResponse,
    UsersResponse
)

from schemas.cloud_credential import (
    CloudCredentialBase,
    AWSCredentialCreate,
    AzureCredentialCreate,
    GCPCredentialCreate,
    CloudCredentialCreate,
    CloudCredentialUpdate,
    CloudCredential,
    CloudCredentialResponse,
    CloudCredentialsResponse
)

from schemas.audit_log import (
    AuditLogBase,
    AuditLogCreate,
    AuditLog,
    AuditLogResponse,
    AuditLogsResponse
)

from schemas.plan_history import (
    PlanHistoryBase,
    StepExecution,
    PlanHistoryCreate,
    PlanHistoryUpdate,
    FeedbackCreate,
    PlanHistory,
    PlanHistoryResponse,
    PlanHistoriesResponse
)

from schemas.auth import (
    LoginRequest,
    GoogleLoginRequest,
    LoginResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest
)

from schemas.prompt import (
    PromptRequest,
    Step,
    PromptResponse,
    PlanExecutionRequest,
    AgentStateRequest,
    AgentRunResponse,
    FeedbackRequest
)

from schemas.browsing import (
    UpworkJobRequest,
    FiverrJobRequest,
    LinkedInJobRequest,
    BrowsingRequest,
    BrowsingResponse,
    ToolCallRequest
)

from schemas.form_automation import (
    BatchJobRequest,
    RegistrationRequest,
    LoginAutomationRequest
)