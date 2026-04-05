"""Models package — import all models so SQLAlchemy registers them."""

from app.models.user import User, UserRole  # noqa: F401
from app.models.case import (  # noqa: F401
    Case, CaseStage, CaseStageHistory, InternalNote,
    StageApproval, CaseAssignment, ApprovalStatus,
    STAGES_ORDER, GATED_STAGES,
)
from app.models.entity_rule import EntityRule  # noqa: F401
from app.models.audit import (  # noqa: F401
    AuditLog, AuditAction,
    Notification, NotificationType,
)
from app.models.contact import Contact  # noqa: F401
from app.models.campaign import (  # noqa: F401
    Campaign, CampaignStatus, ContentType, TargetAudience,
)
from app.models.entity_contact import EntityContact  # noqa: F401
from app.models.broker import Broker  # noqa: F401
from app.models.business import Business  # noqa: F401
