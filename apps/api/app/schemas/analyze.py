from pydantic import BaseModel, Field

from app.models.domain import AnalysisReport


class AnalyzeRequest(BaseModel):
    url: str | None = Field(default=None, description="GitHub pull request URL")
    demo: bool = Field(default=False, description="Analyze built-in demo fixture")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: str
    service: str


class VersionResponse(BaseModel):
    version: str
    analyzer_version: str
    ai_enabled: bool


# Re-export for OpenAPI
AnalyzeResponse = AnalysisReport
