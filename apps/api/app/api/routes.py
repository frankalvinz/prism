from fastapi import APIRouter, Depends, Request

from app.api.deps import get_cache, get_github_client_factory, get_viewer
from app.api.errors import auth_expired_response
from app.core.config import get_settings
from app.core.constants import API_PREFIX
from app.core.exceptions import GitHubAuthError, InvalidUrlError
from app.core.session import ViewerSession
from app.github.url_parser import parse_github_pr_url
from app.providers import get_analysis_provider
from app.schemas import AnalyzeRequest, HealthResponse, VersionResponse
from app.services.demo import demo_github_client
from app.services.orchestrator import AnalysisOrchestrator

router = APIRouter(prefix=API_PREFIX)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="prism-api")


@router.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    settings = get_settings()
    return VersionResponse(
        version=settings.app_version,
        analyzer_version=settings.analyzer_version,
        ai_enabled=settings.ai_enabled,
    )


@router.post("/analyze")
async def analyze(
    body: AnalyzeRequest,
    request: Request,
    viewer: ViewerSession | None = Depends(get_viewer),  # noqa: B008
    client_factory=Depends(get_github_client_factory),  # noqa: B008
):
    settings = get_settings()
    cache = get_cache(request)
    provider = get_analysis_provider(
        ai_enabled=settings.ai_enabled,
        provider_name=settings.ai_provider,
    )

    if body.demo:
        github = demo_github_client()
        try:
            orch = AnalysisOrchestrator(
                github=github,
                settings=settings,
                cache=cache,
                ai_provider=provider,
            )
            return await orch.analyze("prism-demo", "sample-repo", 1)
        finally:
            await github.aclose()

    if not body.url:
        raise InvalidUrlError("Provide a GitHub PR URL or set demo=true.")

    parsed = parse_github_pr_url(body.url)
    github = client_factory(settings)
    try:
        orch = AnalysisOrchestrator(
            github=github,
            settings=settings,
            cache=cache,
            ai_provider=provider,
            viewer_login=viewer.login if viewer is not None else None,
        )
        return await orch.analyze(parsed.owner, parsed.repo, parsed.number)
    except GitHubAuthError as exc:
        return auth_expired_response(exc)
    finally:
        await github.aclose()
