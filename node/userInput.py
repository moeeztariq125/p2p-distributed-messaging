from .node import Node

class UserInput:
    def __init__(self, node_host, node_port, auth_server_host, auth_server_port):
        self.node = Node(node_host, node_port, auth_server_host, auth_server_port)

    def start_node(self):
        self.node.start()

    def stop_node(self):
        self.node.close()

    def signup(self, username, password):
        signup_message = f"signup?{username}|{password}"
        self.node.send_packet(signup_message, self.node.auth_server_host, self.node.auth_server_port)

    def signin(self, username, password):
        signin_message = f"signin?{username}|{password}"
        self.node.send_packet(signin_message, self.node.auth_server_host, self.node.auth_server_port)

    def send_private_message(self, recipient_node_id, text_message):
        self.node.send_message(recipient_node_id,text_message)
    def send_broadcast(self, text_message):
        self.node.send_broadcast(text_message)

    def display_messages(self,nodeid):
        self.node.get_private_messages(nodeid)
    def display_connected_nodes(self):
        print(self.node.connected_nodes)

    def diplay_groupchat_messages(self):
        self.node.get_groupchat_messages()