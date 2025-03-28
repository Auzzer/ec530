import socket
import threading
import json
import time
import sys

# Server configuration (connect to the central server)
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000

# Heartbeat interval (seconds)
HEARTBEAT_INTERVAL = 5

def send_heartbeat(sock, client_id):
    """Send heartbeat messages periodically to the server."""
    while True:
        heartbeat_msg = {
            "action": "heartbeat",
            "sender": client_id,
            "timestamp": time.time()
        }
        try:
            sock.send(json.dumps(heartbeat_msg).encode())
        except Exception as e:
            print("Heartbeat error:", e)
            break
        time.sleep(HEARTBEAT_INTERVAL)

def receive_messages(sock):
    """Continuously receive messages from the server."""
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                print("Server closed connection.")
                break
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                print("Received invalid message:", data)
                continue
            # Print received message.
            if message.get("action") == "message":
                sender = message.get("sender")
                payload = message.get("payload")
                print(f"\n[New message] From '{sender}': {payload}\n> ", end="")
        except Exception as e:
            print("Error receiving message:", e)
            break

def send_messages(sock, client_id):
    """Prompt the user to send messages."""
    while True:
        try:
            recipient = input("Enter recipient ID: ")
            if recipient.strip() == "":
                continue
            payload = input("Enter your message: ")
            message = {
                "action": "message",
                "sender": client_id,
                "recipient": recipient,
                "timestamp": time.time(),
                "payload": payload
            }
            sock.send(json.dumps(message).encode())
        except Exception as e:
            print("Error sending message:", e)
            break

def main():
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    else:
        client_id = input("Enter your client ID: ")

    # Optionally, you can specify a local port for the client.
    local_port = None
    if len(sys.argv) > 2:
        local_port = int(sys.argv[2])
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if local_port:
        # Bind the client socket to a specific port on 127.0.0.1.
        sock.bind(('127.0.0.1', local_port))
    try:
        sock.connect((SERVER_HOST, SERVER_PORT))
    except Exception as e:
        print("Could not connect to server:", e)
        return

    # Send registration message.
    register_msg = {
        "action": "register",
        "sender": client_id,
        "timestamp": time.time()
    }
    sock.send(json.dumps(register_msg).encode())
    print(f"Registered with server as '{client_id}'.")

    # Start heartbeat thread.
    threading.Thread(target=send_heartbeat, args=(sock, client_id), daemon=True).start()
    # Start thread for receiving messages.
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    # Main thread handles user input for sending messages.
    send_messages(sock, client_id)
    sock.close()

if __name__ == '__main__':
    main()
