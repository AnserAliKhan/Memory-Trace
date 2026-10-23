#!/usr/bin/env python3
"""
Rebuild the `uat` branch: main + every eligible open PR targeting main.

Rules (see docs/DEPLOYMENT.md):
  - Eligible: non-draft PRs from the owner/members/collaborators, or any PR a
    maintainer labelled `uat`. A new push to a label-only PR drops the label.
  - A PR that conflicts with main on its own is skipped (it must update first),
    so a stale PR can never revert main in UAT.
  - PRs are merged oldest-push-first with `-X theirs`, so where two PRs change
    the same lines, the most recently pushed one wins. Conflicts git can't
    resolve that way (rename/delete) skip the later PR.
  - frontend/public/uat-manifest.json records what went in; the UAT frontend
    shows it as a banner.

Runs in GitHub Actions (.github/workflows/uat.yml) from main's copy of this file,
never a PR's. Needs only git, gh and the stdlib. Use --dry-run locally: no push,
no GitHub writes.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

UAT_BRANCH = "uat"
UAT_LABEL = "uat"
STATUS_CONTEXT = "uat"
COMMENT_MARKER = "<!-- uat-status -->"
MANIFEST_PATH = "frontend/public/uat-manifest.json"
TRUSTED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"


# --------------------------------------------------------------------------- model


@dataclass
class PullRequest:
    number: int
    title: str
    author: str
    head_sha: str
    draft: bool = False
    author_association: str = "NONE"
    labels: list[str] = field(default_factory=list)

    @property
    def trusted(self) -> bool:
        return self.author_association in TRUSTED_ASSOCIATIONS

    @property
    def ref(self) -> str:
        return f"refs/remotes/pr/{self.number}"

    @classmethod
    def from_api(cls, data: dict) -> "PullRequest":
        return cls(
            number=data["number"],
            title=data.get("title") or "",
            author=(data.get("user") or {}).get("login", ""),
            head_sha=data["head"]["sha"],
            draft=bool(data.get("draft")),
            author_association=data.get("author_association") or "NONE",
            labels=[label["name"] for label in data.get("labels") or []],
        )


@dataclass
class Outcome:
    main_sha: str
    included: list[PullRequest] = field(default_factory=list)
    # number -> (state, reason); state is a commit-status state.
    not_included: dict[int, tuple[str, str]] = field(default_factory=dict)
    # {"winner": int, "loser": int, "files": [str]}
    overrides: list[dict] = field(default_factory=list)


# --------------------------------------------------------------------------- git


class Git:
    def __init__(self, cwd: str | Path = "."):
        self.cwd = str(cwd)

    def run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        proc = subprocess.run(
            ["git", *args], cwd=self.cwd, text=True, capture_output=True
        )
        if check and proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed:\n{proc.stderr.strip()}")
        return proc

    def out(self, *args: str) -> str:
        return self.run(*args).stdout.strip()

    def rev(self, ref: str) -> str | None:
        proc = self.run("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False)
        return proc.stdout.strip() or None

    def tree(self, ref: str) -> str:
        return self.out("rev-parse", f"{ref}^{{tree}}")

    def commit_time(self, ref: str) -> int:
        return int(self.out("log", "-1", "--format=%ct", ref))

    def changed_files(self, base: str, ref: str) -> set[str]:
        return set(filter(None, self.out("diff", "--name-only", f"{base}...{ref}").splitlines()))

    def merge_conflicts(self, ours: str, theirs: str) -> list[str] | None:
        """Files that conflict when merging theirs into ours (no worktree changes).

        Returns [] for a clean merge and None when git can't merge at all
        (e.g. unrelated histories).
        """

        proc = self.run(
            "merge-tree", "--write-tree", "--name-only", "--no-messages", ours, theirs,
            check=False,
        )
        if proc.returncode == 0:
            return []
        if proc.returncode == 1:
            return [line for line in proc.stdout.splitlines()[1:] if line]
        return None


# --------------------------------------------------------------------------- logic


def select_eligible(prs: list[PullRequest]) -> tuple[list[PullRequest], dict[int, tuple[str, str]]]:
    eligible: list[PullRequest] = []
    excluded: dict[int, tuple[str, str]] = {}
    for pr in prs:
        if pr.draft:
            excluded[pr.number] = ("pending", "Not in UAT: draft PR (mark it ready for review)")
        elif not pr.trusted and UAT_LABEL not in pr.labels:
            excluded[pr.number] = ("pending", f"Not in UAT: needs the '{UAT_LABEL}' label from a maintainer")
        else:
            eligible.append(pr)
    return eligible, excluded


def assemble(git: Git, main_sha: str, prs: list[PullRequest]) -> Outcome:
    """Check out `uat` at main_sha and merge eligible PRs, last-pushed winning."""

    outcome = Outcome(main_sha=main_sha)
    candidates: list[PullRequest] = []
    for pr in prs:
        conflicts = git.merge_conflicts(main_sha, pr.head_sha)
        if conflicts is None:
            outcome.not_included[pr.number] = ("failure", "Not in UAT: cannot be merged with main")
        elif conflicts:
            outcome.not_included[pr.number] = (
                "failure",
                "Not in UAT: conflicts with main (" + _files(conflicts) + ") - merge main into this branch",
            )
        else:
            candidates.append(pr)

    candidates.sort(key=lambda pr: (git.commit_time(pr.head_sha), pr.number))
    git.run("checkout", "--quiet", "-B", UAT_BRANCH, main_sha)

    touched: dict[int, set[str]] = {}
    for pr in candidates:
        conflicts = git.merge_conflicts("HEAD", pr.head_sha) or []
        overridden = []
        for earlier in outcome.included:
            if earlier.number not in touched:
                touched[earlier.number] = git.changed_files(main_sha, earlier.head_sha)
            files = sorted(set(conflicts) & touched[earlier.number])
            if files:
                overridden.append({"winner": pr.number, "loser": earlier.number, "files": files})

        merge = git.run(
            "merge", "--no-ff", "--no-edit", "-X", "theirs",
            "-m", f"uat: merge #{pr.number} @ {pr.head_sha[:7]}", pr.head_sha,
            check=False,
        )
        if merge.returncode != 0:
            git.run("merge", "--abort", check=False)
            git.run("reset", "--quiet", "--hard", "HEAD", check=False)
            with_prs = ", ".join(f"#{o['loser']}" for o in overridden) or "PRs already in UAT"
            outcome.not_included[pr.number] = (
                "failure",
                f"Not in UAT: rename/delete conflict with {with_prs} that git can't auto-resolve ("
                + _files(conflicts) + ")",
            )
            continue

        outcome.included.append(pr)
        outcome.overrides.extend(overridden)
    return outcome


def build_manifest(outcome: Outcome, prs: list[PullRequest], repo: str) -> dict:
    """Deterministic (no timestamps) so an unchanged UAT produces an identical tree."""

    by_number = {pr.number: pr for pr in prs}

    def info(pr: PullRequest) -> dict:
        return {
            "number": pr.number,
            "title": pr.title,
            "author": pr.author,
            "sha": pr.head_sha,
            "url": f"https://github.com/{repo}/pull/{pr.number}",
        }

    return {
        "branch": UAT_BRANCH,
        "main_sha": outcome.main_sha,
        "included": [info(pr) for pr in outcome.included],
        "not_included": [
            {**info(by_number[number]), "reason": reason}
            for number, (_state, reason) in sorted(outcome.not_included.items())
        ],
        "overrides": outcome.overrides,
    }


def commit_manifest(git: Git, manifest: dict) -> None:
    path = Path(git.cwd) / MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    git.run("add", "--force", MANIFEST_PATH)  # gitignored on main
    git.run("commit", "--quiet", "--allow-empty", "-m", "uat: update manifest")


def status_for(pr: PullRequest, outcome: Outcome) -> tuple[str, str]:
    if pr.number in outcome.not_included:
        return outcome.not_included[pr.number]
    beats = sorted({o["loser"] for o in outcome.overrides if o["winner"] == pr.number})
    beaten_by = sorted({o["winner"] for o in outcome.overrides if o["loser"] == pr.number})
    parts = ["In UAT"]
    if beats:
        parts.append("overrides " + ", ".join(f"#{n}" for n in beats))
    if beaten_by:
        parts.append("partly overridden by " + ", ".join(f"#{n}" for n in beaten_by))
    return "success", "; ".join(parts)


def comment_body(pr: PullRequest, outcome: Outcome, uat_url: str) -> str | None:
    """Sticky comment text, or None when there's nothing worth explaining."""

    state, description = status_for(pr, outcome)
    beats = [o for o in outcome.overrides if o["winner"] == pr.number]
    beaten_by = [o for o in outcome.overrides if o["loser"] == pr.number]
    # Drafts / unlabelled forks (pending) are explained by the commit status alone.
    if state == "pending" or (state == "success" and not beats and not beaten_by):
        return None

    where = f"[UAT]({uat_url})" if uat_url else "UAT"
    lines = [COMMENT_MARKER, f"**UAT status** for `{pr.head_sha[:7]}`", ""]
    if state == "success":
        lines.append(f"✅ Included in {where}.")
    else:
        lines.append(f"⚠️ {description}.")
    for o in beats:
        lines.append(f"- Overrides #{o['loser']} in {_code_list(o['files'])} (this PR was pushed more recently).")
    for o in beaten_by:
        lines.append(
            f"- #{o['winner']} overrides this PR in {_code_list(o['files'])} "
            "(it was pushed more recently). Push again to take precedence, or test those parts in this PR's own preview."
        )
    lines += ["", "_Updated automatically by the UAT workflow. See docs/DEPLOYMENT.md._"]
    return "\n".join(lines)


