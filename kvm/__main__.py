from typing import Annotated, Optional

import requests
import typer
from rich import print

from kvm.const import (
    DEFAULT_KUBECTL_OUT_FILE,
    DEFAULT_VERSION_FETCH_URL
)
from kvm.provider import OfficialHttpProvider
from kvm.release import ReleaseSpec
from kvm.index import OfficialVersionIndex
from kvm.__version__ import app_version, app_full_name
from kvm.logger import log


def fetch_latest_version(provider_url: str = DEFAULT_VERSION_FETCH_URL) -> ReleaseSpec:
    """Identify the latest available Kubeclt version."""
    log.debug(f"Fetching latest version: GET {provider_url}.")
    try:
        index = OfficialVersionIndex()
        return index.get()
    except requests.HTTPError as e:
        raise RuntimeError(
            "Failed to fetch latest version. "
            f"HTTP error: {e.response.status_code}."
        ) from e
    except Exception as e:
        raise RuntimeError("Failed to fetch latest version.") from e


def download_kubectl(version: str, out_file: str = DEFAULT_KUBECTL_OUT_FILE):
    """Download a kubectl release to disk."""
    provider = OfficialHttpProvider(
        spec=ReleaseSpec(
            version=version
        )
    )

    provider.fetch()
    log.info(f"Downloaded kubectl {version} to {out_file}.")


def download_kubectl_latest():
    """Download latest kubectl release to disk."""
    download_kubectl(fetch_latest_version())


######################################################################

app = typer.Typer(
    help=(
        f"""
        :anchor: [bold blue]{app_full_name}[/bold blue]:
        Seamless [italic]kubectl[/italic] version switcher
        """
    ),
    rich_markup_mode="rich"
)


@app.command()
def latest():
    """
    Identify the latest available Kubeclt version, as per
    the Kuberentes official site.
    """
    release = fetch_latest_version()
    print(f"Latest [italic]kubectl[/italic] version: '{release.version}'.")


@app.command()
def download(
    version: Annotated[
        Optional[str], typer.Argument(envvar="KVM_VERSION_TARGET")
    ] = None
):
    """
    Download a kubectl release. If no version is specified, the latest will
    be downloaded; the version should be in the format 'vX.Y.Z'.
    """
    if version is None:
        log.debug("Version not provided.")
        download_kubectl_latest()
    else:
        download_kubectl(version)


@app.command()
def version():
    """
    Display the current application version.
    """
    print(
        f"""
        :anchor: [bold blue]{app_full_name}[/bold blue] {app_version}
        """
    )


if __name__ == "__main__":
    try:
        app()
    except RuntimeError as e:
        print(f":warning: [bold red]Error[/bold red]: {e}")
