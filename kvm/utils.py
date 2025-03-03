from platform import uname

from kvm.const import SUPPORTED_ARCHS, SUPPORTED_OSES
from kvm.logger import log


def detect_platform() -> tuple:
    os = uname().system.lower()
    arch = uname().machine.lower()

    if os not in SUPPORTED_OSES:
        raise ValueError(f"Unsupported OS: {os}.")
    if arch not in SUPPORTED_ARCHS:
        raise ValueError(f"Unsupported architecture: {arch}.")

    log.debug(f"Working on platform '{os} {arch}'.")

    return (os, arch)
