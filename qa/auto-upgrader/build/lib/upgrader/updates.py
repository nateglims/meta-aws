import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click

from upgrader.proc import run

logger = logging.getLogger(__name__)

RECIPE_NAME_RE = r"^(?P<name>[^_]+)_(?P<version>.+).bb$"

EXCLUDE = [
    "jailer",
    "greengrass",
    "corretto",
    "neo-ai",
    "firecracker",
]  # TODO: Allow this to be passed as an argument.
# e.g. w/ click https://click.palletsprojects.com/en/8.1.x/options/#multiple-options


@click.command()
@click.option("--root", type=click.Path(exists=True))
def find_recipes(root: Path) -> List[str]:
    return _find_recipes(root)


def _find_recipes(root: Path) -> List[str]:
    recipes = []
    for top, _, files in os.walk(root):
        for fname in files:
            m = re.search(RECIPE_NAME_RE, fname)
            if m:
                if all([m.group("name").find(x) for x in EXCLUDE]):
                    logger.debug(f"selecting recipe {top}/{fname}")
                    recipes.append(m.group("name"))
                else:
                    logger.debug(f"excluding recipe {top}/{fname}")
            if not m and fname.endswith(".bb"):
                logger.warn(f"possible recipe did not match: {fname}")
    return recipes


@click.command()
@click.option("--recipe", type=str)
def check_for_updates(recipe: str) -> bool:
    return _check_for_updates(recipe) is not None


def _check_for_updates(recipe: str) -> Optional[dict]:
    (_, stderr) = run(f"devtool check-upgrade-status {recipe}")
    update_re = r"INFO:\s+" + recipe + r"\s+([^\s]+)\s+([^\s]+)"
    m = re.search(update_re, stderr)
    if m:
        logger.info(f"Update for {recipe}:\t{m.group(1)}\t->\t{m.group(2)}")
        return {"recipe": recipe, "previous_version": m.group(1), "next_version": m.group(2)}
    else:
        logger.info(f"No update found for {recipe}.")
        logger.debug(f"devtool output: {stderr}")
        return None


@click.command()
@click.option("--layer-path", type=click.Path(exists=True))
@click.option("--target-branch", type=str, default="master")
def update(layer_path: Path, target_branch: str) -> None:
    logger.info("checking for recipe updates...")
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    for recipe in _find_recipes(layer_path):
        run(f"git -C {layer_path} checkout {target_branch}")
        upgrade = _check_for_updates(recipe)
        if upgrade:
            if upgrade.get("next_version") == "^{}":
                logger.error(f"error getting ref for {upgrade.get('recipe')}")
                continue

            run(f"devtool upgrade {upgrade.get('recipe')}")

            new_branch = f"{date}T" f"_{target_branch}_{upgrade.get('recipe')}"
            commit_msg = (
                f"{upgrade.get('recipe')}: upgrade {upgrade.get('previous_version')} "
                f"-> {upgrade.get('next_version')}"
            )
            run(f"git -C {layer_path} checkout -b {new_branch} {target_branch}")
            run(f"devtool finish --force --force-path-refresh {upgrade.get('recipe')} {layer_path}")
            run(f"git -C {layer_path} add --all")
            run(f'git -C {layer_path} commit -a -m "{commit_msg}"')
            with open("upgraded_recipes.log", "a") as f:
                f.write(new_branch + "\n")
