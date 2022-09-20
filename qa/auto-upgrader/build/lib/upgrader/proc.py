"""Helpers for running processes."""
import logging
import subprocess
from typing import Tuple

logger = logging.getLogger(__name__)


def run(cmd: str) -> Tuple[str, str]:
    logger.info(f'Running command "{cmd}"')
    comp_proc = subprocess.run(cmd, shell=True, capture_output=True)
    return (comp_proc.stdout.decode("utf-8"), comp_proc.stderr.decode("utf-8"))
