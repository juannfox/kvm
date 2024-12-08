import logging as log
import re
from dataclasses import dataclass
from typing import Annotated, Optional

import requests
import typer

from kvm.const import (DEFAULT_HTTP_TIMEOUT, DEFAULT_KUBECTL_OUT_FILE,
                       DEFAULT_VERSION_FETCH_URL, RELEASE_GET_URL_TEMPLATE,
                       VERSION_REGEX, VERSION_REGEX_MINOR, LOG_LEVEL)
from kvm.utils import detect_platform


def fetch_latest_version(provider_url: str = DEFAULT_VERSION_FETCH_URL) -> str:
    """Identify the latest available Kubeclt version."""
    log.debug(f"Fetching latest version: GET {provider_url}.")
    response = requests.get(provider_url, timeout=DEFAULT_HTTP_TIMEOUT)

    if response.status_code == 200 and response.text is not None:
        version = response.text.strip().lower()
        log.debug(f"Got HTTP response: {version}.")
    else:
        raise ValueError(
            "Failed to fetch latest version. "
            f"Status code: {response.status_code}, "
            "response text: "
            f"{response.text if response.text is not None else ''}."
        )

    return version


@dataclass
class ReleaseSpec:
    os: str
    arch: str
    version: str

    def __init__(
            self, version: str, os: str, arch: str
            ):
        self.validate_version(version)
        self.version = version
        self.os = os
        self.arch = arch

    def __repr__(self) -> str:
        return (
            f"ReleaseSpec(version = {self.version},"
            f"os = {self.os}, arch = {self.arch})"
        )

    def digest_input_version(self, version: str) -> str:
        if not version.startswith("v"):
            version = f"v{version}"

        if re.fullmatch(VERSION_REGEX_MINOR, version):
            # TODO - Detect latest patch of the minor version
            version = f"{version}.0"

        log.debug(f"Received version '{version}'.")
        return version

    def validate_version(self, version: str) -> None:
        version = self.digest_input_version(version)

        if re.fullmatch(VERSION_REGEX, version) is None:
            raise ValueError(f"Invalid version format: {version}.")
        log.debug(
            f"Version '{version}' is valid.")


def generate_release_url(spec: ReleaseSpec) -> str:
    try:
        release_url = RELEASE_GET_URL_TEMPLATE.format(
            version=spec.version,
            os=spec.os,
            arch=spec.arch
        ).strip().lower()

        log.debug(f"Found release URL: {release_url}.")
        return release_url
    except ValueError as e:
        raise ValueError(
            "Failed to generate release URL fro m "
            f"template {RELEASE_GET_URL_TEMPLATE}."
        ) from e


def download_kubectl(
        version: str, out_file: str = DEFAULT_KUBECTL_OUT_FILE):
    """Download a kubectl release to disk."""
    platform = detect_platform()

    version_spec = ReleaseSpec(
        version=version, os=platform[0], arch=platform[1])
    release_get_url = generate_release_url(version_spec)

    log.debug(f"Downloading kubectl release from: {release_get_url}.")
    download_response = requests.get(
            release_get_url, stream=True, timeout=DEFAULT_HTTP_TIMEOUT)
    with open(out_file, "wb") as f:
        for chunk in download_response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
        f.close()

    log.info(f"Downloaded kubectl {version} to {out_file}.")


def download_kubectl_latest():
    """Download latest kubectl release to disk."""
    download_kubectl(fetch_latest_version())

######################################################################


log.basicConfig(level=LOG_LEVEL)

app = typer.Typer()


@app.command()
def latest():
    """
    Identify the latest available Kubeclt version, as per
    the Kuberentes official site.
    """
    latest_version = fetch_latest_version()
    ReleaseSpec.validate_version(latest_version)
    log.info(f"Latest kubectl version: {latest_version}.")


@app.command()
def download(
    version: Annotated[Optional[str],
                       typer.Argument(envvar="KVM_VERSION_TARGET")] = None):
    """
    Download a kubectl release. If no version is specified, the latest will
    be downloaded; the version should be in the format 'vX.Y.Z'.
    """
    if version is None:
        log.debug("Version not provided.")
        download_kubectl_latest()
    else:
        download_kubectl(version)


if __name__ == "__main__":
    app()
