from os import getenv

DEFAULT_VERSION_FETCH_URL = "https://ccdn.dl.k8s.io/release/stable.txt"
DEFAULT_HTTP_TIMEOUT = 60
DEFAULT_KUBECTL_OUT_FILE = "kubectl"
SUPPORTED_OSES = ["darwin", "linux", "windows"]
SUPPORTED_ARCHS = ["amd64", "arm64"]
VERSION_REGEX = r"^v\d+\.\d+\.\d+$"
VERSION_REGEX_MINOR = r"^v\d+\.\d+$"
RELEASE_GET_URL_TEMPLATE = (
    "https://cdn.dl.k8s.io/release/{version}/bin/{os}/{arch}/kubectl"
)
LOG_LEVEL = "DEBUG" if getenv("DEBUG") == "1" else "INFO"
