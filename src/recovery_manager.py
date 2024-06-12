import csv
import os


class RecoveryManager:
    """
    Manages the logging and recovery of transactions in a database simulation.

    This class is responsible for logging transaction operations, handling rollbacks, and
    recovering the database state from logs after a failure.

    Attributes:
        log_file_path (str): Path to the transaction log file.
        database (Database): Reference to the associated database.
        active_transactions (set): Set of currently active transaction IDs.
        log_buffer (list): Buffer to store log records before flushing to the log file.
    """

    def __init__(self, database):
        """
        Initialize the RecoveryManager.

        Args:
            database (Database): The database instance associated with this recovery manager.
        """
        self.log_file_path = 'data/log.csv'
        self.database = database
        self.ensure_log_file_exists()
        self.active_transactions = set()
        self.log_buffer = []

    def ensure_log_file_exists(self):
        """Ensure the transaction log file exists, create it if it doesn't."""
        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'w') as f:
                csv.writer(f)

    def load_log(self):
        """
        Load the transaction log file and process its contents.

        This method reads the log file and reconstructs the state of active transactions.
        """
        if os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) == 2 and row[1] == 'S':
                        # Start record
                        trid = int(row[0])
                        self.active_transactions.add(trid)
                    elif len(row) == 4 and row[3] == 'F':
                        # Update record
                        trid = int(row[0])
                        did = int(row[1])
                        old_value = str(row[2])  # Ensure old_value is a string
                        self.database.write(trid, did, old_value)
                    elif len(row) == 2 and row[1] in {'C', 'R'}:
                        # Commit or Rollback record
                        trid = int(row[0])
                        if trid in self.active_transactions:
                            self.active_transactions.remove(trid)

    def log_start(self, trid):
        """
       Log the start of a transaction.

       Args:
           trid (int): Transaction ID.
       """
        self.active_transactions.add(trid)
        self.log_buffer.append(f'{trid},S')
        self.flush_log()

    def log_update(self, trid, did, old_value):
        """
        Log an update operation by a transaction.

        Args:
            trid (int): Transaction ID.
            did (int): Data item ID.
            old_value (str): The old value of the data item.
        """
        self.log_buffer.append(f'{trid},{did},{old_value},F')
        if len(self.log_buffer) >= 25:
            self.flush_log()

    def log_commit(self, trid):
        """
        Log the commit of a transaction.

        Args:
            trid (int): Transaction ID.
        """
        if trid in self.active_transactions:
            self.active_transactions.remove(trid)
        self.log_buffer.append(f'{trid},C')
        self.flush_log()

    def log_rollback(self, trid):
        """
        Log the rollback of a transaction.

        Args:
            trid (int): Transaction ID.
        """
        if trid in self.active_transactions:
            self.active_transactions.remove(trid)
        self.log_buffer.append(f'{trid},R')
        self.flush_log()

    def flush_log(self):
        """Flush the log buffer to the log file."""
        with open(self.log_file_path, 'a') as f:
            for record in self.log_buffer:
                # Join the record with commas and add a newline character at the end
                f.write(','.join(record.split(',')) + '\n')
        self.log_buffer.clear()

    def rollback_transaction(self, trid):
        """
        Rollback the operations of a transaction using the log file.

        Args:
            trid (int): Transaction ID.
        """
        self.flush_log()

        # Read the log file in reverse order to find the operations of the victim transaction
        with open(self.log_file_path, 'r') as f:
            reader = list(csv.reader(f))
            for row in reversed(reader):
                if len(row) == 2 and row[1] == 'S' and int(row[0]) == trid:
                    # Stop processing after encountering the start record of the transaction
                    break
                elif len(row) == 4 and row[3] == 'F' and int(row[0]) == trid:
                    # Found a write operation by the victim transaction
                    _, did, old_value = map(int, row[:3])
                    self.database.write(_, did, old_value)  # Undo the write operation

        # Log the rollback
        self.log_rollback(trid)

    def recover(self):
        """Perform recovery of the database using the log file."""

        # Initialize max_trid to 0
        max_trid = 0

        # Phase 1: Analysis
        active_transactions = set()
        rolled_back_transactions = set()
        min_lsn_to_redo = float('inf')
        with open(self.log_file_path, 'r') as f:
            reader = csv.reader(f)
            for lsn, row in enumerate(reader):
                if len(row) == 2 and row[1] == 'S':
                    # Start record
                    trid = int(row[0])
                    max_trid = max(max_trid, trid)
                    active_transactions.add(trid)
                    min_lsn_to_redo = min(min_lsn_to_redo, lsn)
                elif len(row) == 2 and row[1] in {'C'}:
                    # Commit record
                    trid = int(row[0])
                    if trid in active_transactions:
                        active_transactions.remove(trid)
                elif len(row) == 2 and row[1] in {'R'}:
                    # Commit record
                    trid = int(row[0])
                    rolled_back_transactions.add(trid)
                    if trid in active_transactions:
                        active_transactions.remove(trid)

        # Phase 2: Redo
        with open(self.log_file_path, 'r') as f:
            log_operations = list(csv.reader(f))
            for i, operation in enumerate(log_operations):
                if len(operation) == 4 and operation[3] == 'F':
                    # Apply update operations by toggling the bit
                    trid, did, _ = map(int, operation[:3])
                    current_value = self.database.read(did)
                    new_value = '1' if current_value == '0' else '0'
                    self.database.write(trid, did, new_value)

        # Flush buffer after Redo
        self.database.flush()

        # Phase 3: Undo
        with open(self.log_file_path, 'r') as f:
            reader = list(csv.reader(f))
            for row in reversed(reader):
                if len(row) == 4 and row[3] == 'F':
                    trid, did, old_value = map(int, row[:3])
                    if trid in active_transactions or trid in rolled_back_transactions:
                        # Undo the update by writing back the old value
                        self.database.write(trid, did, old_value)
                        # Note: We could log each undone operation here if needed
                elif len(row) == 2 and row[1] == 'S' and int(row[0]) in active_transactions:
                    # When we reach the start of an active transaction, log the rollback
                    trid = int(row[0])
                    self.log_rollback(trid)
                    active_transactions.remove(trid)
                elif len(row) == 2 and row[1] == 'S' and int(row[0]) in rolled_back_transactions:
                    # When we reach the start of an active transaction, log the rollback
                    trid = int(row[0])
                    rolled_back_transactions.remove(trid)

        # Flush buffer after Undo
        self.database.flush()

        # After successfully completing recovery, reset the log file
        self.reset_log_file()

        return max_trid

    def close(self):
        """Close the recovery manager and flush any remaining logs."""
        self.flush_log()

    def reset_log_file(self):
        """Reset the log file to an empty state."""
        # This method will create a new log.csv, overwriting any existing file
        with open(self.log_file_path, 'w') as f:
            f.write('')
