from authServer.authServerClass import AuthServer
from authServer.usersDatabase import user_db
import signal
import sys

def signal_handler(signal, frame):
    print("\nStopping AuthServer...")
    server.stop()
    sys.exit(0)

host = "127.0.0.1"  # Replace with the desired host IP or hostname
port = 12345  # Replace with the desired port number
server = AuthServer(host, port, user_db)

# Set up the signal handler to catch SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

# Start the AuthServer
server.start()
try:
    # Run the server until you decide to stop it (e.g., by pressing Ctrl+C)
    while True:
        pass
except KeyboardInterrupt:
    # When Ctrl+C is pressed, the KeyboardInterrupt exception is raised
    # Gracefully stop the server and close the socket
    server.stop()
