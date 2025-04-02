import unittest

from unittest.mock import patch
from requests import RequestException

from kvm.index import HTTPVersionIndex, VersionFormatError, ReleaseSpec

KVM_VERSION_REGEX = r"\d+\.\d+\.\d+"


class MockResponse:
    """A fake HTTP response"""
    json_response: dict
    status_code: int
    text: str

    def __init__(
            self, text: str,
            json_response: dict = None,
            status_code: int = 200):
        self.json_response = json_response
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        pass

    def json(self):
        return self.json_response


class TestIndex(unittest.TestCase):
    """Test a version index"""
    index: HTTPVersionIndex

    def setUp(self):
        self.index = HTTPVersionIndex()

    def test_latest(self):
        """Test that the app can find the latest kubectl version"""
        # Positive space
        with patch("requests.request") as mock:
            mock.return_value = MockResponse(
                text="v1.29.0",
            )
            self.assertEqual(
                self.index.latest().version,
                "v1.29.0"
            )

        # Negative space
        with patch("requests.request") as mock:
            mock.return_value = MockResponse(
                text="g1BBerish",
            )
            with self.assertRaises(VersionFormatError):
                self.index.latest().version,

        with patch("requests.request") as mock:
            mock.return_value = MockResponse(
                text="1.29.3",
                status_code=401
            )
            with self.assertRaises(RequestException):
                self.index.latest().version

    def test_list(self):
        """Test that the index can list versions"""
        # Positive space
        with patch("requests.request") as mock:
            mock.return_value = MockResponse(
                text="",
                json_response=[
                    {
                        "tag_name": "v1.29.0",
                        "author": "nottrue"
                    },
                    {
                        "tag_name": "v1.28.2",
                        "other_key": "other_value"
                    },
                ]
            )
            self.assertEqual(
                self.index.list(),
                [ReleaseSpec("v1.29.0"), ReleaseSpec("v1.28.2")]
            )

        # Negative space
        with patch("requests.request") as mock:
            mock.return_value = MockResponse(
                text="",
                json_response={
                    "fake": "value",
                    "other": "values"
                },
            )
            with self.assertRaises(RuntimeError):
                self.index.list(),

        with patch("requests.request") as mock:
            mock.return_value = MockResponse(
                text="",
                status_code=401
            )
            with self.assertRaises(RequestException):
                self.index.list()
