### The method template for fetech_issues

def fetch_issues(repo_name: str, state: str = "all", max_issues: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_issues` from the specified GitHub repository (issues only).
    Returns a DataFrame with columns: id, number, title, user, state, created_at, closed_at, comments.
    """
    # 1) Read GitHub token
    # TODO

    # 2) Initialize client and get the repo
    # TODO

    # 3) Fetch issues, filtered by state ('all', 'open', 'closed')
    issues = repo.get_issues(state=state)

    # 4) Normalize each issue (skip PRs)
    records = []
    for idx, issue in enumerate(issues):
        if max_issues and idx >= max_issues:
            break
        # Skip pull requests
        # TODO

        # Append records
        # TODO

    # 5) Build DataFrame
    # TODO: return statement


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
    c2.add_argument("--repo",  required=True, help="Repository in owner/repo format")
    c2.add_argument("--state", choices=["all","open","closed"], default="all",
                    help="Filter issues by state")
    c2.add_argument("--max",   type=int, dest="max_issues",
                    help="Max number of issues to fetch")
    c2.add_argument("--out",   required=True, help="Path to output issues CSV")

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

# ---------------- The above is example code you can reference for modifying repo_miner.py ----------------
# ---------------- The following is an example test case you can reference -------------------------------


def test_fetch_issues_basic(monkeypatch):
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
    # TODO
