import threading
import random

class Node:
    def __init__(self, id):
        self.id = id
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.state_machine = {}
        self.leader_id = None

    def start_election(self):
        self.current_term += 1
        print(f"Node {self.id} started election term {self.current_term}")
        self.send_request_votes()

    def send_request_votes(self):
        for node in range(3):  # Simplified example with only 3 nodes
            if node != self.id:
                self.request_vote(node)

    def request_vote(self, node_id):
        print(f"Node {self.id} sent vote request to Node {node_id}")
        response = random.choice([True, False])  # Simplified response (in real Raft, this would be a more complex process)
        if response:
            self.voted_for = node_id
            print(f"Node {self.id} voted for Node {node_id}")
        else:
            print(f"Node {self.id} did not vote for Node {node_id}")

    def start_leader(self):
        self.leader_id = self.id
        print(f"Node {self.id} is now the leader")

    def send_log_entries(self, node_id):
        if self.leader_id == self.id:
            entry = f"log entry {random.randint(1, 100)}"
            self.log.append(entry)
            print(f"Leader Node {self.id} sent log entry '{entry}' to Node {node_id}")

    def apply_log_entries(self, node_id):
        if node_id == self.leader_id:
            for entry in self.log:
                print(f"Node {self.id} applied log entry '{entry}'")
                self.state_machine[entry] = True
        else:
            print(f"Node {self.id} did not apply log entry")

def main():
    nodes = [Node(i) for i in range(3)]

    # Simulate network communication and node failures
    threads = []
    for node in nodes:
        t = threading.Thread(target=node.start_election)
        t.start()
        threads.append(t)

    for _ in range(5):  # Simplified example with only 5 iterations
        for node in nodes:
            if random.random() < 0.2:  # Simulate network failure (20% chance)
                print(f"Node {node.id} failed!")
                continue

            if node.id == 0:  # Node 0 is the leader
                node.start_leader()
                for other_node in nodes:
                    if other_node.id != node.id:
                        node.send_log_entries(other_node.id)

            else:
                for log_entry in node.log:
                    node.apply_log_entries(node.id)
                    print(f"Node {node.id} applied log entry '{log_entry}'")

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
