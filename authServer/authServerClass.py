import socket
import threading
import random

class AuthServer:
    def __init__(self, host, port,userDB):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.client_thread = None
        self.user_db = userDB
        self.pending_requests = []  # List to store pending requests (node_id, ip_address)
        self.pending_requests_lock = threading.Lock()  # Lock to handle concurrent access to pending_requests
        self.should_stop = threading.Event()  # Event to indicate when the server should stop

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.running = True
            print(f"AuthServer: AuthServer listening on {self.host}:{self.port}")
            self.client_thread = threading.Thread(target=self._handle_clients)
            self.client_thread.start()
        except Exception as e:
            print(f"AuthServer: Error starting AuthServer: {e}")

    def stop(self):
        try:
            self.should_stop.set()  # Signal the server to stop
            self.running = False
            self.client_thread.join()
            self.socket.close()
            print("AuthServer: AuthServer stopped.")
        except Exception as e:
            print(f"AuthServer: Error stopping AuthServer: {e}")

    def _handle_clients(self):
        while self.running:
            try:
                self.socket.settimeout(5)  # Set a 5-second timeout for recvfrom
                data, client_address = self.socket.recvfrom(1024)
                data_str = data.decode('utf-8')
                print('AuthServer: recvd: ', data_str)
                method, body = data_str.split('?')

                if method == "signup":
                    response = self._handle_signup(body, client_address)
                elif method == "signin":
                    response = self._handle_signin(body, client_address)
                elif method == 'fetch':
                    response = self._handle_fetch()
                else:
                    response = "Invalid method."

                print('AuthServer: ',response, self.pending_requests)
                self.socket.sendto(response.encode('utf-8'), client_address)
            except socket.timeout:
                # Handle the timeout, you can do something here if needed
                pass
            except Exception as e:
                print(f"AuthServer: Error handling client: {e}")

    def _handle_signup(self, body, ip_address):
        try:
            username, password = body.split('|')
            node_id = random.randint(1000, 9999)  # Generate a random node ID



            # Check if the node_id already exists in pending_requests
            if any(node_id == req_node_id for req_node_id, _ in self.pending_requests):
                return "signup?error"

            # Add the user to the UserDatabase
            if self.user_db.signup(username, password, node_id):
                if (self.user_db.no_of_users()) > 1:
                    self.pending_requests.append((node_id, f'{ip_address[0]}:{ip_address[1]}'))
                    return f"signup?{node_id}"
                else:
                    return f"signup?{node_id}|first"

                
            else:
                return "signup?error"

        except ValueError:
            return "signup?error"
      
    def _handle_signin(self, body, ip_address):
        try:
            username, password = body.split('|')
            node_id = self.user_db.signin(username, password)

            # Check if the user database is empty
            if (self.user_db.no_of_users()) == 0:
                return "signin?error"
            

            # Check if the node_id already exists in pending_requests
            if any(node_id == req_node_id for req_node_id, _ in self.pending_requests):
                return f"signin?{node_id}"

            if node_id is not None:
                if (self.user_db.no_of_users()) > 1:
                    self.pending_requests.append((node_id, f'{ip_address[0]}:{ip_address[1]}'))
                    return f"signin?{node_id}"
                else:
                    return f"signin?{node_id}|first"

            else:
                return "signin?error"

        except ValueError:
            return "signin?error"

    def _handle_fetch(self):
        with self.pending_requests_lock:
            if len(self.pending_requests) > 0:
                node_id, ip_address = self.pending_requests.pop(0)
                return f"fetch?{ip_address}|{node_id}"
            else:
                return "fetch?"
            
