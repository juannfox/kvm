from os import getenv
import logging as log

# Logging options
LOG_LEVEL = "DEBUG" if getenv("DEBUG") == "1" else "INFO"
log.basicConfig(level=LOG_LEVEL)