def _files(files: list[str], limit: int = 3) -> str:
    shown = ", ".join(files[:limit])
    return shown + (f" +{len(files) - limit} more" if len(files) > limit else "")


def _code_list(files: list[str]) -> str:
    return ", ".join(f"`{f}`" for f in files)


# --------------------------------------------------------------------------- GitHub


class GitHub:
    def __init__(self, repo: str, dry_run: bool):
        self.repo = repo
        self.dry_run = dry_run

    def _api(self, *args: str, body: dict | None = None) -> str:
        proc = subprocess.run(
            ["gh", "api", *args] + (["--input", "-"] if body is not None else []),
            input=json.dumps(body) if body is not None else None,
            text=True, capture_output=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"gh api {' '.join(args)} failed:\n{proc.stderr.strip()}")
        return proc.stdout

    def _get_all(self, path: str) -> list[dict]:
        out = self._api("--paginate", path, "--jq", ".[]")
        return [json.loads(line) for line in out.splitlines() if line.strip()]

    def _write(self, method: str, path: str, body: dict | None = None) -> None:
        if self.dry_run:
            print(f"[dry-run] {method} {path} {json.dumps(body) if body else ''}")
            return
        self._api("--method", method, path, body=body)

    def open_prs(self) -> list[PullRequest]:
        data = self._get_all(f"repos/{self.repo}/pulls?state=open&base=main&per_page=100")
        return [PullRequest.from_api(d) for d in data]

    def remove_label(self, number: int, label: str) -> None:
        self._write("DELETE", f"repos/{self.repo}/issues/{number}/labels/{label}")

    def set_status(self, sha: str, state: str, description: str, target_url: str) -> None:
        body = {"state": state, "context": STATUS_CONTEXT, "description": description[:140]}
        if target_url:
            body["target_url"] = target_url
        self._write("POST", f"repos/{self.repo}/statuses/{sha}", body)

    def upsert_comment(self, number: int, body: str | None, fallback: str) -> None:
        """Create/update the sticky comment.

        body None means nothing to explain: post nothing, but rewrite an existing
        comment to `fallback` so it doesn't keep showing a stale conflict.
        """

        comments = self._get_all(f"repos/{self.repo}/issues/{number}/comments?per_page=100")
        existing = next(
            (c for c in comments
             if COMMENT_MARKER in (c.get("body") or "") and (c.get("user") or {}).get("login") == BOT_NAME),
            None,
        )
        if existing is None:
            if body is not None:
                self._write("POST", f"repos/{self.repo}/issues/{number}/comments", {"body": body})
            return
        if body is None:
            body = f"{COMMENT_MARKER}\n{fallback}"
        if existing.get("body") != body:
            self._write("PATCH", f"repos/{self.repo}/issues/comments/{existing['id']}", {"body": body})


