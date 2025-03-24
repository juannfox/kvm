from typing import Annotated, Optional
from types import FunctionType
from sys import exit, argv

import requests
import typer
from rich import print
from rich.status import Status

from kvm.const import (
    DEFAULT_KUBECTL_OUT_FILE,
)
from kvm.provider import HttpProvider
from kvm.release import VersionFormatError
from kvm.index import HTTPVersionIndex
from kvm.__version__ import app_version, app_full_name
from kvm.logger import log


def railguard_execution(
        callable: FunctionType,
        action_description: Optional[str] = None,
        **kwargs):
    """Safely execute a callable and break app execution."""
    log.debug(f"Executing '{callable}({kwargs})'.")
    action_description = action_description or f"executing {callable.__name__}"

    try:
        with Status(f":hourglass: {action_description.capitalize()}..."):
            return callable(**kwargs)
    except requests.HTTPError as e:
        log.error(
            f"HTTP error {action_description}: {e}"
        )
    except VersionFormatError as e:
        log.error(
            f"Version error {action_description}: {e}"
        )
    except Exception as e:
        log.error(
            f"Runtime error {action_description}: {e}"
        )
    exit(1)

######################################################################


app = typer.Typer(
    help=(
        f"""
        :anchor: [bold blue]{app_full_name}[/bold blue]:
        Seamless [italic]kubectl[/italic] version switcher
        """
    ),
    rich_markup_mode="rich",
    no_args_is_help=True
)


@app.callback()
def main(ctx: typer.Context):
    """Init for Typer app"""
    log.debug(
        "Starting Typer app's "
        f"subcommand '{ctx.invoked_subcommand}'"
    )
    log.debug(f" User executed: {argv}.")


@app.command()
def latest():
    """
    Identify the latest available Kubeclt version.
    """
    release = railguard_execution(
        callable=HTTPVersionIndex().latest,
        action_description="Identifying latest version"
    )
    print(f"Latest [italic]kubectl[/italic] version: '{release.version}'.")


@app.command()
def list():
    """
    List the available Kubeclt versions.
    """
    releases = railguard_execution(
        callable=HTTPVersionIndex().list,
        action_description="listing available versions"
    )
    releases = [r.version for r in releases]
    releases.sort(reverse=True)
    print(f"Available [italic]kubectl[/italic] versions: {releases}.")


@app.command()
def check(version: str):
    """
    Check if a Kubeclt version exists; the version should be in the format:
     'vX.Y.Z'.
    """
    release = railguard_execution(
        callable=HTTPVersionIndex().get,
        action_description=f"checking version {version}",
        version=version
    )
    if release:
        print(f"[italic]kubectl[/italic] version '{release.version}' exists.")
    else:
        print(f":warning: Version '{version} was not found.'")


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
    if not version:
        release = railguard_execution(
            callable=HTTPVersionIndex().latest,
            action_description="identifying latest version"
        )
        version = release.version

    railguard_execution(
        callable=HttpProvider().fetch,
        action_description=f"downloading version {version}",
        version=version
    )
    log.info(
        f"Downloaded kubectl '{version}' to {DEFAULT_KUBECTL_OUT_FILE}."
    )


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
