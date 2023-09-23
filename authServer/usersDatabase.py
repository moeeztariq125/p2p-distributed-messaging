class UserDatabase:
    def __init__(self):
        self.users = {}

    def signup(self, username, password, node_id):
        if username not in self.users:
            self.users[username] = (password, node_id)
            return True
        else:
            return False

    def signin(self, username, password):
        if username in self.users:
            stored_password, node_id = self.users[username]
            if password == stored_password:
                return node_id
        return None
    
    def no_of_users(self):
        return len(self.users)
    
user_db = UserDatabase()











