from app.providers.base import (
    AnalysisProvider,
    DeterministicAnalysisProvider,
    NullAnalysisProvider,
)


def get_analysis_provider(*, ai_enabled: bool, provider_name: str) -> AnalysisProvider:
    if not ai_enabled:
        return NullAnalysisProvider()
    if provider_name in {"deterministic", "null"}:
        return DeterministicAnalysisProvider()
    # Future: ollama, openai, anthropic
    return DeterministicAnalysisProvider()


__all__ = [
    "AnalysisProvider",
    "DeterministicAnalysisProvider",
    "NullAnalysisProvider",
    "get_analysis_provider",
]
