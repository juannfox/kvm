import logging
from rich.logging import RichHandler
from rich import pretty

from kvm.const import LOG_LEVEL

# Logger
logging.basicConfig(
    level=LOG_LEVEL.upper(),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()],
)
log = logging.getLogger("rich")

pretty.install()  # Rich's Pretty print for REPL
