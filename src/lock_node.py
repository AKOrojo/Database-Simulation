class Node:
    """
    A class representing a node in a doubly linked list.

    This node is used to store information about a transaction's lock within a doubly linked list.
    It contains details about the transaction ID and the type of lock, along with pointers to
    the previous and next nodes in the list.

    Attributes:
        transaction_id (int): The ID of the transaction associated with this node.
        lock_type (str): The type of lock (e.g., 'S' for shared, 'X' for exclusive).
        prev (Node): Reference to the previous node in the list.
        next (Node): Reference to the next node in the list.
    """

    def __init__(self, transaction_id, lock_type):
        """
        Initialize a new node with transaction information and lock type.

        Args:
            transaction_id (int): The ID of the transaction.
            lock_type (str): The type of lock associated with the transaction.
        """
        self.transaction_id = transaction_id
        self.lock_type = lock_type
        self.prev = None  # Initially, the node is not linked to any other node
        self.next = None
