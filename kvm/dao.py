import json
from os import path, makedirs, listdir, remove, getenv

from kvm.logger import log
from kvm.const import (
    DEFAULT_ENCODING,
    FILESTORE_CHECKSUMS_DIR,
    FILESTORE_LOCATION_TEMPLATE,
    FILESTORE_REGISTRY_FILE,
    FILESTORE_LOCATION_FALLBACK,
    TEMP_DIR_ENV_VAR_UNIX,
    TEMP_DIR_ENV_VAR_WINDOWS,
)
from kvm.utils import Sha256Checksum, detect_platform


class DaoError(Exception):
    """A generic DAO error."""


class EntryNotFoundError(DaoError):
    """An entry not found error in the DAO."""


class DuplicateEntryError(DaoError):
    """An error indicating a duplicate entry in the DAO."""


class ChecksumFilestoreDao:
    """
    Data Access Object to interact with
    a Filestore of checksum-based blobs.
    """

    def __init__(self, location: str):
        """
        Initialize the ChecksumDao with a Filestore.
        :param db_path: The path to the database file.
        """
        self.location = location
        if not path.exists(self.location):
            log.debug(f"Initialized Filestore directory at {self.location}.")
            makedirs(self.location)

    def list(self) -> str:
        """List all available files in the filestore."""
        files = listdir(self.location)
        filtered_files = [
            f"{self.location}/{file}"
            for file in files
            if Sha256Checksum.is_valid(file)
        ]
        log.debug(f"Found {len(filtered_files)} files in the filestore.")
        return filtered_files

    def get(self, checksum: Sha256Checksum) -> str:
        """Retrieve a checksum from the database."""
        item = None
        files = listdir(self.location)
        for file in files:
            if file == str(checksum):
                log.debug(f"Found '{self.location}/{file}'.")
                item = f"{self.location}/{file}"
                break

        return item

    def set(self, content: bytes) -> Sha256Checksum:
        """Store a checksum in the database."""
        checksum = Sha256Checksum.calculate_checksum(content)
        file_path = path.join(self.location, str(checksum))

        if not path.exists(file_path):
            try:
                with open(file_path, "wb") as f:
                    log.debug(
                        f"Storing file '{str(checksum)}' at '{self.location}'."
                    )
                    f.write(content)
            except OSError as e:
                raise IOError(
                    f"Failed to write '{str(checksum)}' to {file_path}."
                ) from e
        else:
            log.warning(f"File '{str(checksum)}' already exists, skipping.")

        return checksum

    def clear(self):
        """Clear the checksum database."""
        files = self.list()
        log.debug(f"Clearing {len(files)} files from the checksum database.")
        for file in files:
            try:
                remove(file)
            except OSError as e:
                raise DaoError("Failed to clear the checksum database.") from e


class LocalFilestoreDao:
    """
    Local indexed (key-value) DAO to interact with
    a Filestore of checksum-based blobs.
    """

    def __init__(
        self,
        filestore_location_template: str = FILESTORE_LOCATION_TEMPLATE,
        registry_file: str = FILESTORE_REGISTRY_FILE,
        filestore_dir: str = FILESTORE_CHECKSUMS_DIR,
    ):
        """
        Initialize the LocalFilesystemDao with a database.
        :param db: An object to act as the database.
        """
        if detect_platform() == "windows":
            temp_dir_env_var = TEMP_DIR_ENV_VAR_WINDOWS
        else:
            temp_dir_env_var = TEMP_DIR_ENV_VAR_UNIX

        self.filestore_location = filestore_location_template.format(
            temp_dir=getenv(temp_dir_env_var, FILESTORE_LOCATION_FALLBACK)
        )

        self.registry_file = f"{self.filestore_location}/{registry_file}"
        self.filestore = ChecksumFilestoreDao(
            location=f"{self.filestore_location}/{filestore_dir}"
        )

        try:
            if path.exists(self.registry_file):
                self._load()
            else:
                log.debug("Bootstrapping filestore db.")
                self._dump({})

            log.debug(
                f"Working with local filestore db at: {self.registry_file}."
            )

        except OSError as e:
            raise DaoError(
                f"Failed to create database at {self.registry_file}."
            ) from e
        except Exception as e:
            raise DaoError(
                f"Failed to initialize database at {self.registry_file}."
            ) from e

    def _load(self) -> dict:
        "Load the database from the local filesystem."
        try:
            registry = open(self.registry_file, "r", encoding=DEFAULT_ENCODING)
            return json.load(registry)
        except Exception as e:
            log.error(
                f"Failed to load the database from {self.registry_file}, "
                f"falling back to empty database: {e}"
            )
            return {}

    def _dump(self, data: dict):
        """Dump the database to the local filesystem."""
        try:
            registry = open(self.registry_file, "w", encoding=DEFAULT_ENCODING)
            json.dump(data, registry)
        except Exception:
            log.error(
                f"Failed to dump data to the database at {self.registry_file}."
            )

    def set(self, key: str, value: bytes):
        """
        Store a file in the local filesystem.
        :param value: The file content as bytes.
        """
        current_data = self._load()
        if key not in current_data.keys():
            checksum = self.filestore.set(value)
            current_data[key] = str(checksum)
            self._dump(current_data)
            log.debug(f"Stored file '{key}' in the local filesystem.")
        else:
            log.warning(f"Item with key '{key}' already exists, skipping.")

    def get(self, key: str) -> dict:
        """Retrieve a file from the local filesystem."""
        current_data = self._load()
        item = None
        if key in current_data.keys():
            item = {
                "key": key,
                "checksum": Sha256Checksum(current_data[key]),
                "file": self.filestore.get(current_data[key]),
            }
        return item

    def list(self):
        """List all files in the local filesystem."""
        current_data = self._load()
        items = [f"{key}={checksum}" for key, checksum in current_data.items()]
        log.debug(f"Found {len(items)} items in the local registry.")
        return items

    def clear(self):
        """Clear the local filesystem database."""
        self.filestore.clear()
        self._dump({})
        log.debug("Cleared the local filesystem database.")
