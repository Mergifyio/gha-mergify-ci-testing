import os
import subprocess
from pathlib import Path

import pytest

# Hardcoded locations relative to this file
THIS_DIR = Path(__file__).parent
SCRIPT_PATH = (THIS_DIR.parent / "run.sh").resolve()
MOCK_PATH = (THIS_DIR / "mocks").resolve()


def build_body_with_base_sha(base_sha, pr_nums=None):
    """Build a merge queue PR body with checking_base_sha and optional pull requests."""
    if pr_nums is None:
        pr_nums = [12345]

    lines = [
        "<!---",
        "DO NOT EDIT",
        "-*- Mergify Payload -*-",
        '{"merge-queue-pr": true}',
        "-*- Mergify Payload End -*-",
        "-->",
        "",
        "```yaml",
        "---",
        f"checking_base_sha: {base_sha}",
        "previous_failed_batches: []",
        "pull_requests:"
    ]
    lines += [f"  - number: {n}" for n in pr_nums]
    lines += ["```"]

    return "\n".join(lines)


def print_stdx(proc):
    # Print captured output to help debugging
    print(f"EXIT CODE: {proc.returncode}")
    print("------ STDOUT ------")
    print(proc.stdout or "<empty>")
    print("------ STDERR ------")
    print(proc.stderr or "<empty>")
    print("--------------------")


@pytest.mark.parametrize(
    "base_sha,expected_success",
    [
        pytest.param(
            "9853b3c3c5563d8bab57dc0521d70263115da5ff",
            True,
            id="valid_sha"
        ),
        pytest.param(
            "abc123def456",
            True,
            id="short_sha"
        ),
        pytest.param(
            "0000000000000000000000000000000000000000",
            True,
            id="zero_sha"
        ),
    ],
)
def test_extract_base_sha(base_sha, expected_success, monkeypatch, tmp_path):
    """Test that the script correctly extracts checking_base_sha from merge queue PR body."""
    workdir = Path(tmp_path)
    logfile = workdir / "gh_calls.log"
    logfile.write_text("", encoding="utf-8")

    # Create a mock GITHUB_OUTPUT file
    github_output = workdir / "github_output"
    github_output.write_text("", encoding="utf-8")

    monkeypatch.setenv("PATH", f"{MOCK_PATH}:{os.environ.get('PATH', '')}")
    monkeypatch.setenv("MERGE_QUEUE_PR_URL", "https://example.com/repo/pull/9999")
    monkeypatch.setenv("REPOSITORY_URL", "https://example.com/repo")
    monkeypatch.setenv("MOCK_LOG_FILE", str(logfile))
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    monkeypatch.setenv("MERGE_QUEUE_PR_BODY", build_body_with_base_sha(base_sha))

    proc = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd(),
        text=True,
    )

    if expected_success:
        if proc.returncode != 0:
            print_stdx(proc)
        assert proc.returncode == 0

        # Check that the base SHA was written to GITHUB_OUTPUT
        output_content = github_output.read_text()
        expected_line = f"checking_base_sha={base_sha}"
        assert expected_line in output_content

        # Check that success message was printed
        assert f"Extracted checking_base_sha: {base_sha}" in proc.stdout
    else:
        assert proc.returncode != 0


def test_missing_base_sha(monkeypatch, tmp_path):
    """Test that the script fails when checking_base_sha is missing from the YAML."""
    workdir = Path(tmp_path)
    logfile = workdir / "gh_calls.log"
    logfile.write_text("", encoding="utf-8")

    github_output = workdir / "github_output"
    github_output.write_text("", encoding="utf-8")

    # Body without checking_base_sha
    body = """```yaml
---
previous_failed_batches: []
pull_requests:
  - number: 12345
```"""

    monkeypatch.setenv("PATH", f"{MOCK_PATH}:{os.environ.get('PATH', '')}")
    monkeypatch.setenv("MERGE_QUEUE_PR_URL", "https://example.com/repo/pull/9999")
    monkeypatch.setenv("REPOSITORY_URL", "https://example.com/repo")
    monkeypatch.setenv("MOCK_LOG_FILE", str(logfile))
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    monkeypatch.setenv("MERGE_QUEUE_PR_BODY", body)

    proc = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd(),
        text=True,
    )

    # Should fail with error message
    assert proc.returncode != 0
    assert "checking_base_sha not found in merge queue metadata" in proc.stdout
