from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class CategoryEnum(str, Enum):
    BILLING = "Billing"
    LOGIN = "Login"
    PERFORMANCE = "Performance"
    BUG = "Bug"
    QUESTION = "Question/How-To"


class SeverityEnum(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class IssueTypeEnum(str, Enum):
    KNOWN_ISSUE = "known_issue"
    NEW_ISSUE = "new_issue"


class KnownIssue(BaseModel):
    id: str
    title: str
    similarity_score: float


class TriageRequest(BaseModel):
    description: str = Field(..., description="Support ticket description")


class TriageResponse(BaseModel):
    summary: str
    category: CategoryEnum
    severity: SeverityEnum
    issue_type: IssueTypeEnum
    related_issues: List[KnownIssue]
    next_action: str


class ErrorResponse(BaseModel):
    error: str
    detail: str