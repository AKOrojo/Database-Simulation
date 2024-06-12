# Database Simulation System Documentation

## Introduction
This documentation provides an overview of the Database Simulation System, a Python-based application designed to simulate database operations, including transaction management, locking, recovery, and deadlock detection.

## System Requirements
- Python 3.11
- No external libraries required.

## Components
1. **main.py**: The entry point of the application, handling argument parsing and coordinating the simulation process.
2. **database.py**: Implements the Database class, which simulates a basic database with read, write, and rollback functionalities.
3. **lock_manager.py**: Contains the LockManager class responsible for managing locks to ensure transaction consistency.
4. **recovery_manager.py**: Features the RecoveryManager class for handling transaction recovery and logging.
5. **lock_list.py**: Defines the DoublyLinkedList class, used in LockManager for maintaining locks.
6. **lock_node.py**: Introduces the Node class, representing individual lock nodes in DoublyLinkedList.

## Installation Guide
- Clone or download the repository from the provided source.
- Ensure Python 3.x is installed on your system.

## How to Run the Code

### Running the Simulation:
- Open a terminal or command prompt.
- Navigate to the directory containing main.py.
- Run the command: \`python main.py [OPTIONS]\`
  
  \`[OPTIONS]\` include:
  - \`--recover\`: Run in recovery mode only.
  - \`cycles\`: Maximum number of cycles for the simulation (default=0).
  - \`trans_size\`: Size of the transaction in number of operations (default=0).
  - \`start_prob\`: Probability of a transaction starting per cycle (default=0.0).
  - \`write_prob\`: Probability that each operation is a write (default=0.0).
  - \`rollback_prob\`: Probability of a rollback operation (default=0.0).
  - \`timeout\`: Timeout wait (default=0).

Example:
\`\`\`sh
python main.py 100 5 0.5 0.3 0.1 30
python main.py --recover
\`\`\`

### Exiting the Simulation:
- The simulation runs for the specified number of cycles or until manually terminated.

## Code Structure and Explanation

### main.py - Entry Point for Database Simulation
Functionality: main.py serves as the primary entry point for a database simulation system. It is responsible for orchestrating the entire workflow of the simulation. This includes parsing command-line arguments, initializing core system components, and managing the lifecycle of the simulation.

Key Operations:
1. **Argument Parsing**:
   - Utilizes argparse for handling command-line arguments.
   - Allows configuration of various aspects of the simulation, such as the number of cycles, transaction size, and probabilities of different operations.

2. **Component Initialization**:
   - Instantiates the essential components of the simulation: Database, LockManager, and RecoveryManager.
   - Each component is integral to the simulation, handling specific aspects of database management and transaction processing.

3. **Recovery Process**:
   - Automatically initiates a recovery process at the start of the simulation using the RecoveryManager.
   - Ensures consistency and integrity of the database state, irrespective of the simulation mode.

4. **Simulation Cycle**:
   - Executes the simulation for a predefined number of cycles.
   - Manages and processes transactions, adapting to the probabilities and parameters defined through the command-line arguments.

5. **Deadlock Handling**:
   - Integrates deadlock detection and resolution mechanisms within the LockManager.
   - Ensures smooth transaction processing by managing locks and resolving potential deadlocks.

6. **Finalization**:
   - Responsibly closes all system components at the end of the simulation.
   - Ensures a clean and orderly shutdown of the simulation, maintaining the integrity of the system state.

### database.py - Simulating Database Operations
- **Purpose**: Mimics basic database functionalities, including read, write, and data persistence.
- **Implementation Details**:
  - **Data Initialization**: Initializes a data array representing the database and a buffer for write operations.
  - **File Operations**: Ensures the existence of data files and directories. Reads and writes to the data file to simulate data persistence.
  - **Read and Write**: Provides methods for reading and writing data, including rollback capabilities for undoing operations.

### lock_manager.py - Managing Transaction Locks in Database Simulation
**Function**: The LockManager class in lock_manager.py plays a vital role in ensuring transaction consistency and isolation in a database simulation environment. It manages locks on data items, handling the complex aspects of lock acquisition, release, deadlock detection, and resolution.

**Components and Key Features**:
1. **Lock Table**:
   - Implemented as a hash table (self.lock_table) mapping data item IDs to their associated locks.
   - Each lock is represented in a DoublyLinkedList, allowing efficient addition and removal of locks.

2. **Lock Acquisition and Release**:
   - \`acquire_lock\`: Method to attempt acquiring a lock (shared or exclusive) on a data item for a given transaction.
   - Handles lock compatibility checks and lock upgrades (from shared to exclusive).
   - If a lock cannot be acquired due to an existing incompatible lock, the transaction is added to the waiting queue.
   - \`release_lock\`: Method to release a lock held by a transaction.
   - Processes waiting transactions after a lock is released, to ensure continued progress of other transactions.

3. **Transaction Lock Management**:
   - Tracks locks held by each transaction (self.transaction_locks) to facilitate lock release and management.
   - Provides a method (\`release_all_locks\`) to release all locks held by a transaction, useful in rollback scenarios.

4. **Deadlock Detection and Resolution**:
   - \`detect_deadlock\`: Implements a mechanism to detect deadlocks by constructing and analyzing a wait-for graph of transactions.
   - \`resolve_deadlock\`: Resolves deadlocks by choosing a victim transaction to rollback, based on predefined criteria or probabilities.

5. **Handling Blocked Transactions**:
   - Manages blocked transactions (self.blocked_transactions) with associated timestamps to detect and resolve situations where transactions are waiting excessively long for locks.

6. **Timeout and Rollback**:
   - Considers a timeout parameter to handle transactions that are blocked for longer than the specified duration.
   - Invokes the rollback mechanism through recovery_manager for transactions exceeding the timeout.

7. **Finalization**:
   - A close method to clean up and clear all lock-related data, ensuring a proper shutdown of the lock manager.

### recovery_manager.py - Handling Transaction Recovery in Database Simulation
**Objective**: The RecoveryManager class in recovery_manager.py is crucial for ensuring the integrity and consistency of the database during and after transaction processing. It manages the logging and recovery of transactions, playing a key role in maintaining a stable database state, especially in the event of failures.

**Key Features**:
1. **Logging Operations**:
   - Logs crucial transaction events: start (S), update (F), commit (C), and rollback (R).
   - Maintains a log_buffer for storing log records before they are flushed to the log file, optimizing write operations.

2. **Log File Management**:
   - Manages the transaction log file (log_file_path), ensuring its existence and handling its creation if absent.
   - Implements \`flush_log\` to write buffered log entries to the log file, ensuring durability of log records.

3. **Recovery Algorithm**:
   - Implements a log-based recovery process, crucial for restoring the database to a consistent state post-failure.
   - \`recover\` method:
     - **Phase 1: Analysis** - Reads the log to identify active and rolled-back transactions and determines the start point for redo operations.
     - **Phase 2: Redo** - Re-applies committed transaction operations to ensure all changes are reflected in the database.
     - **Phase 3: Undo** - Rolls back uncommitted or incomplete transactions, undoing their effects to maintain consistency.

4. **Transaction Rollback**:
   - Handles transaction rollbacks (\`rollback_transaction\`) by reversing the operations of a specified transaction based on log records.
   - Utilizes log entries to accurately revert changes made by the transaction.

5. **Integration with Database**:
   - Closely interacts with the Database class (referenced as database) to read and write data items as part of recovery and rollback processes.

6. **Log Resetting**:
   - Provides \`reset_log_file\` to clear the log after successful recovery, preparing the log for new transactions.

7. **Resource Management**:
   - \`close\` method for cleaning up resources and ensuring that all pending logs are flushed, maintaining log integrity.

8. **Return of Maximum Transaction ID**:
   - \`recover\` method returns the highest transaction ID encountered in the log, assisting in transaction management post-recovery.

### lock_list.py and lock_node.py - Supporting the Lock Manager
- **lock_list.py**: Defines the DoublyLinkedList class, which is a fundamental part of the lock manager's data structure.
- **lock_node.py**: Describes the Node class, representing each lock in the DoublyLinkedList. It holds information about the transaction ID and the type of lock.

## Interactions Between Components
- **Transactions**: Managed in main.py, transactions are the central focus of the simulation. They interact with the database and are subject to locking mechanisms.
- **Database Operations**: Each transaction performs operations (read/write) on the database. The Database class handles these operations, ensuring data integrity and persistence.
- **Lock Management**: The LockManager oversees locks on data items for each transaction. It works closely with the transaction flow in main.py to ensure no two transactions conflict when accessing the same data.
- **Recovery Process**: RecoveryManager plays a critical role in maintaining consistency. It logs all transaction operations and performs recovery steps as needed, especially after system failures or during the initialization phase.
