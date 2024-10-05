import requests
import logging as log
import re

DEFAULT_VERSION_FETCH_URL = "https://cdn.dl.k8s.io/release/stable.txt"
DEFAULT_OS = "linux"
DEFAULT_ARCH = "amd64"
VERSION_REGEX = r"^v\d+\.\d+\.\d+$"
RELEASE_GET_URL_TEMPLATE = (
    "https://cdn.dl.k8s.io/release/{version}/bin/{os}/{arch}/kubectl"
)


def fetch_latest_version(provider_url: str = DEFAULT_VERSION_FETCH_URL) -> str:
    log.debug(f"Fetching latest version: GET {provider_url}.")
    response = requests.get(url=provider_url)

    if response.status_code == 200 and response.text is not None:
        version = response.text.strip().lower()
        log.debug(f"Got HTTP response: {version}.")
        ReleaseSpec.validate_version(version)
    else:
        raise ValueError(
            "Failed to fetch latest version. "
            f"Status code: {response.status_code}, "
            "response text: "
            f"{response.text if response.text is not None else ''}."
        )

    return version


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
            raise ValueError(
                "Invalid version format;"
                f"expected '{VERSION_REGEX}', got '{version}'."
            )
        log.debug(
            f"Version '{version}' is a valid match to regex '{VERSION_REGEX}'."
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


latest_version = fetch_latest_version()
version_spec = ReleaseSpec(version=latest_version)
release_get_url = generate_release_url(version_spec)


print(release_get_url)
