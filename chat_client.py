import socket
import os
import json
import base64
import logging

TARGET_IP = "127.0.0.1"
TARGET_PORT = 8889
REALM_IP_MAPPING = {
    'realm1': {'realm_ip': '172.16.16.101', 'realm_port': 8889},
    'realm2': {'realm_ip': '172.16.16.102', 'realm_port': 8889},
    'realm3': {'realm_ip': '172.16.16.103', 'realm_port': 8889}
}
class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (TARGET_IP, TARGET_PORT)
        self.sock.connect(self.server_address)
        self.tokenid = ""

    def set_server_address(self, realm):
        if realm in REALM_IP_MAPPING:
            self.server_address = (REALM_IP_MAPPING[realm]['realm_ip'], REALM_IP_MAPPING[realm]['realm_port'])
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(self.server_address)
            
    def proses(self, cmdline):
        j = cmdline.split(" ")
        try:
            command = j[0].lower().strip()
            if command == 'auth':
                username = j[1].strip()
                password = j[2].strip()
                return self.login(username, password)
            elif command == 'list_server_data':
                return self.list_server_data()
            elif (command=='set_server'):
                realmname = j[1].strip()
                return self.set_server(realmname)
            elif (command=='add_realm'):
                server_name = j[1].strip()
                server_ip = j[2].strip()
                server_port = j[3].strip()
                return self.add_realm(server_name, server_ip, server_port)
            elif command=='register':
                username=j[1].strip()
                password=j[2].strip()
                negara=j[3].strip()
                nama=j[4:]
                return self.register(username, password, negara, nama)
            elif command == 'logout':
                return self.logout()
            elif (command=='add_group'):
                groupname = j[1].strip()
                return self.add_group(groupname)
            elif (command=='join_group'):
                groupname = j[1].strip()
                return self.join_group(groupname)
            
            elif (command=='leave_group'):
                groupname = j[1].strip()
                return self.leave_group(groupname)
            elif (command=='list_group'):
                groupname = j[1].strip()
                return self.list_group(groupname)
            
            elif (command=='list_my_groups'):
                return self.list_my_groups()
            
            elif (command=='list_users'):
                return self.list_users()
            
            elif (command=='get_group'):
                return self.get_groups()

            elif command == 'send':
                usernameto = j[1].strip()
                message = " ".join(j[2:])
                return self.send_message(usernameto, message)
            elif command == 'send_group':
                usernameto = j[1].strip()
                message = " ".join(j[2:])
                return self.send_group_message(usernameto, message)
            elif command == 'inbox':
                return self.inbox()
            elif command == 'send_file':
                usernameto = j[1].strip()
                filename = j[2].strip()
                if not os.path.exists(filename):
                    return f"Error, file '{filename}' not found"
                with open(filename, 'rb') as fp:
                    filecontent = base64.b64encode(fp.read()).decode()
                return self.send_file(usernameto, filename, filecontent)
            elif command == 'send_group_file':
                usernameto = j[1].strip()
                filename = j[2].strip()
                if not os.path.exists(filename):
                    return f"Error, file '{filename}' not found"
                with open(filename, 'rb') as fp:
                    filecontent = base64.b64encode(fp.read()).decode()
                return self.send_group_file(usernameto, filename, filecontent)
            elif command == 'exit':
                return "Keluar"
            else:
                return "*Maaf, command tidak benar"
        except IndexError:
            return "-Maaf, command tidak benar"
    
    def send_string(self, string):
        try:
            self.sock.sendall(string.encode())
            receivemsg = ""
            while True:
                data = self.sock.recv(65536)
                if data:
                    receivemsg += data.decode()
                    if receivemsg.endswith('\r\n\r\n'):
                        return json.loads(receivemsg)
        except Exception as e:
            self.sock.close()
            return {'status': 'ERROR', 'message': f'Gagal: {str(e)}'}
    
    def add_realm(self, server_name, server_ip, server_port):
        string="add_realm {} {} {} \r\n".format(server_name, server_ip, server_port)
        result = self.send_string(string)
        return "{}".format(result['message'])

    def set_server(self, server_name):
        string="set_server {} \r\n".format(server_name)
        result = self.send_string(string)
        return "{}".format(result['message'])

    def login(self, username, password):
        user = username
        if '@' in username:
            user, realm = username.split('@')
            self.set_server_address(realm)
        string = f"auth {user} {password} \r\n"
        result = self.send_string(string)
        if result['status'] == 'OK':
            self.tokenid = result['tokenid']
            return f"username {user} logged in, token {self.tokenid}"
        else:
            return f"Error, {result['message']}"
    
    def logout(self):
        if self.tokenid == "":
            return "Error, not authorized"
        string = f"logout {self.tokenid} \r\n"
        result = self.send_string(string)
        if result['status'] == 'OK':
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_address = (TARGET_IP, TARGET_PORT)
            self.sock.connect(self.server_address)
            self.tokenid = ""
            return f"user logged out"
        else:
            return f"Error, {result['message']}"
    
    def register(self,username,password, negara, nama):
        nama=' '.join(str(e) for e in nama)
        string="register {} {} {} {}\r\n" . format(username,password, negara, nama)
        result = self.send_string(string)
        if result['status']=='OK':
            self.tokenid=result['tokenid']
            return "username {} register in, token {} " .format(username,self.tokenid)
        else:
            return "Error, {}" . format(result['message'])
        
    def add_group(self, groupname):
        if self.tokenid == "":
            return "Error, not authorized"
        string="add_group {} {} \r\n".format(self.tokenid, groupname)
        result = self.send_string(string)
        return "{}".format(result['message'])
    
    def join_group(self, groupname):
        if self.tokenid == "":
            return "Error, not authorized"
        string="join_group {} {} \r\n".format(self.tokenid, groupname)
        result = self.send_string(string)
        return "{}".format(result['message'])
    
    def leave_group(self, groupname):
        if self.tokenid == "":
            return "Error, not authorized"
        string="leave_group {} {} \r\n".format(self.tokenid, groupname)
        result = self.send_string(string)
        return "{}".format(result['message'])
    
    def list_users(self):
        if self.tokenid == "":
            return "Error, not authorized"
        string="list_users\r\n"
        result = self.send_string(string)
        return "{}".format(result['users'])
    
    def list_my_groups(self):
        if self.tokenid == "":
            return "Error, not authorized"
        string="list_my_groups {}\r\n".format(self.tokenid)
        result = self.send_string(string)
        return "{}".format(result['groups'])

    def list_group(self, groupname):
        if self.tokenid == "":
            return "Error, not authorized"
        string="list_group {} {} \r\n".format(self.tokenid, groupname)
        result = self.send_string(string)
        return "{}".format(result['message'])
    
    def get_groups(self):
        string = "get_group\r\n"
        result = self.send_string(string)
        logging.info(f"Response from send_string: {result}")
        if not result:
            logging.warning("get_groups received an empty response.")
            return {
			'messi': { 'nama': 'Lionel Messi', 'negara': 'Argentina', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm1'},
			'henderson': { 'nama': 'Jordan Henderson', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm2'},
			'lineker': { 'nama': 'Gary Lineker', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm3'},
			'ilham1': { 'nama': 'Ilham Satu', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm1'},
			'ilham2': { 'nama': 'Ilham Dua', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm2'},
			'ilham3': { 'nama': 'Ilham Tiga', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm3'}
		}
        if isinstance(result, str):
            try:
                result_dict = json.loads(result)  
                return result_dict
            except json.JSONDecodeError as e:
                logging.warning(f"JSON decoding failed: {e}")
                return {
			'messi': { 'nama': 'Lionel Messi', 'negara': 'Argentina', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm1'},
			'henderson': { 'nama': 'Jordan Henderson', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm2'},
			'lineker': { 'nama': 'Gary Lineker', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm3'},
			'ilham1': { 'nama': 'Ilham Satu', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm1'},
			'ilham2': { 'nama': 'Ilham Dua', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm2'},
			'ilham3': { 'nama': 'Ilham Tiga', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm3'}
		}
        elif isinstance(result, dict):
            return result  
        
        logging.warning("Unexpected result type")
        return {
			'messi': { 'nama': 'Lionel Messi', 'negara': 'Argentina', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm1'},
			'henderson': { 'nama': 'Jordan Henderson', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm2'},
			'lineker': { 'nama': 'Gary Lineker', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm3'},
			'ilham1': { 'nama': 'Ilham Satu', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm1'},
			'ilham2': { 'nama': 'Ilham Dua', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm2'},
			'ilham3': { 'nama': 'Ilham Tiga', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm3'}
		}
    
        
    # def get_groups(self):
    #     string = "get_group\r\n"
    #     result = self.send_string(string)
        
    #     logging.info(f"Response from send_string: {result}")
        
    #     if not result:
    #         logging.warning("get_groups received an empty response.")
    #         return {}
        
    #     try:
    #         result_dict = json.loads(result)  # Deserialize the JSON string
    #         return result_dict
    #     except json.JSONDecodeError as e:
    #         logging.warning(f"JSON decoding failed: {e}")
    #         return {}  # Return an empty dictionary or handle as appropriate

    def list_server_data(self):
        string="list_server_data \r\n"
        result = self.send_string(string)
        return "{}".format(result)


    def send_message(self, usernameto="xxx", message="xxx"):
        if self.tokenid == "":
            return "Error, not authorized"
        string = f"send {self.tokenid} {usernameto} {message} \r\n"
        result = self.send_string(string)
        if result['status'] == 'OK':
            return f"message sent to {usernameto}"
        else:
            return f"Error, {result['message']}"
    
    def send_group_message(self, usernameto="xxx", message="xxx"):
        if self.tokenid == "":
            return "Error, not authorized"
        string = f"send_group {self.tokenid} {usernameto} {message} \r\n"
        result = self.send_string(string)
        if result['status'] == 'OK':
            return f"message sent to {usernameto}"
        else:
            return f"Error, {result['message']}"
    
    def inbox(self):
        if self.tokenid == "":
            return "Error, not authorized"
        string = f"inbox {self.tokenid} \r\n"
        result = self.send_string(string)
        if result['status'] == 'OK':
            return json.dumps(result['messages'], indent=4)
        else:
            return f"Error, {result['message']}"
    
    def send_file(self, usernameto, filename, filecontent):
        if self.tokenid == "":
            return "Error, not authorized"
        string = f"send_file {self.tokenid} {usernameto} {filename} {filecontent} \r\n"
        result = self.send_string(string)
        if result['status'] == 'OK':
            return f"file {filename} sent to {usernameto}"
        else:
            return f"Error, {result['message']}"
        
    def send_group_file(self, usernameto, filename, filecontent):
        if self.tokenid == "":
            return "Error, not authorized"
        string = f"send_group_file {self.tokenid} {usernameto} {filename} {filecontent} \r\n"
        result = self.send_string(string)
        if result['status'] == 'OK':
            return f"file {filename} sent to {usernameto}"
        else:
            return f"Error, {result['message']}"

if __name__ == "__main__":
    cc = ChatClient()
    print("""\
    Command List
        register <username> <password> <negara> <nama>
            - Register a new user with the specified username, password, country, and name.
        auth <username> <password>
            - Log in with the specified username and password within the default realm.
        auth <username>@<user's realm> <password>
            - Log in with the specified username and password within the specified realm.
        inbox
            - Show the inbox of received messages.
        logout
            - Log out.

        send <receiver's username> <message>
            - Send a message to a user within the same realm.
        send <receiver's username>@<receiver's realm> <message>
            - Send a message to a user in a different realm.

        add_group <group's name>
            - Add a new group chat.
        join_group <group's name>
            - Join an existing group chat.
        leave_group <group's name>
            - Leave an existing group chat.
        list_group <group's name>
            - List members of a group chat.
        send_group <group's name> <message>
            - Send a message to a group chat.

        send_file <receiver's username> <filename>
            - Send a file to a user within the same realm.
        send_file <receiver's username>@<receiver's realm> <filename>
            - Send a file to a user in a different realm.
        send_group_file <group's name> <filename>
            - Send a file to a group chat.

        add_realm <server_name> <server_ip> <server_port>
            - Add a new realm server.
        set_server <server_name>
            - Set the current server to the specified realm.

        list_server_data
            - List data from the server.
        exit
            - Quits the program.

    """)

    while True:
        cmdline = input(f"Command {cc.tokenid}: ")
        response = cc.proses(cmdline)
        print(response)
        if response == "Keluar":
            break
