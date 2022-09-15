import click

from .github import create_pulls


@click.group()
def cli() -> None:
    pass


cli.add_command(create_pulls)

if __name__ == "__main__":
    cli()
