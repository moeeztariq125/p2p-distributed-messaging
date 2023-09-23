import argparse
from node.userInput import UserInput
import signal
import sys
import time

def signal_handler(signal, frame):
    print("\nStopping UserInput...")
    user.stop_node()
    sys.exit(0)

if __name__ == "__main__":
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="Node Client")

    # Add command-line arguments for port number and username
    parser.add_argument("port", type=int, help="The port number to connect to")
    parser.add_argument("username", type=str, help="The username for the node")

    # Parse the command-line arguments
    args = parser.parse_args()

    node_host = "127.0.0.1"  # Replace with the desired node host IP or hostname
    auth_server_host = "127.0.0.1"  # Replace with the auth server's IP or hostname
    auth_server_port = 12345  # Replace with the auth server's port number
    signal.signal(signal.SIGINT, signal_handler)

    user = UserInput(node_host, args.port, auth_server_host, auth_server_port)
    user.start_node()
    user.signup(args.username, args.password)
    user.signin(args.username, args.password)
    time.sleep(5)
    if args.username == 'user2':
        time.sleep(10)
        user.send_private_message('3263',"hi there")
        time.sleep(2)
        user.send_private_message('3263',"hi there2")
        user.send_private_message('3263',"hi there3")
        time.sleep(5)
        user.send_private_message('3263',"hi there4")
        user.send_private_message('3263',"hi there5")
        time.sleep(7)
        user.send_private_message('3263',"hi there6")
        time.sleep(15)
        user.display_messages('3263')
    if args.username == 'user3':
        user.send_private_message('3536',"hi there")
        user.send_private_message('3536',"hi there2")
        time.sleep(2)
        user.send_private_message('3536',"hi there3")
        user.send_private_message('3536',"hi there4")
        time.sleep(6)
        user.send_private_message('3536',"hi there5")
        user.send_private_message('3536',"hi there6")
        time.sleep(15)
        user.display_messages('3536')

    try:
    # Run the server until you decide to stop it (e.g., by pressing Ctrl+C)
        while True:
            pass
    except KeyboardInterrupt:
        # When Ctrl+C is pressed, the KeyboardInterrupt exception is raised
        user.stop_node()



