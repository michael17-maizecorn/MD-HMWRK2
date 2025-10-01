#!/usr/bin/env python3
"""
repo_miner.py

A command-line tool to:
  1) Fetch and normalize commit data from GitHub

Sub-commands:
  - fetch-commits
"""

import os
import argparse
from typing import Dict, List, Optional

import pandas as pd
from github import Github


def fetch_issues(repo_full_name: str, state: str = "all", max_issues: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_issues` from the specified GitHub repository (issues only).
    Returns a DataFrame with columns: id, number, title, user, state, created_at, closed_at, comments.
    """
    token = os.getenv("GITHUB_TOKEN")
    gh = Github(token)
    repo = gh.get_repo(repo_full_name)

    records: List[Dict[str, object]] = []
    count = 0

    for issue in repo.get_issues(state=state):
        if max_issues is not None and count >= max_issues:
            break

        #Skip pr's
        if hasattr(issue, "pull_request") and issue.pull_request is not None:
            continue

        created = issue.created_at
        closed = issue.closed_at

        open_days = None
        if closed is not None and created is not None:
            #Calculate days open for
            open_days = (closed - created).days

        records.append({
            "id": getattr(issue, "id"),
            "number": getattr(issue, "number"),
            "title": getattr(issue, "title"),
            "user": getattr(issue.user, "login") if getattr(issue, "user", None) else None,
            "state": getattr(issue, "state"),
            "created_at": created.isoformat() if created else None,
            "closed_at": closed.isoformat() if closed else None,
            "comments": getattr(issue, "comments"),
            "open_duration_days": open_days,
        })
        count += 1

    return pd.DataFrame.from_records(
        records,
        columns=["id", "number", "title", "user", "state", "created_at", "closed_at", "comments", "open_duration_days"]
    )


def fetch_commits(repo_name: str, max_commits: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_commits` from the specified GitHub repository.
    Returns a DataFrame with columns: sha, author, email, date, message.
    """
    # 1) Read GitHub token from environment
    # TODO
    token = os.getenv("GITHUB_TOKEN")
    github = Github(token)

    repo = github.get_repo(repo_name)


    records: List[Dict[str, str]] = []
    count = 0
    for c in repo.get_commits():

        commit_author = getattr(c.commit, "author")
        author_name = getattr(commit_author, "name")
        author_email = getattr(commit_author, "email")
        author_date = getattr(commit_author, "date")

        records.append(
            {
                "sha": getattr(c, "sha"),
                "author": author_name,
                "email": author_email,
                "date": author_date.isoformat(),
                "message": getattr(c.commit, "message").splitlines()[0].strip(),
            }
        )
        count += 1
        if max_commits is not None and count >= max_commits:
            break


    return pd.DataFrame.from_records(
        records, columns=["sha", "author", "email", "date", "message"]
    )
    

def main():
    """
    Parse command-line arguments and dispatch to sub-commands.
    """
    parser = argparse.ArgumentParser(
        prog="repo_miner",
        description="Fetch GitHub commits/issues and summarize them"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command: fetch-commits
    c1 = subparsers.add_parser("fetch-commits", help="Fetch commits and save to CSV")
    c1.add_argument("--repo", required=True, help="Repository in owner/repo format")
    c1.add_argument("--max",  type=int, dest="max_commits",
                    help="Max number of commits to fetch")
    c1.add_argument("--out",  required=True, help="Path to output commits CSV")


    # Sub-command: fetch-issues
    c2 = subparsers.add_parser("fetch-issues", help="Fetch issues and save to CSV")
    c2.add_argument("--repo", required=True, help="Repository in owner/repo format")
    c2.add_argument("--state", choices=["all", "open", "closed"], default="all",
                    help="Filter issues by state")
    c2.add_argument("--max", type=int, dest="max_issues",
                    help="Max number of issues to fetch")
    c2.add_argument("--out", required=True, help="Path to output issues CSV")

    args = parser.parse_args()

    # Dispatch based on selected command
    if args.command == "fetch-commits":
        df = fetch_commits(args.repo, args.max_commits)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} commits to {args.out}")

    elif args.command == "fetch-issues":
        df = fetch_issues(args.repo, args.state, args.max_issues)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} issues to {args.out}")

if __name__ == "__main__":
    main()
