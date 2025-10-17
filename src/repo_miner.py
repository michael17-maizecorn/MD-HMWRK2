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


def merge_and_summarize(commits_df: pd.DataFrame, issues_df: pd.DataFrame) -> None:
    """
    Takes two DataFrames (commits and issues) and prints:
      - Top 5 committers by commit count
      - Issue close rate (closed/total)
      - Average open duration for closed issues (in days)
    """
    # Copy to avoid modifying original data
    commits = commits_df.copy()
    issues  = issues_df.copy()

    # 1) Normalize date/time columns to pandas datetime
    commits['date']      = pd.to_datetime(commits['date'], errors='coerce')
    issues['created_at'] = pd.to_datetime(issues['created_at'], errors='coerce')
    issues['closed_at']  = pd.to_datetime(issues['closed_at'], errors='coerce')

    # 2) Top 5 committers
    top = (
        commits
        .dropna(subset=['author'])  # Exclude commits without an author
        .groupby('author', dropna=False)  # Group by author
        .size()  # Count commits per author
        .reset_index(name='count')  # Convert to DataFrame
        .sort_values(['count', 'author'], ascending=[False, True])  # Sort by count desc, author asc
        .head(5)  # Take top 5
    )
    print("Top 5 committers:")
    for _, row in top.iterrows():
        print(f"  {row['author']}: {row['count']} commits")

    # 3) Calculate issue close rate
    total_issues = len(issues)
    closed_issues = (issues["state"].str.lower() == "closed").sum() if "state" in issues else 0
    close_rate = (closed_issues / total_issues) if total_issues else 0.0
    print(f"Issue close rate: {close_rate:.2f}")

    # 4) Compute average open duration (days) for closed issues
    closed = issues["closed_at"].notna() & issues["created_at"].notna()
    durations = (issues.loc[closed, "closed_at"] - issues.loc[closed, "created_at"]).dt.total_seconds() / 86400.0
    if not durations.empty:
        avg_days = durations.mean()
        print(f"Avg. issue open duration: {avg_days:.2f} days")
    else:
        print("Avg. issue open duration: N/A")




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

    # Sub-command: summarize
    c3 = subparsers.add_parser("summarize", help="Summarize commits and issues")
    c3.add_argument("--commits", required=True, help="Path to commits CSV file")
    c3.add_argument("--issues", required=True, help="Path to issues CSV file")

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

    elif args.command == "summarize":
        # Read CSVs into DataFrames
        commits_df = pd.read_csv(args.commits)
        issues_df = pd.read_csv(args.issues)
        # Generate and print the summary
        merge_and_summarize(commits_df, issues_df)

if __name__ == "__main__":
    main()
