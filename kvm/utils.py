from platform import uname
import requests
from re import match
from hashlib import sha256
from os import path, access, W_OK

from kvm.const import (
    SUPPORTED_ARCHS,
    SUPPORTED_OSES,
    DEFAULT_HTTP_TIMEOUT,
    CHECKSUM_REGEX,
)
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


def http_request(
    url: str,
    method: str = "GET",
    stream: bool = False,
    check_status: bool = True,
    timeout: int = DEFAULT_HTTP_TIMEOUT,
) -> requests.Response:
    """Make an HTTP request."""
    try:
        response = requests.request(
            method=method, url=url, stream=stream, timeout=timeout
        )
        response.raise_for_status()
        if check_status and (
            response.status_code != 200 or response.text is None
        ):
            raise requests.HTTPError(
                "Unexpected HTTP response: Expected Status code 200, "
                f"got {response.status_code}; expected response text, "
                f"got '{response.text}'."
            )
        return response
    except Exception as e:
        raise requests.HTTPError("Failed to make HTTP request.") from e


class Sha256Checksum:
    """Class to represent SHA-256 checksums."""

    def __init__(self, checksum: str):
        checksum = checksum.strip().lower()
        if not self.is_valid(checksum):
            raise ValueError(f"Invalid SHA-256 checksum: {checksum}")
        self.value = checksum

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"Sha256Checksum({self.value})"

    @staticmethod
    def is_valid(checksum: str) -> bool:
        """Validate the format of a SHA-256 checksum."""
        return bool(match(CHECKSUM_REGEX, checksum.strip().lower()))

    @staticmethod
    def calculate_checksum(content: bytes) -> str:
        """
        Calculate a checksum for the given key.
        """
        # Receive a stream object
        checksum = sha256()
        checksum.update(content)
        return Sha256Checksum(checksum.hexdigest())


def check_path_writable(check_path: str) -> bool:
    exists = path.exists(check_path)
    writable = access(check_path, W_OK)
    log.debug(
        f"Access for path '{check_path}': exists={exists}, writable={writable}."
    )
    return exists and writable
