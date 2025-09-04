from platform import uname
import requests

from kvm.const import SUPPORTED_ARCHS, SUPPORTED_OSES, DEFAULT_HTTP_TIMEOUT
from kvm.logger import log


def detect_platform() -> tuple:
    os = uname().system.lower()
    arch = uname().machine.lower()

    if os not in SUPPORTED_OSES:
        raise ValueError(f"Unsupported OS: {os}.")
    if arch not in SUPPORTED_ARCHS:
        raise ValueError(f"Unsupported architecture: {arch}.")
    if arch == "aarch64":
        arch = "arm64"

    log.debug(f"Working on platform '{os} {arch}'.")

    return (os, arch)


def http_request(
        url: str,
        method: str = "GET",
        stream: bool = False,
        check_status: bool = True,
        timeout: int = DEFAULT_HTTP_TIMEOUT) -> requests.Response:
    """Make an HTTP request."""
    try:
        response = requests.request(
            method=method,
            url=url,
            stream=stream,
            timeout=timeout
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
