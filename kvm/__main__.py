from typing import Annotated, Optional
from types import FunctionType
from sys import exit, argv
from tempfile import NamedTemporaryFile
from shutil import move
from os import path

import requests
import typer
from rich import print
from rich.status import Status

from kvm.const import (
    DEFAULT_KUBECTL_OUT_FILE,
    DEFAULT_KUBECTL_DOWNLOAD_PATH,
    DEFAULT_KUBECTL_INSTALL_PATH,
)
from kvm.provider import HttpProvider
from kvm.release import VersionFormatError
from kvm.index import HTTPVersionIndex
from kvm.__version__ import app_version, app_full_name
from kvm.logger import log
from kvm.utils import check_path_writable


def railguard_execution(
    callable: FunctionType, action_description: Optional[str] = None, **kwargs
):
    """Safely execute a callable and break app execution."""
    log.debug(f"Executing '{callable}({kwargs})'.")
    action_description = action_description or f"executing {callable.__name__}"

    try:
        with Status(f":hourglass: {action_description.capitalize()}..."):
            return callable(**kwargs)
    except requests.RequestException as e:
        log.error(f"HTTP error {action_description}: {e}")
    except VersionFormatError as e:
        log.error(f"Version error {action_description}: {e}")
    except Exception as e:
        log.error(f"Runtime error {action_description}: {e}")
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
    no_args_is_help=True,
)


@app.callback()
def main(ctx: typer.Context):
    """Init for Typer app"""
    log.debug(f"Starting Typer app's subcommand '{ctx.invoked_subcommand}'")
    log.debug(f" User executed: {argv}.")


@app.command()
def latest():
    """
    Identify the latest available Kubeclt version.
    """
    release = railguard_execution(
        callable=HTTPVersionIndex().latest,
        action_description="Identifying latest version",
    )
    print(f"Latest [italic]kubectl[/italic] version: '{release.version}'.")


@app.command()
def list():
    """
    List the available Kubeclt versions.
    """
    releases = railguard_execution(
        callable=HTTPVersionIndex().list,
        action_description="listing available versions",
    )
    releases = [r.version for r in releases]
    releases.sort(reverse=True)
    print(f"Available [italic]kubectl[/italic] versions: {releases}.")


@app.command()
def check(version: str):
    """
    Check if a Kubeclt version exists; format should be:
     'vX.Y.Z'.
    """
    release = railguard_execution(
        callable=HTTPVersionIndex().get,
        action_description=f"checking version {version}",
        version=version,
    )
    if release:
        print(f"[italic]kubectl[/italic] version '{release.version}' exists.")
    else:
        print(f":warning: Version '{version} was not found.'")


@app.command()
def download(
    version: Annotated[
        Optional[str],
        typer.Argument(envvar="KVM_VERSION_TARGET"),
    ] = None,
    out_file: Annotated[
        Optional[str], typer.Argument(envvar="KVM_OUT_FILE")
    ] = f"{DEFAULT_KUBECTL_DOWNLOAD_PATH}/{DEFAULT_KUBECTL_OUT_FILE}-<version>",
):
    """
    Download a kubectl release. If no version is specified, the latest will
    be downloaded; the version should be in the format 'vX.Y.Z'.
    """
    if not version:
        release = railguard_execution(
            callable=HTTPVersionIndex().latest,
            action_description="identifying latest version",
        )
        version = release.version

    out_file = out_file.replace("<version>", f"v{version}")
    out_file = path.expanduser(out_file)

    railguard_execution(
        callable=HttpProvider().fetch,
        action_description=f"downloading version {version}",
        version=version,
        out_file=out_file,
    )
    print(
        f":white_heavy_check_mark: Downloaded [italic]kubectl[/italic] "
        f"'{version}' as '{out_file}'."
    )


@app.command()
def install(
    version: Annotated[
        Optional[str],
        typer.Argument(envvar="KVM_VERSION_TARGET"),
    ] = None,
    install_path: Annotated[
        Optional[str], typer.Argument(envvar="KVM_INSTALL_PATH")
    ] = DEFAULT_KUBECTL_INSTALL_PATH,
):
    """
    Install a kubectl release in PATH. If no version is specified, the latest
    will be installed; the version should be in the format 'vX.Y.Z'.
    """
    if not version:
        release = railguard_execution(
            callable=HTTPVersionIndex().latest,
            action_description="identifying latest version",
        )
        version = release.version

    temp_file = NamedTemporaryFile()

    # Download
    railguard_execution(
        callable=HttpProvider().fetch,
        action_description=f"downloading version {version}",
        version=version,
        out_file=temp_file.name,
    )

    target_file = path.expanduser(install_path)
    target_path = path.dirname(target_file)
    if not check_path_writable(target_path):
        log.error(
            f"Failed to install version {version} to {target_file}: "
            f"Permission denied. "
            f"Did you run {app_full_name} with enough privileges?"
        )
        exit(1)

    # Install (Move)
    railguard_execution(
        callable=move,
        action_description=f"installing version {version} to {target_file}",
        src=temp_file.name,
        dst=target_file,
    )

    temp_file.close()

    print(
        f":white_heavy_check_mark: Installed [italic]kubectl[/italic] "
        f"'{version}' as '{target_file}'."
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
        print(f":anchor: [bold blue]{app_full_name}[/bold blue]")
        app()
    except RuntimeError as e:
        print(f":warning: [bold red]Error[/bold red]: {e}")
