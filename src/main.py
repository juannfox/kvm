import logging as log
import re
from dataclasses import dataclass
import requests
from os import getenv
import typer


DEFAULT_VERSION_FETCH_URL = "https://cdn.dl.k8s.io/release/stable.txt"
DEFAULT_OS = "linux"
DEFAULT_ARCH = "amd64"
DEFAULT_HTTP_TIMEOUT = 60
VERSION_REGEX = r"^v\d+\.\d+\.\d+$"
RELEASE_GET_URL_TEMPLATE = (
    "https://cdn.dl.k8s.io/release/{version}/bin/{os}/{arch}/kubectl"
)


def fetch_latest_version(provider_url: str = DEFAULT_VERSION_FETCH_URL) -> str:
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
            self, version: str, os: str = DEFAULT_OS, arch: str = DEFAULT_ARCH
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

    @staticmethod
    def validate_version(version: str) -> None:
        if re.fullmatch(VERSION_REGEX, version) is None:
            raise ValueError("Invalid version format: {version}.")
        log.debug(
            f"Version '{version}' is valid."
            )


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
        raise e(
            "Failed to generate release URL from "
            f"template {RELEASE_GET_URL_TEMPLATE}."
        )


# Logging options
LOG_LEVEL = "DEBUG" if getenv("DEBUG") == "1" else "INFO"
log.basicConfig(level=LOG_LEVEL)

app = typer.Typer()


@app.command()
def latest():
    latest_version = fetch_latest_version()
    ReleaseSpec.validate_version(latest_version)
    log.info(f"Latest kubectl version: {latest_version}.")


@app.command()
def install(version: str = None):
    if version is None:
        version = fetch_latest_version()
    version_spec = ReleaseSpec(version=version)
    release_get_url = generate_release_url(version_spec)

    log.debug(f"Downloading kubectl release from: {release_get_url}.")
    download_response = requests.get(
            release_get_url, stream=True, timeout=DEFAULT_HTTP_TIMEOUT)
    with open("kubectl", "wb") as f:
        for chunk in download_response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
        f.close()

    log.info(f"Downloaded kubectl {version}.")


if __name__ == "__main__":
    app()
