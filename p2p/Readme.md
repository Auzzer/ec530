## Python’s Socket Module & Client–Server Architecture:
Both server and client use Python’s socket module. The server listens on 127.0.0.1:5000 and handles multiple clients (each on a different local port if desired).

## Peer-to-Peer Communication with Full-Duplex Messaging:
Even though a centralized server is used for registration/discovery, the design supports full-duplex asynchronous messaging using separate threads for sending and receiving. The server relays messages between peers, and clients handle both sending and receiving concurrently.

## Asynchronous Handling Using Threading:
The server spawns a new thread for each connected client. The client spawns one thread to continuously receive messages and another to send periodic heartbeat messages while the main thread handles user input.

## Offline Message Storage & Delivery:
If the recipient is offline or fails to send a heartbeat, the server stores the message. When the recipient reconnects (registers), the server retrieves and sends the stored offline messages. There is an option to integrate Redis for persistent storage.

## Message Protocol for Automation/Notification:
The JSON-based protocol includes fields such as "action", "sender", "recipient", "timestamp", and "payload". This allows for automation (e.g., scheduled notifications) and offline message queuing until the recipient comes online.

## Discovery (Heartbeat/Keep-Alive):
Clients send heartbeat messages every few seconds so the server can track active connections. If a heartbeat is not received within a timeout period, the server considers the client offline.

## Database Integration (Redis Option):
The server code optionally integrates Redis to persist offline messages. If Redis is available, messages are stored in a Redis list keyed by client ID. Otherwise, an in-memory dictionary is used.

## Extensibility for Messaging API & Subscriber Features:
This basic framework can be extended further into an API-based messaging system (using Flask/FastAPI) or to include a publish-subscribe mechanism.

