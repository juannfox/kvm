import logging
from rich.logging import RichHandler
from rich import pretty
from os import getenv

from kvm.const import LOG_LEVEL

# Logger
logging.basicConfig(
    level=getenv("LOG_LEVEL", LOG_LEVEL),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)
log = logging.getLogger("rich")

pretty.install()  # Rich's Pretty print for REPL