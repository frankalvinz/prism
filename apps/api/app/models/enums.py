from enum import Enum


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(str, Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    API = "api"
    DEPENDENCIES = "dependencies"
    CONFIGURATION = "configuration"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    PAYMENTS = "payments"
    DATA_HANDLING = "data_handling"
    CI_CD = "ci_cd"
    ENVIRONMENT = "environment"
    COMPLEXITY = "complexity"
    TESTING = "testing"
    CHANGE = "change"
    IMPACT = "impact"
    OTHER = "other"


class FindingSource(str, Enum):
    DETERMINISTIC = "deterministic"
    AI = "ai"


class FileStatus(str, Enum):
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    RENAMED = "renamed"
    COPIED = "copied"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


class FileRole(str, Enum):
    SOURCE = "source"
    TEST = "test"
    CONFIG = "config"
    DEPENDENCY = "dependency"
    DOCUMENTATION = "documentation"
    GENERATED = "generated"
    MIGRATION = "migration"
    OTHER = "other"


class FileArea(str, Enum):
    UI = "ui"
    API = "api"
    SERVICE = "service"
    DATA_MODEL = "data_model"
    DATABASE = "database"
    AUTH = "auth"
    CONFIG = "config"
    INFRA = "infra"
    CI = "ci"
    TEST = "test"
    DOCS = "docs"
    STYLES = "styles"
    DEPENDENCY = "dependency"
    CONSTANTS = "constants"
    HOOKS_STATE = "hooks_state"
    OTHER = "other"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
