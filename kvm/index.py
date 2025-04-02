"""Software version index classes"""
import requests
import re

from dataclasses import dataclass, field

from kvm.const import (
    LATEST_VERSION_ENDPOINT_URL, VERSION_INDEX_URL, VERSION_REGEX_MINOR
)
from kvm.release import ReleaseSpec, VersionFormatError
from kvm.utils import http_request
from kvm.logger import log


@dataclass
class HTTPVersionIndex:
    """A software version index."""
    index_url: str = field(default=VERSION_INDEX_URL)
    latest_url: str = field(default=LATEST_VERSION_ENDPOINT_URL)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(index_url = '{self.index_url}')"

    def _request_latest(self,) -> requests.Response:
        """Request the latest version of a software."""
        response = http_request(self.latest_url)
        return ReleaseSpec(response.text.strip().lower())

    def latest(self) -> ReleaseSpec:
        """Get the latest version of a software."""
        return self._request_latest()

    def _request_versions(self) -> ReleaseSpec:
        """
        Request a given version over HTTP

        Returns: A dictionary of versions, sorted by version number.

        Raises:
            RuntimeError: If the version index returns an unexpected payload.
            VersionFormatError: If the version format is invalid.
        """
        response = http_request(
            self.index_url
        )
        payload = response.json()  # Format [{...tag_name...}, ...]

        versions = {}  # Format {'v1.29.0': {ReleaseSpec()}, ...}
        for release in payload:
            try:
                if isinstance(release, dict):
                    tag_name = release["tag_name"]
                    release = ReleaseSpec(tag_name.strip().lower())
                    versions[release.version] = release
                else:
                    raise RuntimeError(
                        "Version index returned invalid formatted payload."
                    )
            except KeyError as e:
                raise RuntimeError(
                    "Version index returned unexpected payload."
                ) from e
            except VersionFormatError:
                pass

        log.debug(f"Found {len(versions)} versions.")
        return dict(sorted(versions.items(), reverse=True))

    def _request_version(self, version: str) -> ReleaseSpec:
        """Request a given version over HTTP"""
        versions = self._request_versions()

        try:
            version = ReleaseSpec(version).version
            return versions.get(version)
        except KeyError:
            raise RuntimeError(f"Version '{version}' not found.")

    def _request_minor_version(self, version: str) -> ReleaseSpec:
        """Request a given minor version's latest patch over HTTP"""
        versions = self._request_versions()  # Already sorted

        for k, v in versions.items():
            if k.replace("v", "").startswith(version.replace("v", "")):
                return v  # Latest patch version ensured by dict order

        # Otherwise
        raise RuntimeError(f"Version '{version}' not found.")

    def get(self, version: str) -> ReleaseSpec:
        """Identify the latest version of a software."""
        if re.fullmatch(VERSION_REGEX_MINOR, version):
            log.debug(
                f"Identifying latest patch for minor version '{version}'."
            )
            return self._request_minor_version(version)

        return self._request_version(version)

    def list(self) -> list[ReleaseSpec]:
        """Identify the latest version of a software."""
        versions = self._request_versions()
        return [v for v in versions.values()]
