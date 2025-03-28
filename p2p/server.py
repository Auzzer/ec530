import socket
import threading
import json
import time

# Optional Redis integration for persistent offline storage.
USE_REDIS = False
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    USE_REDIS = True
    print("Using Redis for offline message storage.")
except Exception as e:
    print("Redis not available, using in-memory storage. Error:", e)

# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000

# Data structures:
# clients: mapping from client_id to a dictionary with socket and last_seen timestamp.
clients = {}  # {client_id: {"socket": socket, "last_seen": timestamp}}
# For in-memory offline storage (used if Redis is not available)
offline_messages = {}  # {client_id: [message1, message2, ...]}

HEARTBEAT_TIMEOUT = 15  # seconds

def store_offline_message(recipient, message):
    if USE_REDIS:
        # Store the message as a JSON string in a Redis list keyed by "offline:<recipient>"
        redis_client.rpush(f"offline:{recipient}", json.dumps(message))
    else:
        offline_messages.setdefault(recipient, []).append(message)
    print(f"Stored offline message for {recipient}.")

def retrieve_offline_messages(client_id):
    messages = []
    if USE_REDIS:
        key = f"offline:{client_id}"
        while True:
            msg = redis_client.lpop(key)
            if msg is None:
                break
            messages.append(json.loads(msg))
    else:
        messages = offline_messages.pop(client_id, [])
    return messages

def handle_client(client_socket, address):
    client_id = None
    try:
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break  # client disconnected
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                print("Received invalid JSON:", data)
                continue

            action = message.get("action")

            if action == "register":
                client_id = message.get("sender")
                clients[client_id] = {"socket": client_socket, "last_seen": time.time()}
                print(f"[{time.ctime()}] Registered client '{client_id}' from {address}")
                # Check and deliver any offline messages.
                msgs = retrieve_offline_messages(client_id)
                if msgs:
                    for offline_msg in msgs:
                        try:
                            client_socket.send(json.dumps(offline_msg).encode())
                        except Exception as e:
                            print(f"Error sending offline message to {client_id}: {e}")
                continue

            elif action == "heartbeat":
                # Update last seen timestamp.
                if client_id in clients:
                    clients[client_id]["last_seen"] = time.time()
                continue

            elif action == "message":
                sender = message.get("sender")
                recipient = message.get("recipient")
                payload = message.get("payload")
                timestamp = message.get("timestamp")
                print(f"[{time.ctime()}] Message from '{sender}' to '{recipient}': {payload}")
                # Check if recipient is online and active.
                if recipient in clients and (time.time() - clients[recipient]["last_seen"] <= HEARTBEAT_TIMEOUT):
                    try:
                        clients[recipient]["socket"].send(json.dumps(message).encode())
                    except Exception as e:
                        print(f"Error sending message to {recipient}: {e}")
                        store_offline_message(recipient, message)
                else:
                    # Recipient offline or heartbeat timed out; store the message.
                    store_offline_message(recipient, message)
                continue

            else:
                print("Unknown action:", action)
    except Exception as e:
        print(f"Exception with client '{client_id}':", e)
    finally:
        if client_id:
            if client_id in clients:
                del clients[client_id]
            print(f"Connection with client '{client_id}' closed.")
        client_socket.close()

def heartbeat_checker():
    """Background thread to check for stale client connections."""
    while True:
        current_time = time.time()
        to_remove = []
        for client_id, info in list(clients.items()):
            if current_time - info["last_seen"] > HEARTBEAT_TIMEOUT:
                print(f"Client '{client_id}' timed out (last seen {int(current_time - info['last_seen'])} seconds ago).")
                to_remove.append(client_id)
        for client_id in to_remove:
            try:
                clients[client_id]["socket"].close()
            except Exception:
                pass
            del clients[client_id]
        time.sleep(5)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

    # Start heartbeat checking thread.
    threading.Thread(target=heartbeat_checker, daemon=True).start()

    while True:
        client_socket, address = server_socket.accept()
        print(f"Accepted connection from {address}")
        threading.Thread(target=handle_client, args=(client_socket, address), daemon=True).start()

if __name__ == '__main__':
    start_server()