# --------------------------------------------------------------------------- main


def drop_label_on_untrusted_push(prs: list[PullRequest], github: GitHub) -> None:
    """A new push to a label-only PR needs fresh maintainer review."""

    if os.environ.get("EVENT_ACTION") != "synchronize":
        return
    number = int(os.environ.get("EVENT_PR_NUMBER") or 0)
    for pr in prs:
        if pr.number == number and not pr.trusted and UAT_LABEL in pr.labels:
            print(f"#{number}: new push from a non-collaborator; removing '{UAT_LABEL}' label")
            github.remove_label(number, UAT_LABEL)
            pr.labels.remove(UAT_LABEL)


def write_outputs(changed: bool, sha: str, outcome: Outcome, prs: list[PullRequest]) -> None:
    if path := os.environ.get("GITHUB_OUTPUT"):
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"changed={'true' if changed else 'false'}\nsha={sha}\n")
    lines = [
        f"## UAT {'updated' if changed else 'unchanged'} - main@{outcome.main_sha[:7]}",
        "", "| PR | Status |", "|---|---|",
    ]
    for pr in prs:
        lines.append(f"| #{pr.number} {pr.title} | {status_for(pr, outcome)[1]} |")
    summary = "\n".join(lines)
    print(summary)
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(summary + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", default=os.environ.get("REPO") or os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--pages-project", default=os.environ.get("PAGES_PROJECT", ""))
    parser.add_argument("--dry-run", action="store_true", help="no push, no GitHub writes")
    args = parser.parse_args(argv)
    if not args.repo:
        parser.error("--repo (or REPO / GITHUB_REPOSITORY) is required")

    git = Git()
    if git.out("status", "--porcelain", "--untracked-files=no"):
        parser.error("working tree has uncommitted changes; run in a clean checkout")
    github = GitHub(args.repo, args.dry_run)
    uat_url = f"https://{UAT_BRANCH}.{args.pages_project}.pages.dev" if args.pages_project else ""

    for key, value in (("user.name", BOT_NAME), ("user.email", BOT_EMAIL)):
        if git.run("config", key, check=False).returncode != 0:
            git.run("config", key, value)

    prs = sorted(github.open_prs(), key=lambda pr: pr.number)
    drop_label_on_untrusted_push(prs, github)
    eligible, excluded = select_eligible(prs)

    refspecs = ["+refs/heads/main:refs/remotes/origin/main"]
    refspecs += [f"+refs/pull/{pr.number}/head:{pr.ref}" for pr in eligible]
    git.run("fetch", "--quiet", "--no-tags", "origin", *refspecs)
    git.run("fetch", "--quiet", "--no-tags", "origin",
            f"+refs/heads/{UAT_BRANCH}:refs/remotes/origin/{UAT_BRANCH}", check=False)
    for pr in eligible:
        # The ref is the truth: the PR may have been pushed after we listed it.
        pr.head_sha = git.rev(pr.ref) or pr.head_sha

    main_sha = git.rev("refs/remotes/origin/main")
    outcome = assemble(git, main_sha, eligible)
    outcome.not_included.update(excluded)
    commit_manifest(git, build_manifest(outcome, prs, args.repo))

    new_sha = git.rev("HEAD")
    old_sha = git.rev(f"refs/remotes/origin/{UAT_BRANCH}")
    changed = old_sha is None or git.tree(old_sha) != git.tree(new_sha)
    if changed and not args.dry_run:
        lease = f"refs/heads/{UAT_BRANCH}:{old_sha or ''}"
        git.run("push", "--quiet", f"--force-with-lease={lease}", "origin", f"HEAD:refs/heads/{UAT_BRANCH}")

    for pr in prs:
        state, description = status_for(pr, outcome)
        github.set_status(pr.head_sha, state, description, uat_url)
        icon = "✅" if state == "success" else "ℹ️"
        github.upsert_comment(pr.number, comment_body(pr, outcome, uat_url), f"{icon} {description}.")

    write_outputs(changed, new_sha, outcome, prs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
