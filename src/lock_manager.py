import random
from src.lock_list import DoublyLinkedList
from src.lock_node import Node


class LockManager:
    """
        Manages locks for transactions in a database simulation.

        This class handles the acquisition and release of locks for transactions,
        ensuring data consistency. It also includes mechanisms for deadlock detection
        and resolution.

        Attributes:
            lock_table (dict): A dictionary mapping data item IDs to their corresponding lock lists.
            waiting_transactions (dict): Tracks transactions waiting for a lock along with the requested lock type.
            transaction_locks (dict): A dictionary mapping transaction IDs to a set of data item IDs they have locks on.
    """

    def __init__(self, rollback_prob=0.0, timeout=0):
        """Initialize the LockManager with empty structures for managing locks."""
        self.lock_table = {}  # Hash table: {data_item_id: DoublyLinkedList}
        self.waiting_transactions = {}  # {transaction_id: (data_item_id, lock_type)}
        self.transaction_locks = {}  # New dictionary to track locks per transaction
        self.rollback_prob = rollback_prob
        self.timeout = timeout
        self.blocked_transactions = {}  # New dict to track blocked transactions and their timestamps

    def acquire_lock(self, trid, did, lock_type):
        """
        Attempt to acquire a lock for a transaction on a specific data item.

        Args:
            trid (int): Transaction ID.
            did (int): Data item ID.
            lock_type (str): Type of lock ('S' for shared, 'X' for exclusive).

        Returns:
            bool: True if the lock was acquired, False otherwise.
        """
        # Get or create the lock list for the data item
        lock_list = self.lock_table.setdefault(did, DoublyLinkedList())

        # Check if the data item is already locked by other transactions
        current = lock_list.head
        while current:
            if current.transaction_id == trid:
                # If the requesting transaction already holds the lock
                if lock_type == 'X' and current.lock_type == 'S':
                    current.lock_type = 'X'  # Upgrade lock to exclusive if needed
                return True  # Lock already held by this transaction
            if (current.lock_type == 'X') or (lock_type == 'X' and current.lock_type == 'S'):
                # Lock cannot be acquired due to an existing incompatible lock
                self.waiting_transactions[trid] = (did, lock_type)

                return False
            current = current.next

        # The data item is not locked by this transaction, so acquire the lock
        new_node = Node(trid, lock_type)
        lock_list.append(new_node)

        # Add the data item to the set of locks held by the transaction
        if trid not in self.transaction_locks:
            self.transaction_locks[trid] = set()
        self.transaction_locks[trid].add(did)

        return True

    def release_lock(self, trid, did):
        """
        Release a lock held by a transaction on a specific data item.

        Args:
            trid (int): Transaction ID.
            did (int): Data item ID.

        Returns:
            bool: True if the lock was released, False otherwise.
        """
        # Retrieve the list of locks for the given data item
        lock_list = self.lock_table.get(did)
        if not lock_list:
            return False

        # Find and remove the lock node corresponding to the transaction
        node_to_release = lock_list.find(trid)
        if node_to_release:
            lock_list.remove(node_to_release)

            # Process waiting transactions if necessary
            # [Add logic here if you need to handle waiting transactions after releasing a lock]

            # Remove the data item from the set of locks held by the transaction
            if trid in self.transaction_locks and did in self.transaction_locks[trid]:
                self.transaction_locks[trid].remove(did)
                if not self.transaction_locks[trid]:  # If no more locks, remove the transaction entry
                    del self.transaction_locks[trid]

            return True
        return False

    def release_all_locks(self, trid):
        """
        Release all locks held by a given transaction.

        Args:
            trid (int): Transaction ID.
        """
        if trid not in self.transaction_locks:
            return

        # Release each lock held by the transaction
        for did in self.transaction_locks[trid].copy():
            self.release_lock(trid, did)

    def detect_deadlock(self, active_transactions, recovery_manager, current_cycle):
        """
        Detect and resolve deadlocks among transactions.

        Args:
            active_transactions (dict): Currently active transactions.
            recovery_manager (RecoveryManager): The recovery manager instance for handling rollbacks.
            current_cycle (int): The current cycle number in the transaction processing loop.

        Returns:
            bool: True if a deadlock was detected and resolved, False otherwise.
        """

        # Check for transactions that exceeded the timeout after handling deadlocks
        self.check_timeouts(recovery_manager, active_transactions, current_cycle)
        
        # Build the wait-for graph
        wait_for_graph = {}
        for trid, (did, _) in self.waiting_transactions.items():
            lock_list = self.lock_table.get(did)
            if lock_list:
                current = lock_list.head
                while current:
                    if current.transaction_id != trid:
                        if current.transaction_id not in wait_for_graph:
                            wait_for_graph[current.transaction_id] = set()
                        wait_for_graph[current.transaction_id].add(trid)
                    current = current.next

        # Detect cycles in the wait-for graph
        visited = set()
        rec_stack = set()
        for node in wait_for_graph:
            if node not in visited:
                if self.is_cyclic_util(node, wait_for_graph, visited, rec_stack):
                    self.resolve_deadlock(rec_stack, active_transactions, recovery_manager, current_cycle)
                    return True

        return False

    def resolve_deadlock(self, deadlock_cycle, active_transactions, recovery_manager, current_cycle):
        """
        Resolve a deadlock by choosing a victim transaction to rollback.

        Args:
            deadlock_cycle (set): Set of transaction IDs involved in the deadlock.
            active_transactions (dict): Currently active transactions.
            recovery_manager (RecoveryManager): The recovery manager instance.
            current_cycle (int): The current cycle number in the transaction processing loop.
        """
        # Choose the victim transaction
        victim = min(deadlock_cycle, key=lambda trid: active_transactions.get(trid, (float('inf'),))[0])
        if victim not in active_transactions:
            return

        # Rollback the victim transaction
        if random.random() < self.rollback_prob:
            self.lock_manager_rollback(recovery_manager, victim, active_transactions)
        else:
            if victim not in self.blocked_transactions:
                self.blocked_transactions[victim] = current_cycle

    def lock_manager_rollback(self, recovery_manager, victim, active_transactions):

        recovery_manager.rollback_transaction(victim)

        # Release locks held by the victim
        for did, lock_list in self.lock_table.items():
            node = lock_list.find(victim)
            if node:
                self.release_all_locks(victim)

        # Remove the victim from waiting transactions
        if victim in self.waiting_transactions:
            del self.waiting_transactions[victim]

        # Remove the victim from active transactions
        if victim in active_transactions:
            del active_transactions[victim]

    def is_cyclic_util(self, node, graph, visited, rec_stack):
        """
        Utility function to check for cycles in a graph (used for deadlock detection).

        Args:
            node (int): The current node (transaction ID) being visited.
            graph (dict): The graph representing waiting transactions.
            visited (set): Set of visited nodes.
            rec_stack (set): Set of nodes currently in the recursion stack.

        Returns:
            bool: True if a cycle is detected, False otherwise.
        """
        visited.add(node)
        rec_stack.add(node)

        if node in graph:
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if self.is_cyclic_util(neighbor, graph, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True

        rec_stack.remove(node)
        return False

    def close(self):
        """Clean up the lock manager by clearing all lock-related data."""
        self.lock_table.clear()
        self.waiting_transactions.clear()

    def check_timeouts(self, recovery_manager, active_transactions, current_cycle):
        """
        Check for transactions that have been waiting longer than the timeout
        and trigger a rollback if necessary.
        """
        for trid, cycle in list(self.blocked_transactions.items()):
            if current_cycle - cycle > self.timeout:
                self.lock_manager_rollback(recovery_manager, trid, active_transactions)
                del self.blocked_transactions[trid]
