import socket

# Set the address and port number of the Node server
HOST = 'CT101'
PORT = 24

# Create a TCP socket object
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the Node server
try:
    sock.connect((HOST, PORT))
except Exception as e:
    print(f"Error connecting: {e}")
    exit(1)

print("Connected to Node server")

# Send a message to the Node server (replace with your own data)
data = "Hello from Python!".encode('utf-8')
sock.sendall(data)

# Receive response from Node server
response = sock.recv(1024).decode('utf-8')
print(f"Received response: {response}")

# Close the socket
sock.close()