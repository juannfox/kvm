from os import getenv


DEFAULT_HTTP_TIMEOUT = 60
DEFAULT_HTTP_CHUNK_SIZE = 8192
DEFAULT_KUBECTL_OUT_FILE = "./kubectl"
DEFAULT_ENCODING = "utf-8"
SUPPORTED_OSES = ["darwin", "linux", "windows"]
SUPPORTED_ARCHS = ["x86_64", "arm64"]
VERSION_REGEX = r"^v\d+\.\d+\.\d+$"  # e.g. 'v1.29.3'
VERSION_REGEX_MINOR = r"^v?\d+\.\d+$"  # e.g 'v1.29'
CHECKSUM_REGEX = r'^[a-f0-9]{64}$'  # SHA-256 checksum format
LOG_LEVEL = "DEBUG" if getenv("DEBUG") == "1" else "INFO"

# region URLs
LATEST_VERSION_ENDPOINT_URL = "https://cdn.dl.k8s.io/release/stable.txt"
VERSION_INDEX_URL = (
    "https://api.github.com/repos/kubernetes/kubernetes/releases"
)
RELEASE_GET_URL_TEMPLATE = (
    "https://cdn.dl.k8s.io/release/{version}/bin/{os}/{arch}/kubectl"
)
CHECKSUM_URL_TEMPLATE = (
    "https://cdn.dl.k8s.io/release/{version}/bin/{os}/{arch}/kubectl.sha256"
)
# endregion
