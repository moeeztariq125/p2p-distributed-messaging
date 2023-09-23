import socket
import threading
import signal
import sys
import time
import random
import json
import functools


class Node:
    def __init__(self, host, port, auth_server_host, auth_server_port):
        self.host = host
        self.port = port
        self.auth_server_host = auth_server_host
        self.auth_server_port = auth_server_port
        self.socket = None
        self._create_socket()
        self.node_id = None  # Initialize node_id to None
        self.receive_thread = None
        self.fetch_thread = None 
        self.running = False
        self.connected_nodes = {}  # Dictionary to store "ipaddress:port" against node ids
        self.group_vector_clock = {}  # Group vector clock dictionary
        self.private_vector_clocks = {}  # Dictionary of private messaging vector clocks
        self.user_messages = {}  # {node_id: [message1, message2, ...]}
        self.group_storage = {}
        self.first=False

    def _create_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))

    def transform_request(self, method, body):
        return f"{method}?{body}"

    def send_packet(self, packet_data, send_host, send_port):
        self.socket.sendto(packet_data.encode('utf-8'), (send_host, int(send_port)))

    def signup(self, username, password):
        method = "signup"
        body = f"{username}|{password}"
        formatted_request = self.transform_request(method, body)
        self.send_packet(formatted_request, self.auth_server_host, self.auth_server_port)

    def signin(self, username, password):
        method = "signin"
        body = f"{username}|{password}"
        formatted_request = self.transform_request(method, body)
        self.send_packet(formatted_request, self.auth_server_host, self.auth_server_port)

    def _receive_messages(self):
        while self.running:
            try:
                self.socket.settimeout(5)  # Set a 5-second timeout for recvfrom
                data, addr = self.socket.recvfrom(1024)
                message = data.decode('utf-8')
                print(f'{self.node_id}: recvd: ',message)
                if message.startswith("signup?") or message.startswith("signin?"):
                    self._handle_auth(message.split('?')[1])
                    # print(f"Received node_id: {self.node_id}")
                elif message.startswith("connect?"):
                    self._update_connected_nodes(message)
                elif message.startswith("message?"):
                    self._handle_message(message)
                elif message.startswith("broadcast?"):
                    self._handle_broadcast(message , addr)
                elif message.startswith("fetch?"):
                    self._handle_fetch(message)
                else:
                    print(f"{self.node_id}: Received: {message} from {addr}")
                    # Here, you can implement further processing of the received message as needed
            except socket.timeout:
                # Handle the timeout, you can do something here if needed
                pass
            except Exception as e:
                print(f"{self.node_id}: Error while receiving: {e}")

    def _handle_auth(self,message):
        if message == 'error':
            return
        split = message.split('|')
        if(len(split)==1):
            self.node_id = split[0]
            return

        if(split[1] == 'first'):
            self.first = True

                
        self.node_id = split[0]

    def _handle_broadcast(self, message, addr):
        if self.node_id not in self.group_vector_clock:
            self.group_vector_clock[self.node_id] = 0
        msg_data = message.split("?")[1].split("|")
        text_id = msg_data[0]
        text = msg_data[1]
        sender_node_id = msg_data[2]
        sender_vector_clock =   json.loads(msg_data[3].replace("'", "\""))
        # Initialize the group vector clock for the sender node if not present
        if sender_node_id not in self.group_vector_clock:
            self.group_vector_clock[sender_node_id] = 0

        if sender_node_id not in self.connected_nodes:
            self.connected_nodes[sender_node_id] = f'{addr[0]}:{addr[1]}'

        # Update the group vector clock for the sender node
        for key,value in sender_vector_clock.items():
            node_id = key
            clock = value
            if node_id == self.node_id:
                self.group_vector_clock[node_id] = max(clock, self.group_vector_clock[node_id]) + 1
            else:
                self.group_vector_clock[node_id] = max(clock, self.group_vector_clock[node_id])
        # Store the broadcast message in group storage
        self.group_storage[text_id] = (text, sender_node_id, self.group_vector_clock.copy())

    def send_broadcast(self, text_message):
        # Get the current node's vector clock from the group vector clock and increment it
        if self.node_id not in self.group_vector_clock:
            self.group_vector_clock[self.node_id] = 0
        self.group_vector_clock[self.node_id] += 1
        print(self.group_vector_clock)
        # Create a unique text_id for the broadcast message
        text_id = random.randint(0, 10000)  # Generate a random node ID


        # Create the broadcast message body with text_id, sender node ID, and clock
        broadcast_body = f"{text_id}|{text_message}|{self.node_id}|{self.group_vector_clock}"

        # Format the message as "broadcast?broadcast_body"
        broadcast_message = f"broadcast?{broadcast_body}"

        # Send the broadcast message to all connected peers
        for node_id, address in self.connected_nodes.items():
            print(f'sent to:{node_id} at {address}, {broadcast_message}')
            ip, port = address.split(":")
            self.send_packet(broadcast_message, ip, int(port))

        # Update the group vector clock for the current node
        self.group_storage[text_id] = (text_message, self.node_id, self.group_vector_clock.copy())
        
    def _update_connected_nodes(self, message):
        node_info = message.split("?")[1]
        nodes_list = node_info.split("|")
        for i in range(0, len(nodes_list), 2):
            node_id = nodes_list[i]
            ip_address = nodes_list[i+1]
            if(self.node_id==node_id):
                continue
            self.connected_nodes[node_id] = f"{ip_address}"
            if(node_id not in self.group_vector_clock):
                self.group_vector_clock[node_id]=0
        print(f"{self.node_id}: Updated connected_nodes: {self.connected_nodes}")
        self.send_broadcast(f'{self.node_id} just joined the chat!')

    def connect(self, send_host, send_port, nodes_list):
        method = "connect"
        body = "|".join(nodes_list)
        formatted_request = self.transform_request(method, body)
        print(f'{self.node_id}: sending connections: {formatted_request}')
        self.send_packet(formatted_request, send_host, send_port)

    def start(self):
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_messages)
        print(f"{self.node_id}: node listening on {self.host}:{self.port}")
        self.fetch_thread = threading.Thread(target=self._fetch_pending_requests)
        self.fetch_thread.start()
        self.receive_thread.start()

    def stop(self):
        self.running = False
        if self.fetch_thread:
            self.fetch_thread.join()
        self.receive_thread.join()
        self.socket.close()

    def _handle_message(self, message):
        msg_data = message.split("?")[1].split("|")
        text = msg_data[0]
        node_id = msg_data[1]
        sender_vector_clock = json.loads(msg_data[2].replace("'","\""))
        # Initialize the private vector clock for the node_id if not present
        if node_id not in self.private_vector_clocks:
            self.private_vector_clocks[node_id] = {self.node_id:0,node_id:0}
        # Apply vector clock rules to update the private vector clock for the sender node
        self.private_vector_clocks[node_id][node_id] = max(sender_vector_clock[node_id],self.private_vector_clocks[node_id][node_id])
        self.private_vector_clocks[node_id][self.node_id] = max(sender_vector_clock[self.node_id],self.private_vector_clocks[node_id][self.node_id])+1
        # Store the message in local storage for the given node_id
        self._store_message(node_id, text, node_id, self.private_vector_clocks[node_id].copy())

    def send_message(self, node_id, text_message):

        # Get the IP address and port of the peer with the given node_id
        if node_id not in self.connected_nodes:
            print(f"{self.node_id}: Error: Node with ID {node_id} is not connected.")
            return
        
        # Get the current node's vector clock and increment it
        if(node_id not in self.private_vector_clocks):
            self.private_vector_clocks[node_id]={node_id:0,self.node_id:0}

        self.private_vector_clocks[node_id][self.node_id]+=1
        

        peer_ip, peer_port = self.connected_nodes[node_id].split(":")

        # Store the message in local storage
        self._store_message(node_id, text_message, self.node_id, self.private_vector_clocks[node_id].copy())

        # Format the message as "message?text|node_id|vector_clock"
        formatted_message = f"message?{text_message}|{self.node_id}|{self.private_vector_clocks[node_id]}"

        # Send the message to the peer's IP address and port
        self.send_packet(formatted_message, peer_ip, int(peer_port))

    def _store_message(self, node_id, text, sender_id, vector_clock):
        # Store the message in the dictionary for the given node_id
        message_data = {
            "text": text,
            "sender_id": sender_id,
            "vector_clock": vector_clock,
        }

        if node_id not in self.user_messages:
            self.user_messages[node_id] = []
        self.user_messages[node_id].append(message_data)
        print(f"{self.node_id}: Stored Message for user {node_id}: {message_data}")

    def signal_handler(self, signal, frame):
        print(f"{self.node_id}: Stopping Node...")
        self.close()
        sys.exit(0)

    def close(self):
        self.stop()
        self.socket.close()

    def _fetch_pending_requests(self):
            print('fetching')
            while self.running:
                # Check if the node has any connected peers
                if (not self.connected_nodes) and (not self.first):
                    print(f"{self.node_id}: Node has no connected peers. Skipping fetch request.")
                else:
                    # Create and send the fetch request to the AuthServer
                    fetch_request = "fetch?"
                    self.send_packet(fetch_request, self.auth_server_host, self.auth_server_port)

                # Wait for 5 seconds before making the next fetch request
                time.sleep(5)

    def _handle_fetch(self,message):
        splitted = message.split('?')
        if(len(splitted[1])==0):
            return
        ip,nodeid = splitted[1].split('|')
        formatted_list = [f"{node_id}|{ip}" for node_id, ip in self.connected_nodes.items()]
        formatted_list.append(f"{self.node_id}|{self.host}:{self.port}")
        result = '|'.join(formatted_list)
        method = 'connect'
        transformed_packet = self.transform_request(method,result)
        print(f'{self.node_id}: sending connections: {transformed_packet}')
        self.send_packet(transformed_packet,ip.split(':')[0],ip.split(':')[1])

    def compare_vector_clocks_private_chat(self,message1, message2):
        for node in message1["vector_clock"]:
            if message1["vector_clock"][node] < message2["vector_clock"][node]:
                return -1
            elif message1["vector_clock"][node] > message2["vector_clock"][node]:
                return 1
        return 0
    
    def compare_vector_clocks_group_chat(self,message1, message2):
        for node in message1[2]:
            if message1[2][node] < message2[2][node]:
                return -1
            elif message1[2][node] > message2[2][node]:
                return 1
        return 0
    
    def get_groupchat_messages(self):
        print(self.group_storage.values())
        sorted_group_chat_messages = (sorted(self.group_storage.values(), key=functools.cmp_to_key(self.compare_vector_clocks_group_chat)))
        sorted_group_chat_messages = [list(t) for t in sorted_group_chat_messages]

        print(f'{self.node_id}-sorted groupchat messages ,{sorted_group_chat_messages}')

    def get_private_messages(self,nodeid):
        if(nodeid not in self.user_messages):
            print(f'{self.node_id}-sorted messages to {nodeid},no messages')
            return
        sorted_chat_messages = (sorted(self.user_messages[nodeid], key=functools.cmp_to_key(self.compare_vector_clocks_private_chat)))
        print(f'{self.node_id}-sorted messages to {nodeid},{sorted_chat_messages}')
