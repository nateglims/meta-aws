import logging

import click

from .github import create_pulls
from .updates import check_for_updates, find_recipes, update

logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    logging.basicConfig(level=logging.DEBUG)
    pass


cli.add_command(create_pulls)
cli.add_command(find_recipes)
cli.add_command(check_for_updates)
cli.add_command(update)

if __name__ == "__main__":
    cli()
