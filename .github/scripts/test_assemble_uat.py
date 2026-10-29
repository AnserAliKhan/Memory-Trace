"""Tests for assemble_uat.py. Run from the repo root:

    python -m pytest .github/scripts/test_assemble_uat.py
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

import assemble_uat
from assemble_uat import (
    MANIFEST_PATH,
    Git,
    PullRequest,
    assemble,
    build_manifest,
    comment_body,
    commit_manifest,
    select_eligible,
    status_for,
)

BASE = "line1\nline2\nline3\nline4\nline5\nline6\nline7\n"


def sh(cwd: Path, *args: str, when: int | None = None) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    if when is not None:
        env["GIT_COMMITTER_DATE"] = env["GIT_AUTHOR_DATE"] = f"@{when} +0000"
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True,
                          text=True, capture_output=True).stdout.strip()


def commit(cwd: Path, files: dict[str, str | None], msg: str, when: int = 1_000) -> str:
    for path, content in files.items():
        target = cwd / path
        if content is None:
            sh(cwd, "rm", "-q", path)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    sh(cwd, "add", "-A")
    sh(cwd, "commit", "-q", "-m", msg, when=when)
    return sh(cwd, "rev-parse", "HEAD")


def edit(line: int, value: str, text: str = BASE) -> str:
    lines = text.splitlines()
    lines[line - 1] = value
    return "\n".join(lines) + "\n"


@pytest.fixture(autouse=True)
def isolated_git_config(monkeypatch):
    """Ignore the developer's global git config (signing, hooks, identity)."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    sh(tmp_path, "init", "-q", "-b", "main")
    sh(tmp_path, "config", "user.name", "t")
    sh(tmp_path, "config", "user.email", "t@t")
    commit(tmp_path, {"app.txt": BASE, "other.txt": BASE}, "base")
    return tmp_path


def make_pr(repo: Path, number: int, files: dict[str, str | None], when: int,
            base: str = "main", **kw) -> PullRequest:
    sh(repo, "checkout", "-q", "-b", f"pr{number}", base)
    sha = commit(repo, files, f"pr {number}", when=when)
    sh(repo, "checkout", "-q", "main")
    return PullRequest(number=number, title=f"PR {number}", author="dev", head_sha=sha,
                       author_association=kw.pop("author_association", "OWNER"), **kw)


def read(repo: Path, path: str) -> str | None:
    target = repo / path
    return target.read_text() if target.exists() else None


def main_sha(repo: Path) -> str:
    return sh(repo, "rev-parse", "main")


# --------------------------------------------------------------------------- eligibility


def test_select_eligible():
    prs = [
        PullRequest(1, "owner", "a", "s1", author_association="OWNER"),
        PullRequest(2, "collab", "b", "s2", author_association="COLLABORATOR"),
        PullRequest(3, "draft", "a", "s3", draft=True, author_association="OWNER"),
        PullRequest(4, "fork", "x", "s4", author_association="CONTRIBUTOR"),
        PullRequest(5, "fork+label", "x", "s5", author_association="NONE", labels=["uat"]),
        PullRequest(6, "draft fork+label", "x", "s6", draft=True, labels=["uat"]),
    ]
    eligible, excluded = select_eligible(prs)
    assert [pr.number for pr in eligible] == [1, 2, 5]
    assert excluded[3][0] == excluded[4][0] == excluded[6][0] == "pending"
    assert "draft" in excluded[3][1] and "label" in excluded[4][1]


# --------------------------------------------------------------------------- merging


def test_non_conflicting_prs_are_all_included(repo):
    a = make_pr(repo, 1, {"app.txt": edit(1, "A")}, when=200)
    b = make_pr(repo, 2, {"other.txt": edit(7, "B"), "new.txt": "new\n"}, when=100)
    outcome = assemble(Git(repo), main_sha(repo), [a, b])

    assert [pr.number for pr in outcome.included] == [2, 1]  # oldest push first
    assert outcome.not_included == {} and outcome.overrides == []
    assert read(repo, "app.txt").startswith("A\n")
    assert read(repo, "other.txt").endswith("B\n")
    assert read(repo, "new.txt") == "new\n"
    assert sh(repo, "rev-parse", "--abbrev-ref", "HEAD") == "uat"


