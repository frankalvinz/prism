from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import (
    FileArea,
    FileRole,
    FileStatus,
    FindingSource,
    RiskCategory,
    RiskLevel,
    Severity,
)


class PullRequestCommit(BaseModel):
    sha: str
    message: str
    author: str | None = None
    committed_at: datetime | None = None


class ChangedFile(BaseModel):
    filename: str
    status: FileStatus
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: str | None = None
    previous_filename: str | None = None
    language: str | None = None
    is_test_file: bool = False
    is_generated_file: bool = False
    is_binary: bool = False
    role: FileRole = FileRole.OTHER
    area: FileArea = FileArea.OTHER


class OpenPullRequest(BaseModel):
    owner: str
    repo: str
    number: int
    title: str
    html_url: str
    author_login: str | None = None
    author_avatar_url: str | None = None
    draft: bool = False
    comments: int = 0
    labels: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PullRequest(BaseModel):
    id: int
    number: int
    title: str
    description: str | None = None
    author: str
    repository: str
    owner: str
    base_branch: str
    head_branch: str
    head_sha: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    state: str
    additions: int = 0
    deletions: int = 0
    changed_files_count: int = 0
    commits: list[PullRequestCommit] = Field(default_factory=list)
    changed_files: list[ChangedFile] = Field(default_factory=list)
    html_url: str
    is_private: bool = False


class RiskFinding(BaseModel):
    id: str
    severity: Severity
    category: RiskCategory
    title: str
    description: str
    file: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    source: FindingSource = FindingSource.DETERMINISTIC
    recommendation: str | None = None
    files: list[str] = Field(default_factory=list)


class DependencyChange(BaseModel):
    name: str
    change_type: str  # added | removed | updated
    ecosystem: str
    old_version: str | None = None
    new_version: str | None = None
    file: str


class DependencyEdge(BaseModel):
    source: str
    target: str
    relationship: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class ChangeStatistics(BaseModel):
    total_files: int = 0
    additions: int = 0
    deletions: int = 0
    net_change: int = 0
    files_added: int = 0
    files_modified: int = 0
    files_deleted: int = 0
    files_renamed: int = 0
    binary_files: int = 0
    file_type_distribution: dict[str, int] = Field(default_factory=dict)
    language_distribution: dict[str, int] = Field(default_factory=dict)
    role_distribution: dict[str, int] = Field(default_factory=dict)
    area_distribution: dict[str, int] = Field(default_factory=dict)
    area_churn: dict[str, dict[str, int]] = Field(default_factory=dict)


class ComplexityObservation(BaseModel):
    file: str
    language: str
    function_count: int = 0
    class_count: int = 0
    max_nesting_depth: int = 0
    max_cyclomatic_complexity: int | None = None
    large_functions: list[str] = Field(default_factory=list)
    complex_functions: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class TestingAnalysis(BaseModel):
    test_files_added: int = 0
    test_files_modified: int = 0
    test_files_deleted: int = 0
    production_files_changed: int = 0
    test_to_source_ratio: float | None = None
    test_directory_present: bool = False
    frameworks_detected: list[str] = Field(default_factory=list)
    findings: list[RiskFinding] = Field(default_factory=list)


class ActionItem(BaseModel):
    priority: int = 1
    title: str
    detail: str
    files: list[str] = Field(default_factory=list)


class ReviewSummary(BaseModel):
    risk_level: RiskLevel = RiskLevel.LOW
    headline: str = ""
    overview: str = ""
    highlights: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)


class AIAnalysis(BaseModel):
    summary: str | None = None
    key_changes: list[str] = Field(default_factory=list)
    risk_observations: list[str] = Field(default_factory=list)
    testing_observations: list[str] = Field(default_factory=list)
    review_questions: list[str] = Field(default_factory=list)
    additional_findings: list[RiskFinding] = Field(default_factory=list)
    provider: str
    model: str | None = None
    generated_at: datetime


class AnalysisReport(BaseModel):
    pr: PullRequest
    summary: str
    statistics: ChangeStatistics
    complexity: list[ComplexityObservation] = Field(default_factory=list)
    risks: list[RiskFinding] = Field(default_factory=list)
    testing: TestingAnalysis
    dependencies: list[DependencyChange] = Field(default_factory=list)
    dependency_edges: list[DependencyEdge] = Field(default_factory=list)
    review_questions: list[str] = Field(default_factory=list)
    analyzed_at: datetime
    analyzer_version: str
    partial: bool = False
    partial_message: str | None = None
    files_analyzed: int = 0
    files_total: int = 0
    ai_analysis: AIAnalysis | None = None
    review: ReviewSummary | None = None
