class DoublyLinkedList:
    """
    A simple implementation of a doubly linked list.

    This class provides basic functionalities of a doubly linked list such as
    appending a new node, removing an existing node, and finding a node by a specific key.

    Attributes:
        head (Node): The first node in the linked list.
        tail (Node): The last node in the linked list.
    """

    def __init__(self):
        """Initialize a new empty doubly linked list."""
        self.head = None
        self.tail = None

    def append(self, node):
        """
        Append a new node to the end of the list.

        Args:
            node (Node): The node to be appended to the list.
        """
        if not self.head:
            # If the list is empty, set both head and tail to the new node
            self.head = node
            self.tail = node
        else:
            # Link the new node to the current tail and update the tail reference
            self.tail.next = node
            node.prev = self.tail
            self.tail = node

    def remove(self, node):
        """
        Remove a node from the list.

        Args:
            node (Node): The node to be removed from the list.
        """
        if node.prev:
            # If the node is not at the head, link the previous node to the next node
            node.prev.next = node.next
        if node.next:
            # If the node is not at the tail, link the next node to the previous node
            node.next.prev = node.prev
        if node == self.head:
            # If the node is the head, update the head reference
            self.head = node.next
        if node == self.tail:
            # If the node is the tail, update the tail reference
            self.tail = node.prev
        # Disconnect the node from the list
        node.prev = None
        node.next = None

    def find(self, transaction_id):
        """
        Find a node by its transaction ID.

        Args:
            transaction_id (int): The transaction ID to find.

        Returns:
            Node: The node with the matching transaction ID, or None if not found.
        """
        current = self.head
        while current:
            if current.transaction_id == transaction_id:
                return current
            current = current.next
        return None