@pytest.mark.parametrize("newest", [1, 2])
def test_last_pushed_pr_wins_conflicting_lines(repo, newest):
    when = {1: 100, 2: 100}
    when[newest] = 200
    a = make_pr(repo, 1, {"app.txt": edit(4, "FROM-1"), "other.txt": edit(1, "only-1")}, when=when[1])
    b = make_pr(repo, 2, {"app.txt": edit(4, "FROM-2")}, when=when[2])
    outcome = assemble(Git(repo), main_sha(repo), [a, b])

    loser = 3 - newest
    assert {pr.number for pr in outcome.included} == {1, 2}
    assert f"FROM-{newest}" in read(repo, "app.txt")
    assert f"FROM-{loser}" not in read(repo, "app.txt")
    assert read(repo, "other.txt").startswith("only-1\n")  # loser's non-conflicting change kept
    assert outcome.overrides == [{"winner": newest, "loser": loser, "files": ["app.txt"]}]


def test_pr_conflicting_with_main_is_skipped(repo):
    stale = make_pr(repo, 1, {"app.txt": edit(2, "STALE")}, when=300)
    ok = make_pr(repo, 2, {"other.txt": edit(1, "ok")}, when=100)
    commit(repo, {"app.txt": edit(2, "MAIN-MOVED-ON")}, "main moves", when=200)
    outcome = assemble(Git(repo), main_sha(repo), [stale, ok])

    assert [pr.number for pr in outcome.included] == [2]
    state, reason = outcome.not_included[1]
    assert state == "failure" and "conflicts with main" in reason and "app.txt" in reason
    assert "MAIN-MOVED-ON" in read(repo, "app.txt")


def test_unresolvable_conflict_skips_later_pr_cleanly(repo):
    deleter = make_pr(repo, 1, {"app.txt": None}, when=100)
    modifier = make_pr(repo, 2, {"app.txt": edit(3, "MOD")}, when=200)
    outcome = assemble(Git(repo), main_sha(repo), [deleter, modifier])

    assert [pr.number for pr in outcome.included] == [1]
    state, reason = outcome.not_included[2]
    assert state == "failure" and "#1" in reason
    assert outcome.overrides == []
    assert read(repo, "app.txt") is None
    assert sh(repo, "status", "--porcelain") == ""
    assert not (repo / ".git" / "MERGE_HEAD").exists()


# --------------------------------------------------------------------------- manifest / reporting


def test_manifest_is_deterministic_and_reruns_produce_same_tree(repo):
    a = make_pr(repo, 1, {"app.txt": edit(4, "X")}, when=100)
    b = make_pr(repo, 2, {"app.txt": edit(4, "Y")}, when=200)
    draft = PullRequest(3, "PR 3", "dev", "f" * 40, draft=True)
    git = Git(repo)

    trees = []
    for _ in range(2):
        eligible, excluded = select_eligible([a, b, draft])
        outcome = assemble(git, main_sha(repo), eligible)
        outcome.not_included.update(excluded)
        manifest = build_manifest(outcome, [a, b, draft], "o/r")
        commit_manifest(git, manifest)
        trees.append(git.tree("HEAD"))

    assert trees[0] == trees[1]
    on_disk = json.loads(read(repo, MANIFEST_PATH))
    assert on_disk == manifest
    assert [p["number"] for p in on_disk["included"]] == [1, 2]
    assert on_disk["included"][0]["url"] == "https://github.com/o/r/pull/1"
    assert on_disk["not_included"][0]["number"] == 3
    assert on_disk["overrides"] == [{"winner": 2, "loser": 1, "files": ["app.txt"]}]


