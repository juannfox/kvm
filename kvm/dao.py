import json
from kvm.logger import log
from os import path, makedirs
from hashlib import sha256


class DaoError(Exception):
    """A generic DAO error."""


class EntryNotFoundError(DaoError):
    """An entry not found error in the DAO."""


class DuplicateEntryError(DaoError):
    """An error indicating a duplicate entry in the DAO."""


class BinaryDao:
    """
    Data Access Object to interact with
    a database for binary files.
    """

    def _calculate_checksum(self, content: bytes) -> str:
        """
        Calculate a checksum for the given key.
        """
        # Receive a stream object
        checksum = sha256()
        checksum.update(content)
        return checksum.hexdigest()

    def get(self, key: str):
        """Retrieve an item from the database."""
        return self._db.get(key)

    def set(self, key: str, content: bytes):
        """Store an item in the database."""
        self._db[key] = self._calculate_checksum(content)

    def list(self):
        """List all items in the database."""
        return list(self._db.keys())

    def clear(self):
        """Clear the database."""
        self._db.clear()


class LocalFilesystemDao(BinaryDao):
    """
    Local filesystem DAO to interact with
    a local file system for binary files.
    """

    def __init__(
            self,
            db_path: str = "/tmp/kvm/versions.json",
            file_path: str = "/tmp/kvm"):
        """
        Initialize the LocalFilesystemDao with a database.
        :param db: An object to act as the database.
        """
        self._db_path = db_path
        self._file_path = file_path
        self._db = dict()

        if path.exists(self._db_path):
            self._db = self._load_db()

        if not path.exists(self._file_path):
            log.debug(f"Initialized database directory at {self._file_path}.")
            makedirs(self._file_path)

    def _load_db(self):
        """
        Load the database from the local filesystem.
        """
        local_db = dict()
        try:
            with open(self._db_path, "r", encoding="utf-8") as f:
                log.debug(f"Loading database from {self._db_path}.")
                local_db = json.load(f)
        except Exception as e:
            log.error(
                f"Failed to load database from {self._db_path}: {e}"
            )
        return local_db

    def _dump_db(self):
        """
        Dump the database to the local filesystem.
        """

        try:
            with open(self._db_path, "w", encoding="utf-8") as f:
                log.debug(f"Dumping database to {self._db_path}.")
                json.dump(self._db, f)
        except Exception as e:
            log.error(
                f"Failed to dump database to {self._db_path}: {e}"
            )

    def set(self, key: str, value: bytes):
        """
        Store a file in the local filesystem.
        :param value: The file content as bytes.
        """
        if key in self._db.keys():
            raise DuplicateEntryError(f"Item with key '{key}' already exists.")

        checksum = self._calculate_checksum(value)
        file_path = path.join(self._file_path, checksum)

        if not path.exists(file_path):
            try:
                with open(file_path, "wb") as f:
                    log.debug(
                        f"Storing file '{key}={checksum}' at {file_path}."
                    )
                    f.write(value)
                    self._db[key] = checksum
                    self._dump_db()
            except OSError as e:
                raise IOError(f"Failed to write file to {file_path}.") from e
        else:
            raise DuplicateEntryError(
                f"File '{key}={checksum}' already exists."
            )

    def get(self, key: str):
        """Retrieve a file from the local filesystem."""
        if key not in self._db.keys():
            raise EntryNotFoundError(f"Item with key '{key}' not found.")

        file_path = path.join(self._file_path, key)
        if not path.exists(file_path):
            raise EntryNotFoundError(f"File '{key}={file_path}' not found.")

        try:
            with open(file_path, "rb") as f:
                log.debug(f"Retrieving file '{key}' from {file_path}.")
                return f.read()
        except OSError as e:
            raise IOError(f"Failed to read file from {file_path}.") from e

    def list(self):
        """List all files in the local filesystem."""
        return [f"{key}={checksum}" for key, checksum in self._db.items()]
