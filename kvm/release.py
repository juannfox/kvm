import re
from dataclasses import dataclass, field

from kvm.const import VERSION_REGEX, VERSION_REGEX_MINOR
from kvm.utils import detect_platform
from kvm.logger import log


class VersionFormatError(Exception):
    """A version format error."""


@dataclass
class ReleaseSpec:
    """A release specification for a software."""

    version: str = field(default_factory=str)
    os: str = field(default_factory=str)
    arch: str = field(default_factory=str)

    def __post_init__(self):
        self._validate_version()

        if not self.os or not self.arch:
            self.os, self.arch = detect_platform()

    def __repr__(self) -> str:
        return (
            f"ReleaseSpec(version = '{self.version}',"
            f"os = '{self.os}', arch = '{self.arch}')"
        )

    def _digest_prefix(self) -> str:
        """Ensure a version string has the right prefix"""
        if not self.version.startswith("v"):
            self.version = f"v{self.version}"

    def _digest_patch(self) -> str:
        """Validate and ammend the patch on a semver version string"""
        if re.fullmatch(VERSION_REGEX_MINOR, self.version):
            # TODO - Fetch (online) latest patch of the minor version
            return f"{self.version}.0"

    def _validate_version(self) -> None:
        self._digest_prefix()
        self._digest_patch()

        if re.fullmatch(VERSION_REGEX, self.version) is None:
            raise VersionFormatError(
                f"Invalid version format: '{self.version}', "
                f"expected '${VERSION_REGEX}'."
            )
        log.debug(f"Version '{self.version}' is valid.")