def test_status_and_comment_text(repo):
    a = make_pr(repo, 1, {"app.txt": edit(4, "X")}, when=100)
    b = make_pr(repo, 2, {"app.txt": edit(4, "Y")}, when=200)
    c = make_pr(repo, 3, {"other.txt": edit(1, "Z")}, when=150)
    outcome = assemble(Git(repo), main_sha(repo), [a, b, c])
    url = "https://uat.refound.pages.dev"

    assert status_for(b, outcome) == ("success", "In UAT; overrides #1")
    assert status_for(a, outcome) == ("success", "In UAT; partly overridden by #2")
    assert status_for(c, outcome) == ("success", "In UAT")
    assert comment_body(c, outcome, url) is None
    assert "Overrides #1 in `app.txt`" in comment_body(b, outcome, url)
    body = comment_body(a, outcome, url)
    assert body.startswith(assemble_uat.COMMENT_MARKER) and "#2 overrides this PR" in body

    outcome.not_included[4] = ("pending", "Not in UAT: draft PR")
    draft = PullRequest(4, "d", "dev", "e" * 40, draft=True)
    assert comment_body(draft, outcome, url) is None


# --------------------------------------------------------------------------- end to end


def test_main_end_to_end(tmp_path, monkeypatch):
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    clone = tmp_path / "clone"
    sh(tmp_path, "init", "-q", "--bare", str(origin))
    work.mkdir()
    sh(work, "init", "-q", "-b", "main")
    commit(work, {"app.txt": BASE}, "base")
    prs = [make_pr(work, 1, {"app.txt": edit(1, "ONE")}, when=100),
           make_pr(work, 2, {"app.txt": edit(1, "TWO")}, when=200),
           make_pr(work, 3, {"app.txt": edit(7, "fork")}, when=300, author_association="NONE")]
    sh(work, "remote", "add", "origin", str(origin))
    sh(work, "push", "-q", "origin", "main",
       *[f"pr{pr.number}:refs/pull/{pr.number}/head" for pr in prs])
    sh(tmp_path, "clone", "-q", str(origin), str(clone))

    writes: list[tuple] = []
    monkeypatch.setattr(assemble_uat.GitHub, "open_prs", lambda self: [
        PullRequest(pr.number, pr.title, pr.author, pr.head_sha,
                    author_association=pr.author_association) for pr in prs])
    monkeypatch.setattr(assemble_uat.GitHub, "_get_all", lambda self, path: [])
    monkeypatch.setattr(assemble_uat.GitHub, "_write",
                        lambda self, method, path, body=None: writes.append((method, path, body)))
    outputs = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(outputs))
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.chdir(clone)

    assert assemble_uat.main(["--repo", "o/r", "--pages-project", "refound"]) == 0
    assert "changed=true" in outputs.read_text()
    uat_app = sh(origin, "show", "uat:app.txt")
    assert uat_app.startswith("TWO") and "fork" not in uat_app
    manifest = json.loads(sh(origin, "show", f"uat:{MANIFEST_PATH}"))
    assert [p["number"] for p in manifest["included"]] == [1, 2]

    statuses = {path.rsplit("/", 1)[-1]: body for method, path, body in writes if "/statuses/" in path}
    assert statuses[prs[1].head_sha]["state"] == "success"
    assert statuses[prs[1].head_sha]["target_url"] == "https://uat.refound.pages.dev"
    assert statuses[prs[2].head_sha]["state"] == "pending"
    comments = [path for method, path, body in writes if path.endswith("/comments")]
    assert comments == ["repos/o/r/issues/1/comments", "repos/o/r/issues/2/comments"]

    # Second run with nothing changed: no new push.
    uat_before = sh(origin, "rev-parse", "uat")
    outputs.write_text("")
    assert assemble_uat.main(["--repo", "o/r"]) == 0
    assert "changed=false" in outputs.read_text()
    assert sh(origin, "rev-parse", "uat") == uat_before
