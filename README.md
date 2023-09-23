# p2p-distributed-messaging
This is a demo project to simulate p2p messaging in a distributed environment.

To start the project:
1. Start the auth server using
    python index.py
This will start the auth server at port 12345 of localhost

2. start nodes using:
    python node_client.py
This file simulates the start of nodes and starts p2p and group messages

Working:
The auth server uses the authServerClass which in turn uses an objet of usersDatabase class. 
The usersDatabase stores the credentials of each user such that a user can signout and signin later to resume their session.
Furthermore the authserver has the methods to handle these authentication/authorization procedures.

To start a node, userInput Class is used. An object of that class hosts an object of node Class. Each node is tied with a port.
Every functionality of userInput Class uses a function of node Class but with a level of abstraction.


Improvements:
You can modify the usersDatabase class to become a wrapper for a SQL/NOSQL Database so that if the auth server restarts, it can resume from a previous state.
You can add local storages to each node where a user has signed in, when the user gets signed out, that local storage gets purged. But with a critical number of nodes online, chat history could be preserved using a distributed kind of storage.
You can build a protocol to sync messages if they get purged for a user.