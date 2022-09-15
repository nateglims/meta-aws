import os
from pathlib import Path
from typing import Iterable, Optional

import click
from github import Github


@click.command()
@click.option("--branch-file", type=click.Path(exists=True))
@click.option("--target-branch", type=str)
@click.option("--repo", type=str)
@click.argument("branches", nargs=-1)
def create_pulls(
    target_branch: str, repo: str, branch_file: Optional[Path], branches: Iterable[str]
) -> None:
    if branch_file is not None:
        with open(branch_file) as f:
            branches = [s.strip() for s in f.readlines()]
    _create_prs(target_branch, repo, branches)


def _create_prs(target_branch: str, repo: str, branches: Iterable[str]) -> None:
    """Create pull requests on pushed branches."""
    assert "GITHUB_TOKEN" in os.environ, "GITHUB_TOKEN not found in env"
    token = os.environ.get("GITHUB_TOKEN")
    gh = Github(token)
    gh_repo = gh.get_repo(repo)
    for branch in branches:
        gh_repo.create_pull(
            base=target_branch, head=branch, title=branch, body="Automatically created."
        )
