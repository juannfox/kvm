import unittest
import re
import subprocess

from kvm.const import DEFAULT_ENCODING

KVM_VERSION_REGEX = r"\d+\.\d+\.\d+"


class TestApp(unittest.TestCase):
    """Test the Typer application layer"""

    def test_package_version(self):
        """Validate that the package version is up to date"""
        with open("pyproject.toml", "r", encoding=DEFAULT_ENCODING) as f:
            pyproject = f.read().replace("\n", "")
            pyproject_version = re.match(
                fr".+version\s*=\s*\"({KVM_VERSION_REGEX})\".+", pyproject
            )

        with open("kvm/__version__.py", "r", encoding=DEFAULT_ENCODING) as f:
            versionpy = f.read().replace("\n", "")
            versionpy_version = re.match(
                fr".*app_version\s*=\s*\"({KVM_VERSION_REGEX})\".*", versionpy
            )

        self.assertIsInstance(
            pyproject_version, re.Match,
            msg="Invalid or missing version in Pyproject.toml."
        )
        self.assertIsInstance(
            versionpy_version, re.Match,
            msg="Invalid or missing version in __version__.py."
        )
        self.assertEqual(
            pyproject_version.groups()[0],
            versionpy_version.groups()[0],
            msg="Version mismatch between Pyproject.toml and __version__.py."
        )

    # def test_print_version(self):
    #     """Test that the typer app prints the version"""
    #     process = subprocess.Popen(
    #         args=["python3", "-m", "kvm", "version"],
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.PIPE,
    #     )

    #     stdout, _ = process.communicate()
    #     output = stdout.decode(DEFAULT_ENCODING)
    #     self.assertIsInstance(
    #         re.match(fr".+({KVM_VERSION_REGEX}).+", output).groups()[0],
    #         str
    #     )
