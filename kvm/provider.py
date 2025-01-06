"""Logic for release providers."""

import logging as log

from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from kvm.const import RELEASE_GET_URL_TEMPLATE
from kvm.release import ReleaseSpec


class Provider(ABC):
    """A release provider for a given software."""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def __repr__(self) -> str:
        return f"{self.__class__.__name__.capitalize()} provider"

    @abstractmethod
    def get(self, spec: ReleaseSpec) -> str:
        """Get the latest version of a given software."""
        raise NotImplementedError()


class HttpProvider(Provider, ABC):
    """An HTTP-based release provider."""

    @abstractmethod
    def generate_release_url(self, spec: ReleaseSpec) -> str:
        """Generate a release URL from a given specification."""
        raise NotImplementedError()

    def get(self, spec: ReleaseSpec) -> str:
        """Get an HTTP URL to a given software release."""
        return self.generate_release_url(spec)


@dataclass
class OfficialHttpProvider(HttpProvider):
    """The official release provider by Google/Kubernetes."""

    url_template: str = field(default=RELEASE_GET_URL_TEMPLATE)

    def generate_release_url(self, spec: ReleaseSpec) -> str:
        """Generate an HTTP release URL from K8s provider."""
        try:
            release_url = self.url_template.format(
                version=spec.version,
                os=spec.os,
                arch=spec.arch
            ).strip().lower()

            log.debug(f"Found release URL: {release_url}.")
            return release_url
        except ValueError as e:
            raise ValueError(
                "Failed to generate release URL fro m "
                f"template {self.url_template}."
            ) from e
