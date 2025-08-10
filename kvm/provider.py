"""Logic for release providers."""

import requests
import os

from shutil import copyfile
from csv import Error
from dataclasses import dataclass, field

from kvm.const import (
    RELEASE_GET_URL_TEMPLATE,
    DEFAULT_HTTP_CHUNK_SIZE,
    DEFAULT_KUBECTL_OUT_FILE,
    CHECKSUM_URL_TEMPLATE
)
from kvm.release import ReleaseSpec
from kvm.logger import log
from kvm.utils import http_request, Sha256Checksum
from kvm.index import HTTPVersionIndex
from kvm.dao import LocalFilestoreDao


class ProviderError(Error):
    """A release provider error."""


@dataclass
class HttpProvider:
    """
    An HTTP-based release provider, which defaults to the official release
    provider by Google/Kubernetes.
    """

    url_template: str = field(default=RELEASE_GET_URL_TEMPLATE)
    checksum_template: str = field(default=CHECKSUM_URL_TEMPLATE)

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

    def _generate_checksum_url(self, spec: ReleaseSpec) -> str:
        """Generate an HTTP checksum URL from K8s provider."""
        try:
            checksum_url = (
                self.checksum_template.format(
                    version=spec.version, os=spec.os, arch=spec.arch
                )
                .strip()
                .lower()
            )

            log.debug(f"Found checksum URL: {checksum_url}.")
            return checksum_url
        except ValueError as e:
            raise ValueError(
                "Failed to generate checksum URL from "
                f"template {self.checksum_template}."
            ) from e

    def _write_stream_to_file(
            self, response: requests.Response,
            out_file: str):
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
            return http_request(url=url, stream=True)
        except requests.HTTPError as e:
            raise ProviderError(
                "Failed to fetch release over HTTP. Response Status code: "
                f"{e.response.status_code}."
            ) from e
        except Exception as e:
            raise ProviderError("Failed to fetch release over HTTP.") from e

    def _request_checksum(self, spec: ReleaseSpec) -> requests.Response:
        """Request a release checksum over HTTP."""
        try:
            url = self._generate_checksum_url(spec)
            log.debug(f"Fetching checksum: {spec} with HTTP GET {url}.")
            response = http_request(url=url, stream=True)

            if response.text is None:
                raise ProviderError(
                    "Checksum response text is empty. "
                    "Expected a valid checksum."
                )

            return response.text.strip().lower()
        except requests.HTTPError as e:
            raise ProviderError(
                "Failed to fetch checksum over HTTP. Response Status code: "
                f"{e.response.status_code}."
            ) from e
        except Exception as e:
            raise ProviderError("Failed to fetch checksum over HTTP.") from e

    def _digest_version(self, version) -> ReleaseSpec:
        """Digest the version string."""
        return HTTPVersionIndex().get(version)

    def fetch(self, version: str, out_file: str = DEFAULT_KUBECTL_OUT_FILE):
        """Fetch a software release over HTTP."""
        release = self._digest_version(version)
        checksum = self._request_checksum(release)

        cache = LocalFilestoreDao()
        cached_file = cache.get(version)

        if cached_file and str(cached_file['checksum']) == checksum:
            log.debug(
                f"Found cached file for {version}: "
                f"{cached_file['file']} "
                f"({cached_file['checksum']})."
            )
            copyfile(cached_file['file'], out_file)
        else:
            log.debug(f"Release {version} not found in cache, downloading.")
            response = self._request_release(release)
            downloaded_checksum = Sha256Checksum.calculate_checksum(
                response.content
            )
            if str(downloaded_checksum) == checksum:
                log.debug(
                    f"Checksum for download of {version} is valid: {checksum}."
                )
                cache.set(version, response.content)
                self._write_stream_to_file(response, out_file)
            else:
                raise ProviderError(
                    f"Checksum mismatch for downloaded release '{version}'. "
                    f"Expected '{checksum}', "
                    f"got: '{downloaded_checksum}."
                )

        self._add_executable_permissions(out_file)

        # TODO remove
        cache.list()
