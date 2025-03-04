"""Logic for release providers."""
from csv import Error
import requests

from abc import ABC, abstractmethod

from kvm.const import (
    RELEASE_GET_URL_TEMPLATE,
    DEFAULT_HTTP_TIMEOUT,
    DEFAULT_HTTP_CHUNK_SIZE,
    DEFAULT_KUBECTL_OUT_FILE
)
from kvm.release import ReleaseSpec
from kvm.logger import log


class ProviderError(Error):
    """A release provider error."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class Provider(ABC):
    """A release provider for a given software."""

    spec: ReleaseSpec

    def __init__(self, spec: ReleaseSpec):
        self.spec = spec

    def __repr__(self) -> str:
        return f"{self.__class__.__name__.capitalize()} provider"

    @abstractmethod
    def fetch(self, out_file: str = DEFAULT_KUBECTL_OUT_FILE):
        """Get the latest version of a given software."""
        raise NotImplementedError()


class HttpProvider(Provider, ABC):
    """An HTTP-based release provider."""
    url: str

    def __init__(self, spec: ReleaseSpec):
        self.url = self.generate_release_url(spec)
        super().__init__(spec)

    @abstractmethod
    def generate_release_url(self, spec: ReleaseSpec) -> str:
        """Generate a release URL from a given specification."""
        raise NotImplementedError()

    def write_stream_to_file(self, response: requests.Response, out_file: str):
        """Write an HTTP response stream to a file."""
        try:
            log.debug(f"Writing HTTP response stream to file: '{out_file}'.")
            with open(out_file, "wb") as f:
                for chunk in response.iter_content(
                    chunk_size=DEFAULT_HTTP_CHUNK_SIZE
                ):
                    if chunk:
                        f.write(chunk)
                f.close()
        except OSError as e:
            raise ProviderError(
                "Failed to write HTTP response stream to file"
            ) from e

    def request_release(self, spec: ReleaseSpec) -> requests.Response:
        """Request a release over HTTP."""
        try:
            log.debug(f"Fetching release: {spec} with HTTP GET {self.url}.")
            response = requests.get(
                url=self.url,
                stream=True,
                timeout=DEFAULT_HTTP_TIMEOUT
            )
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            raise ProviderError(
                "Failed to fetch release over HTTP. Response Status code: "
                f"{e.response.status_code}."
            ) from e
        except Exception as e:
            raise ProviderError("Failed to fetch release over HTTP.") from e

    def fetch(self, out_file: str = DEFAULT_KUBECTL_OUT_FILE):
        """Fetch a software release over HTTP."""
        response = self.request_release(self.spec)
        self.write_stream_to_file(response, out_file)


class OfficialHttpProvider(HttpProvider):
    """The official release provider by Google/Kubernetes."""

    url_template: str

    def __init__(
        self,
        spec: ReleaseSpec,
        url_template: str = RELEASE_GET_URL_TEMPLATE
    ):
        self.url_template = url_template
        super().__init__(spec)

    def generate_release_url(self, spec: ReleaseSpec) -> str:
        """Generate an HTTP release URL from K8s provider."""
        try:
            release_url = (
                self.url_template.format(
                    version=spec.version, os=spec.os, arch=spec.arch
                )
                .strip()
                .lower()
            )

            log.debug(f"Found release URL: {release_url}.")
            return release_url
        except ValueError as e:
            raise ValueError(
                "Failed to generate release URL from "
                f"template {self.url_template}."
            ) from e
