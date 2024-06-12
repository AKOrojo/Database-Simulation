import os


class Database:
    """
    A simple database simulation class.

    This class simulates basic database operations like read, write, and rollback.
    It manages a file-based data storage to persist data and maintains a buffer
    for write operations.

    Attributes:
        data_file_path (str): Path to the database file.
        data (list): In-memory representation of the database data.
        buffer (list): Buffer to store write operations before flushing to file.
        write_count (int): Counter to track the number of writes since last flush.
    """

    def __init__(self):
        """Initialize the Database class."""
        self.data_file_path = 'data/db.txt'
        self.ensure_data_directory_exists()
        self.ensure_data_file_exists()
        self.data = ['0'] * 32  # Initialize database with 32 bits set to '0'
        self.buffer = []  # Buffer to store write operations
        self.load_from_file()
        self.write_count = 0

    def ensure_data_directory_exists(self):
        """Ensure that the data directory exists, create it if it doesn't."""
        os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)

    def ensure_data_file_exists(self):
        """Ensure that the data file exists, create it with default data if it doesn't."""
        if not os.path.exists(self.data_file_path):
            with open(self.data_file_path, 'w') as f:
                f.write('0' * 32)

    def load_from_file(self):
        """
        Load data from the data file into memory.

        This method reads the data file and loads its content into the `data` attribute.
        It ensures that the data is valid (32 characters long and only contains '0' and '1').
        """
        if os.path.exists(self.data_file_path):
            with open(self.data_file_path, 'r') as f:
                data = f.read().strip()
                if len(data) == 32 and all(bit in '01' for bit in data):
                    self.data = list(data)

    def read(self, did):
        """
        Read a value from the database.

        Args:
            did (int): The index of the data item to read.

        Returns:
            str or None: The value of the data item if within range, otherwise None.
        """
        if 0 <= did < 32:
            return self.data[did]
        return None

    def write(self, trid, did, value):
        """
        Write a value to the database.

        Args:
            trid (int): The transaction ID.
            did (int): The index of the data item to write.
            value (str): The value to write.
        """
        value = str(value)  # Convert value to string
        if 0 <= did < 32 and value in '01':
            self.buffer.append((did, value))
            self.data[did] = value
            self.write_count += 1
            if self.write_count % 25 == 0:
                self.flush()

    def rollback_write(self, did, value):
        """
        Roll back a write operation by setting a specific value at a given index.

        Args:
            did (int): The index of the data item to rollback.
            value (str): The value to set for rollback.
        """
        value = str(value)  # Convert value to string for comparison
        if 0 <= did < 32 and value in '01':
            self.data[did] = value
            self.flush()

    def flush(self):
        """
        Flush the buffer contents to the data file and clear the buffer.

        This method writes the current state of `data` to the data file and resets
        the buffer and write count.
        """
        with open(self.data_file_path, 'w') as f:
            f.write(''.join(self.data))
        self.write_count = 0
        self.buffer.clear()

    def close(self):
        """Output the database state before closing."""
        print("Database Internal State Before Crash:")
        print(''.join(self.data))

    def reset_data_file(self):
        """
        Reset the data file to the default state.

        This method overwrites the existing data file with the default data (32 '0's).
        """
        with open(self.data_file_path, 'w') as f:
            f.write('0' * 32)

    def rollback(self, did, old_value):
        """
        Roll back a write operation by setting a specific old value at a given index.

        Args:
            did (int): The index of the data item to rollback.
            old_value (str): The old value to set for rollback.
        """
        if 0 <= did < len(self.data):
            self.data[did] = str(old_value)
