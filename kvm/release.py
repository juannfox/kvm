import logging as log
import re
from dataclasses import dataclass, field

from kvm.const import VERSION_REGEX, VERSION_REGEX_MINOR


@dataclass
class ReleaseSpec:
    """A release specification for a software."""

    version: str = field(default_factory=str)
    os: str = field(default_factory=str)
    arch: str = field(default_factory=str)

    def __post_init__(self):
        self.validate_version()

    def __repr__(self) -> str:
        return (
            f"ReleaseSpec(version = {self.version},"
            f"os = {self.os}, arch = {self.arch})"
        )

    @staticmethod
    def digest_input_version(version: str) -> str:
        if not version.startswith("v"):
            version = f"v{version}"

        if re.fullmatch(VERSION_REGEX_MINOR, version):
            # TODO - Detect latest patch of the minor version
            version = f"{version}.0"

        log.debug(f"Received version '{version}'.")
        return version

    def validate_version(self) -> None:
        self.digest_input_version(self.version)

        if re.fullmatch(VERSION_REGEX, self.version) is None:
            raise ValueError(
                f"Invalid version format: '{self.version}', "
                f"expected '${VERSION_REGEX}'."
            )
        log.debug(f"Version '{self.version}' is valid.")
