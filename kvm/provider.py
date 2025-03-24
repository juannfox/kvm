"""Logic for release providers."""
import requests
import os

from csv import Error
from dataclasses import dataclass, field

from kvm.const import (
    RELEASE_GET_URL_TEMPLATE,
    DEFAULT_HTTP_CHUNK_SIZE,
    DEFAULT_KUBECTL_OUT_FILE
)
from kvm.release import ReleaseSpec
from kvm.logger import log
from kvm.utils import http_request
from kvm.index import HTTPVersionIndex


class ProviderError(Error):
    """A release provider error."""


@dataclass
class HttpProvider():
    """
    An HTTP-based release provider, which defaults to the official release
    provider by Google/Kubernetes.
    """
    url_template: str = field(default=RELEASE_GET_URL_TEMPLATE)

    def _generate_release_url(self, spec: ReleaseSpec) -> str:
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

    def _write_stream_to_file(
            self, response: requests.Response, out_file: str):
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

    def _add_executable_permissions(self, file: str):
        """Add executable permissions to a file."""
        if os.name == "posix":
            try:
                stat = os.stat(file)
                os.chmod(file, stat.st_mode | 0o111)
            except OSError as e:
                raise ProviderError(
                    f"Failed to add executable permissions to file '{file}':"
                    f" {e}"
                )

    def _request_release(self, spec: ReleaseSpec) -> requests.Response:
        """Request a release over HTTP."""
        try:
            url = self._generate_release_url(spec)
            log.debug(f"Fetching release: {spec} with HTTP GET {url}.")
            return http_request(
                url=url,
                stream=True
            )
        except requests.HTTPError as e:
            raise ProviderError(
                "Failed to fetch release over HTTP. Response Status code: "
                f"{e.response.status_code}."
            ) from e
        except Exception as e:
            raise ProviderError("Failed to fetch release over HTTP.") from e

    def _digest_version(self, version) -> ReleaseSpec:
        """Digest the version string."""
        return HTTPVersionIndex().get(version)

    def fetch(
            self, version: str, out_file: str = DEFAULT_KUBECTL_OUT_FILE):
        """Fetch a software release over HTTP."""
        release = self._digest_version(version)
        response = self._request_release(release)
        self._write_stream_to_file(response, out_file)
        self._add_executable_permissions(out_file)
