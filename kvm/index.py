"""Software version index classes"""
import requests
from  dataclasses import dataclass, field

from kvm.const import LATEST_VERSION_ENDPOINT_URL, VERSION_INDEX_URL
from kvm.release import ReleaseSpec
from kvm.utils import http_request
from kvm.logger import log


@dataclass
class HTTPVersionIndex:
    """A software version index."""
    index_url: str = field(default=VERSION_INDEX_URL)
    latest_url: str = field(default=LATEST_VERSION_ENDPOINT_URL)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(index_url = '{self.index_url}')"

    def _digest_version(self, response: requests.Response) -> ReleaseSpec:
        """Process a version string and return a Release spec."""
        return ReleaseSpec(response.text.strip().lower())

    def _request_latest(self,) -> requests.Response:
        """Request the latest version of a software."""
        response = http_request(self.latest_url)
        return ReleaseSpec(response.text.strip().lower())

    def latest(self) -> ReleaseSpec:
        """Get the latest version of a software."""
        return self._request_latest()

    def _request_versions(self) -> ReleaseSpec:
        """Request a given version over HTTP"""
        response = http_request(
            self.index_url
        )
        payload = response.json() # Format [{...tag_name...}, ...]

        versions = {} # Format {'v1.29.0': {ReleaseSpec()}, ...}
        for release in payload:
            try:
                tag_name = release["tag_name"]
                release = ReleaseSpec(tag_name.strip().lower())
                versions[release.version] = release
            except KeyError as e:
                raise RuntimeError(
                    "Version index retuurned unexpected payload."
                ) from e
            except ValueError:
                log.debug(f"Skipping invalid version {tag_name}.")

        return versions

    def _request_version(self, version: str) -> ReleaseSpec:
        """Request a given version over HTTP"""
        versions = self._request_versions()
        try:
            version = ReleaseSpec(version).version
            return versions.get(version)
        except KeyError:
            raise RuntimeError(f"Version '{version}' not found.")

    def get(self, version: str) -> ReleaseSpec:
        """Identify the latest version of a software."""
        return self._request_version(version)

    def list(self) -> list[ReleaseSpec]:
        """Identify the latest version of a software."""
        versions = self._request_versions()
        return [v for v in versions.values()]
