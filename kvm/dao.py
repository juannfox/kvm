from os import path, makedirs, listdir
from hashlib import sha256


class DaoError(Exception):
    """A generic DAO error."""


class EntryNotFoundError(DaoError):
    """An entry not found error in the DAO."""


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

    def set(self, content: bytes):
        """Store an item in the database."""
        key = self._calculate_checksum(content)
        self._db[key] = content

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

    def __init__(self, _db_path: str = "/tmp/kvm"):
        """
        Initialize the LocalFilesystemDao with a database.
        :param db: An object to act as the database.
        """
        self._db_path = _db_path
        if not path.exists(_db_path):
            makedirs(_db_path)

        self._db = set()
        self._db = self.list()

    def set(self, value: bytes):
        """
        Store a file in the local filesystem.
        :param value: The file content as bytes.
        """
        checksum = self._calculate_checksum(value)
        file_path = path.join(self._db_path)

        try:
            with open(path.join(self._db_path, checksum), "wb") as f:
                f.write(value)
                self._db.add(checksum)
        except OSError as e:
            raise IOError(f"Failed to write file to {file_path}.") from e

    def get(self, key: str):
        """Retrieve a file from the local filesystem."""
        if key not in self._db:
            raise EntryNotFoundError(f"File with key '{key}' not found.")

        file_path = path.join(self._db_path, key)
        if not path.exists(file_path):
            raise EntryNotFoundError(f"File {file_path} not found.")

        try:
            with open(file_path, "rb") as f:
                return f.read()
        except OSError as e:
            raise IOError(f"Failed to read file from {file_path}.") from e

    def list(self):
        """List all files in the local filesystem."""
        files = listdir(self._db_path)
        return {f.replace(self._db_path, "") for f in files}
