from app.core.config import Settings
from app.github.normalizer import normalize_changed_file, normalize_pull_request
from app.models.enums import FileRole, FileStatus
from app.services.demo import load_fixture


def test_normalize_changed_file_detects_test_and_python():
    raw = {
        "filename": "tests/test_foo.py",
        "status": "added",
        "additions": 3,
        "deletions": 0,
        "changes": 3,
        "patch": "+def test_foo():\n+    assert True\n",
    }
    file = normalize_changed_file(raw, max_patch_size=10_000)
    assert file.language == "Python"
    assert file.is_test_file is True
    assert file.role == FileRole.TEST
    assert file.status == FileStatus.ADDED


def test_normalize_pull_request_from_fixture():
    data = load_fixture("small_python_pr")
    settings = Settings(max_files=100)
    pr, partial, msg = normalize_pull_request(
        data["pull_request"], data["files"], data.get("commits", []), settings
    )
    assert pr.number == 12
    assert pr.owner == "acme"
    assert pr.repository == "widgets"
    assert len(pr.changed_files) == 2
    assert partial is False
    assert msg is None


def test_normalize_respects_max_files():
    data = load_fixture("large_pr")
    settings = Settings(max_files=50)
    pr, partial, msg = normalize_pull_request(
        data["pull_request"], data["files"], [], settings
    )
    assert len(pr.changed_files) == 50
    assert partial is True
    assert msg is not None
    assert "50 of" in msg
