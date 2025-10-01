# tests/test_repo_miner.py

import os
import pandas as pd
import pytest
from datetime import datetime, timedelta
from src.repo_miner import fetch_commits
from src.repo_miner import fetch_issues
import re

# --- Helpers for dummy GitHub API objects ---

class DummyAuthor:
    def __init__(self, name, email, date):
        self.name = name
        self.email = email
        self.date = date

class DummyCommitCommit:
    def __init__(self, author, message):
        self.author = author
        self.message = message

class DummyCommit:
    def __init__(self, sha, author, email, date, message):
        self.sha = sha
        self.commit = DummyCommitCommit(DummyAuthor(author, email, date), message)

class DummyUser:
    def __init__(self, login):
        self.login = login

class DummyIssue:
    def __init__(self, id_, number, title, user, state, created_at, closed_at, comments, is_pr=False):
        self.id = id_
        self.number = number
        self.title = title
        self.user = DummyUser(user)
        self.state = state
        self.created_at = created_at
        self.closed_at = closed_at
        self.comments = comments
        # attribute only on pull requests
        self.pull_request = DummyUser("pr") if is_pr else None

class DummyRepo:
    def __init__(self, commits, issues):
        self._commits = commits
        self._issues = issues

    def get_commits(self):
        return self._commits

    def get_issues(self, state="all"):
        # filter by state
        if state == "all":
            return self._issues
        return [i for i in self._issues if i.state == state]

class DummyGithub:
    def __init__(self, token):
        assert token == "fake-token"
    def get_repo(self, repo_name):
        # ignore repo_name; return repo set in test fixture
        return self._repo

@pytest.fixture(autouse=True)
def patch_env_and_github(monkeypatch):
    # Set fake token
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    # Patch Github class
    import src.repo_miner as rm
    monkeypatch.setattr(rm, "Github", lambda token: gh_instance)
    gh_instance._repo = DummyRepo([], [])
    yield
    # TODO

# Helper global placeholder
gh_instance = DummyGithub("fake-token")

# --- Tests for fetch_commits ---
# An example test case
def test_fetch_commits_basic(monkeypatch):
    # Setup dummy commits
    now = datetime.now()
    commits = [
        DummyCommit("sha1", "Alice", "a@example.com", now, "Initial commit\nDetails"),
        DummyCommit("sha2", "Bob", "b@example.com", now - timedelta(days=1), "Bug fix")
    ]
    gh_instance._repo = DummyRepo(commits, [])
    df = fetch_commits("any/repo")
    assert list(df.columns) == ["sha", "author", "email", "date", "message"]
    assert len(df) == 2
    assert df.iloc[0]["message"] == "Initial commit"

def test_fetch_commits_limit(monkeypatch):
    # More commits than max_commits
    # TODO： Test that fetch_commits respects the max_commits limit.
    now = datetime.now()
    commits = [#fake commit data
        DummyCommit(f"sha{i}", "Dev", f"d{i}@ex.com", now - timedelta(minutes=i), f"Msg {i}")
        for i in range(10)
    ]
    gh_instance._repo = DummyRepo(commits, [])

    df = fetch_commits("any/repo", max_commits=3)
    assert len(df) == 3
    assert list(df["sha"]) == ["sha0", "sha1", "sha2"]

def test_fetch_commits_empty(monkeypatch):
    gh_instance._repo = DummyRepo([],[])
    df = fetch_commits("any/repo")
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert list(df.columns) == ["sha", "author", "email", "date", "message"]

def test_fetch_issues_iso(monkeypatch):
    now = datetime.now()
    issues = [
        DummyIssue(1, 101, "Issue A", "alice", "open", now, None, 0),
        DummyIssue(2, 102, "Issue B", "bob", "closed", now - timedelta(days=2), now, 2)
    ]
    gh_instance._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    assert {"id", "number", "title", "user", "state", "created_at", "closed_at", "comments"}.issubset(df.columns)
    assert len(df) == 2
    # Check date normalization
    iso = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    #(open issue): created_at is ISO closed_at is None
    r0 = df.iloc[0]
    assert isinstance(r0["created_at"], str) and iso.match(r0["created_at"])
    assert r0["closed_at"] is None

    #(closed issue): both created_at and closed_at are ISO strings
    r1 = df.iloc[1]
    assert isinstance(r1["created_at"], str) and iso.match(r1["created_at"])
    assert isinstance(r1["closed_at"], str) and iso.match(r1["closed_at"])


def test_fetch_issues_excludes_prs(monkeypatch):
    now = datetime.now()
    issues = [
        DummyIssue(1, 101, "Real issue", "alice", "open", now, None, 0, is_pr=False),
        DummyIssue(2, 102, "This is a PR", "bob", "open", now, None, 2, is_pr=True),
    ]

    gh_instance._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    # PR is excluded
    assert set(df["title"]) == {"Real issue"}
    assert {"id","number","title","user","state","created_at","closed_at","comments","open_duration_days"}.issubset(df.columns)


def test_fetch_issues_duration_calculate(monkeypatch):
    created = datetime(2025, 9, 20, 12, 0, 0)
    closed = datetime(2025, 9, 22, 9, 0, 0)  # ~1 day 21h later
    issues = [DummyIssue(10, 210, "Closed", "michael", "closed", created, closed, 3, is_pr=False)]
    gh_instance._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="closed")

    row = df.iloc[0]
    assert row["open_duration_days"] == 1


