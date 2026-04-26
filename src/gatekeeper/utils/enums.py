from enum import StrEnum


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Confidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Category(StrEnum):
    SAST = "sast"
    DEPENDENCY = "dependency"
    SECRET = "secret"


class Decision(StrEnum):
    BLOCK = "BLOCK"
    WARN = "WARN"
    ALLOW = "ALLOW"
