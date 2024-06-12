import argparse
import random
from src.recovery_manager import RecoveryManager
from src.lock_manager import LockManager
from src.database import Database


def main():
    """
    Main function for running the Database Simulation.

    This function sets up the argument parser for command-line options, initializes
    the main components (Database, LockManager, and RecoveryManager), and runs
    the simulation cycles, managing transactions throughout the process.
    """
    # Setup command-line argument parser
    parser = argparse.ArgumentParser(description='Database Simulation')
    parser.add_argument('--recover', action='store_true', help='Run in recovery mode only')
    parser.add_argument('cycles', type=int, nargs='?', default=0, help='Maximum number of cycles for the simulation')
    parser.add_argument('trans_size', type=int, nargs='?', default=0,
                        help='Size of the transaction in number of operations')
    parser.add_argument('start_prob', type=float, nargs='?', default=0.0,
                        help='Probability of a transactions starting per cycle')
    parser.add_argument('write_prob', type=float, nargs='?', default=0.0,
                        help='Probability that each operation is a write')
    parser.add_argument('rollback_prob', type=float, nargs='?', default=0.0, help='Probability of a rollback operation')
    parser.add_argument('timeout', type=int, nargs='?', default=0, help='Timeout wait')

    args = parser.parse_args()

    # Initialize main components of the simulation
    database = Database()
    lock_manager = LockManager(rollback_prob=args.rollback_prob, timeout=args.timeout)
    recovery_manager = RecoveryManager(database)

    # Recovery phase: ensure the system is in a consistent state
    # Transaction ID counter
    next_trid = recovery_manager.recover()

    # Prepare to track active and completed transactions
    active_transactions = {}  # Format: {transaction_id: (operations_count, last_did)}

    completed_transactions = set()

    # Exit if recovery mode is specified
    if args.recover:
        return

    # Simulation cycles
    for cycle in range(args.cycles):
        # Decide whether to start a new transaction in this cycle
        if random.random() < args.start_prob:
            trid = next_trid
            next_trid += 1
            active_transactions[trid] = (0, None)
            recovery_manager.log_start(trid)

        # Process each active transaction
        for trid in list(active_transactions.keys()):
            count, last_did = active_transactions[trid]

            # Check if the transaction can perform more operations
            if count < args.trans_size:
                # Generate a random data item ID (did)
                did = random.randint(0, 31)

                # Decide on read or write operation
                if random.random() < args.write_prob:
                    # Write operation
                    old_value = database.read(did)
                    new_value = '1' if old_value == '0' else '0'
                    if lock_manager.acquire_lock(trid, did, 'X'):
                        database.write(trid, did, new_value)
                        recovery_manager.log_update(trid, did, old_value)
                else:
                    # Read operation
                    if lock_manager.acquire_lock(trid, did, 'S'):
                        database.read(did)

                active_transactions[trid] = (count + 1, did)
            else:
                # Transaction is ready to commit
                recovery_manager.log_commit(trid)
                _, did = active_transactions[trid]
                if did is not None:
                    lock_manager.release_all_locks(trid)
                del active_transactions[trid]
                completed_transactions.add(trid)

        # Handle deadlock scenarios
        lock_manager.detect_deadlock(active_transactions, recovery_manager, cycle)

    # Close all components and terminate the simulation
    recovery_manager.close()
    lock_manager.close()
    database.close()


if __name__ == "__main__":
    main()
