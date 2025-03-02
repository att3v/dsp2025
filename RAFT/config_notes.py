def main(): #esim 3 nodes
    network = {
        0: Follower(0, network, '192.168.1.2', 5000),
        1: Leader(1, network, '192.168.1.3', 5001),
        2: Follower(2, network, '192.168.1.4', 5002)
    }

    for node in network.values():
        t = threading.Thread(target=node.start_election)
        t.start()

    # ...existing code...
    import random
import threading
from abc import ABC, abstractmethod

class Node(ABC):
    def __init__(self, id: int, network: dict):
        self.id = id
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.state_machine = {}
        self.network = network
        self.leader_id = None

    @abstractmethod
    def start_election(self) -> None:
        pass

    @abstractmethod
    def request_vote(self, node_id: int) -> bool:
        pass

    @abstractmethod
    def send_log_entries(self, node_id: int) -> None:
        pass

    @abstractmethod
    def apply_log_entries(self, log_entry: str) -> None:
        pass

class Leader(Node):
    def start_election(self) -> None:
        self.current_term += 1
        print(f"Node {self.id} started election term {self.current_term}")
        self.send_request_votes()

    def send_request_votes(self) -> None:
        for node_id in range(3):  # Simplified example with only 3 nodes
            if node_id != self.id:
                response = self.request_vote(node_id)
                if response:
                    self.voted_for = node_id
                    print(f"Node {self.id} voted for Node {node_id}")
                else:
                    print(f"Node {self.id} did not vote for Node {node_id}")

    def send_log_entries(self, node_id: int) -> None:
        entry = f"log entry {random.randint(1, 100)}"
        self.log.append(entry)
        print(f"Leader Node {self.id} sent log entry '{entry}' to Node {node_id}")
        self.network[node_id].send_log_entry(entry)

class Follower(Node):
    def start_election(self) -> None:
        if random.random() < 0.2:  # Simulate network failure (20% chance)
            print(f"Node {self.id} failed!")
            return

        for node in self.network.values():
            if node.id != self.id:
                response = node.request_vote(self.id)
                if response:
                    self.voted_for = self.id
                    print(f"Node {self.id} voted for Node {self.id}")
                else:
                    print(f"Node {self.id} did not vote for Node {self.id}")

    def apply_log_entries(self, log_entry: str) -> None:
        if log_entry.startswith("log entry "):
            entry_id = int(log_entry.split()[2])
            self.state_machine[entry_id] = True
            print(f"Node {self.id} applied log entry '{log_entry}'")

def main():
    network = {
        0: Follower(0),
        1: Leader(1, network),
        2: Follower(2)
    }

    for node in network.values():
        t = threading.Thread(target=node.start_election)
        t.start()

    for _ in range(5):  # Simplified example with only 5 iterations
        for node_id, node in network.items():
            if random.random() < 0.2:  # Simulate network failure (20% chance)
                print(f"Node {node.id} failed!")
                continue

            if node_id == 1:
                leader = node
                for follower_id, follower in network.items():
                    if follower_id != node_id:
                        leader.send_log_entries(follower_id)

            else:
                for log_entry in leader.log:
                    leader.apply_log_entries(log_entry)

    for t in [threading.Thread(target=network[0].start_election) for _ in range(3)]:
        t.start()
        t.join()

if __name__ == "__main__":
    main()
