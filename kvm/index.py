"""Software version index classes"""

from abc import ABC, abstractmethod

import requests

from kvm.const import DEFAULT_VERSION_FETCH_URL
from kvm.release import ReleaseSpec
from kvm.utils import http_request


class HTTPVersionIndex(ABC):
    """A software version index."""
    index_url: str

    def __init__(self, index_url: str):
        self.index_url = index_url

    @abstractmethod
    def parse_version(self, response: str) -> ReleaseSpec:
        """Parse a version string."""
        raise NotImplementedError()

    @abstractmethod
    def request_version() -> requests.Response:
        """Request the latest version of a software."""
        raise NotImplementedError()

    def get(self) -> ReleaseSpec:
        """Identify the latest version of a software."""
        response = self.request_version()
        return self.parse_version(response)


class OfficialVersionIndex(HTTPVersionIndex):
    """The official software version index."""

    def __init__(self, index_url: str = DEFAULT_VERSION_FETCH_URL):
        super().__init__(index_url=index_url)

    def parse_version(self, response: str) -> ReleaseSpec:
        """Parse a version string."""
        return ReleaseSpec(response.strip().lower())

    def request_version(self) -> requests.Response:
        """Request the latest version of a software."""
        return http_request(
            self.index_url
        )
