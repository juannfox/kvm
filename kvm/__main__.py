from typing import Annotated, Optional

import requests
import typer
from rich import print

from kvm.const import (
    DEFAULT_HTTP_TIMEOUT,
    DEFAULT_KUBECTL_OUT_FILE,
    DEFAULT_VERSION_FETCH_URL
)
from kvm.provider import OfficialHttpProvider
from kvm.release import ReleaseSpec
from kvm.__version__ import app_version, app_full_name
from kvm.logger import log


def fetch_latest_version(provider_url: str = DEFAULT_VERSION_FETCH_URL) -> str:
    """Identify the latest available Kubeclt version."""
    log.debug(f"Fetching latest version: GET {provider_url}.")
    try:
        response = requests.get(provider_url, timeout=DEFAULT_HTTP_TIMEOUT)
        response.raise_for_status()

        if response.status_code == 200 and response.text is not None:
            version = response.text.strip().lower()
            log.debug(f"Got HTTP response: {version}.")
            return version
        else:
            raise RuntimeError(
                "Failed to fetch latest version. "
                f"Status code: {response.status_code}, "
                "response text: "
                f"{response.text if response.text is not None else ''}."
            )
    except requests.HTTPError as e:
        raise RuntimeError(
            "Failed to fetch latest version. "
            f"HTTP error: {e.response.status_code}."
        ) from e
    except requests.ConnectionError as e:
        raise RuntimeError(
            "Failed to fetch latest version. Connection error."
        ) from e
    except Exception as e:
        raise RuntimeError("Failed to fetch latest version.") from e


def download_kubectl(version: str, out_file: str = DEFAULT_KUBECTL_OUT_FILE):
    """Download a kubectl release to disk."""
    version_spec = ReleaseSpec(
        version=version
    )

    release_get_url = OfficialHttpProvider().generate_release_url(version_spec)

    log.debug(f"Downloading kubectl release from: {release_get_url}.")
    download_response = requests.get(
        release_get_url, stream=True, timeout=DEFAULT_HTTP_TIMEOUT
    )
    with open(out_file, "wb") as f:
        for chunk in download_response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
        f.close()

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
    latest_version = fetch_latest_version()
    release = ReleaseSpec(version=latest_version)
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
