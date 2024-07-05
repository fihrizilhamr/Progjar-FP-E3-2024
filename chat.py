import sys
import os
import json
import uuid
import logging
import fcntl
import struct
import socket
import threading
import base64
from queue import Queue

class Chat:
	def __init__(self):
		self.sessions = {}
		self.users = {
			'messi': { 'nama': 'Lionel Messi', 'negara': 'Argentina', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm1'},
			'henderson': { 'nama': 'Jordan Henderson', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm2'},
			'lineker': { 'nama': 'Gary Lineker', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm3'},
			'ilham1': { 'nama': 'Ilham Satu', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm1'},
			'ilham2': { 'nama': 'Ilham Dua', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm2'},
			'ilham3': { 'nama': 'Ilham Tiga', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm3'}
		}
		self.realms = {
			'realm1': {'realm_ip': '172.16.16.101', 'realm_port': 8889},
			'realm2': {'realm_ip': '172.16.16.102', 'realm_port': 8889},
			# 'realm3': {'realm_ip': '172.16.16.103', 'realm_port': 8889}
		}
		self.groups = {
			'Grup_Satu': {'members': ['messi@realm1', 'henderson@realm2', 'lineker@realm3']},
			'Informatika': {'members': ['ilham1@realm1', 'ilham2@realm2', 'ilham3@realm3']}
		}
		self.current_realm = self.get_realm_by_ip()

	def get_eth1_ip(self):
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			ip_address = socket.inet_ntoa(fcntl.ioctl(
				s.fileno(),
				0x8915,  
				struct.pack('256s', b'eth1'[:15])
			)[20:24])
			
			for realm, info in self.realms.items():
				if info['realm_ip'] == ip_address:
					return realm
			
			return None 

		except IOError:
			return None
		
	def get_realm_by_ip(self):
		try:
			interfaces = os.listdir('/sys/class/net/')
			for interface in interfaces:
				if interface.startswith('eth'):
					s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
					try:
						ip_address = socket.inet_ntoa(fcntl.ioctl(
							s.fileno(),
							0x8915,
							struct.pack('256s', bytes(interface[:15], 'utf-8'))
						)[20:24])
					except IOError:
						continue 
					
					for realm, info in self.realms.items():
						if info['realm_ip'] == ip_address:
							return realm
			
			return None 

		except IOError:
			return None
		
	def _enqueue_message(self, outqueue_sender, inqueue_receiver, user, message):
		if user not in outqueue_sender:
			outqueue_sender[user] = Queue()
		outqueue_sender[user].put(message)

		if user not in inqueue_receiver:
			inqueue_receiver[user] = Queue()
		inqueue_receiver[user].put(message)

	def _parse_realm(self, username):
		if '@' in username:
			user, realm = username.split('@')
			return user, realm
		return username, self.current_realm

	def _safe_json_dumps(self, obj):
		try:
			return json.dumps(obj)
		except TypeError:
			logging.warning(f"Object of type {type(obj).__name__} is not JSON serializable")
			return json.dumps(str(obj)) 
		
	def proses(self, data):
		j = data.split(" ")
		logging.warning({data})
		try:
			command = j[0].strip()
			if command == 'auth':
				username = j[1].strip()
				password = j[2].strip()
				logging.warning("AUTH: auth {} {}".format(username, password))
				return self.autentikasi_user(username, password)
			elif command == 'list_server_data':
				users_str = self._safe_json_dumps(self.users)
				servers_str = self._safe_json_dumps(self.realms)
				groups_str = self._safe_json_dumps(self.groups)
				realm_str = self._safe_json_dumps(self.current_realm)
				logging.warning("LIST: server data: users={}, servers={}, groups={}, current realm={}".format(users_str, servers_str, groups_str, realm_str))
				return users_str, servers_str, groups_str, realm_str
			elif command == 'set_server':
				realm_str = j[1].strip()
				self.current_realm = self.get_realm_by_ip()
				if (self.current_realm is None):
					self.current_realm = realm_str
				logging.warning("SET: realm become {}".format(self.current_realm))
				return self._safe_json_dumps(self.current_realm)

			elif command == 'list_users':
				list_users = []
				for user_name, user_info in self.users.items():
					list_users.append(user_name+"@"+user_info['realm'])
				logging.warning("LISTUSERS: server data: users={}".format(list_users))
				return {'status': 'OK', 'users': list_users}
			
			elif command == 'list_my_groups':
				sessionid = j[1].strip()
				usernamefrom = self.sessions[sessionid]['username']
				user_test = usernamefrom + "@" + self.get_user(usernamefrom)['realm']
				
				my_groups = []
				
				for group_name, group_info in self.groups.items():
					if user_test in group_info['members']:
						my_groups.append(group_name)
				logging.warning("LISTMYGROUPS: server data: users={} groups={}".format(user_test, my_groups))
				return {'status': 'OK', 'groups': my_groups}

			
			elif (command=='add_realm'):
				server_name = j[1].strip()
				server_ip = j[2].strip()
				server_port = j[3].strip()
				logging.warning("ADDREALM: added realm {}" . format(server_name))
				return self.add_realm(server_name, server_ip, server_port)
			elif (command=='add_realm_to_another_realm'):
				server_name = j[1].strip()
				server_ip = j[2].strip()
				server_port = j[3].strip()
				logging.warning("ADDREALM INTERREALM: added realm {}" . format(server_name))
				return self.add_realm_to_another_realm(server_name, server_ip, server_port)
			
			elif command == 'logout':
				sessionid = j[1].strip()
				logging.warning("LOGOUT: {}".format(sessionid))
				return self.logout(sessionid)
			elif command=='register':
				username=j[1].strip()
				password=j[2].strip()
				negara=j[3].strip()
				nama = ' '.join(j[4:]).strip()
				logging.warning("REGISTER: register {} {}" . format(username,password))
				return self.register_user(username,password, negara, nama)
			elif command=='register_to_another_realm':
				username=j[1].strip()
				password=j[2].strip()
				negara=j[3].strip()
				user_realm = j[4].strip()
				nama = ' '.join(j[5:]).strip()
				logging.warning("REGISTER INTERREALM: register {} {}" . format(username,password))
				return self.register_user_to_another_realm(username,password, negara, user_realm, nama)
			elif (command=='add_group'):
				sessionid = j[1].strip()
				groupname = j[2].strip()
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("ADDGROUP: session {} added group {}" . format(sessionid, groupname))
				return self.addgroup(sessionid,usernamefrom,groupname)
			elif (command=='add_group_to_another_realm'):
				usernamefrom = j[1].strip()
				groupname = j[2].strip()
				logging.warning("ADDGROUP INTERREALM: added group {}" . format(groupname))
				return self.add_group_to_another_realm(usernamefrom,groupname)
			elif (command == 'join_group'):
				sessionid = j[1].strip()
				groupname = j[2].strip()
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("JOINGROUP: user {} joined group {}" . format(usernamefrom,groupname))
				return self.joingroup(sessionid, usernamefrom, groupname)
			elif (command == 'join_group_to_another_realm'):
				usernamefrom = j[1].strip()
				groupname = j[2].strip()
				logging.warning("JOINGROUP INTERREALM: user {} joined group {}" . format(usernamefrom,groupname))
				return self.joingroup_to_another_realm(usernamefrom, groupname)
			
			elif (command == 'leave_group'):
				sessionid = j[1].strip()
				groupname = j[2].strip()
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("LEAVEGROUP: user {} left group {}" . format(usernamefrom,groupname))
				return self.leavegroup(sessionid, usernamefrom, groupname)
			elif (command == 'leave_group_to_another_realm'):
				usernamefrom = j[1].strip()
				groupname = j[2].strip()
				logging.warning("LEAVEGROUP INTERREALM: user {} left group {}" . format(usernamefrom,groupname))
				return self.leavegroup_to_another_realm(usernamefrom, groupname)

			elif (command=='list_group'):
				sessionid = j[1].strip()
				groupname = j[2].strip()
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("LISTGROUP: user {} list group {}" . format(usernamefrom,groupname))
				return self.list_group_user(usernamefrom, groupname)
			
			elif (command=='get_group'):
				# sessionid = j[1].strip()
				# usernamefrom = self.sessions[sessionid]['username']
				# logging.warning("GETGROUP: get group")
				# username_from = usernamefrom + "@" + self.get_user(usernamefrom)['realm']
				# matched_groups = {}
				# for group_name, group_info in self.groups.items():
				# 	if username_from in group_info['members']:
				# 		matched_groups[group_name] = group_info
				# return self._safe_json_dumps(matched_groups)
				users_str = self._safe_json_dumps(self.users)
				return users_str

			elif command == 'send':
				sessionid = j[1].strip()
				usernameto = j[2].strip()
				message = " ".join(j[3:])
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("SEND: session {} send message from {} to {}".format(sessionid, usernamefrom, usernameto))
				return self.send_message(sessionid, usernamefrom, usernameto, message)
			elif command == 'send_group':
				sessionid = j[1].strip()
				usernameto = j[2].strip()
				message = " ".join(j[3:])
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("SEND_GROUP: session {} send message from {} to {}".format(sessionid, usernamefrom, usernameto))
				return self.send_group_message(sessionid, usernamefrom, usernameto, usernameto,message)
			elif command == 'send_to_another_realm':
				usernamefrom = j[1].strip()
				usernameto = j[2].strip()
				group_destination = j[3].strip() if len(j) >= 5 else ''
				message = " ".join(j[4:])
				logging.warning("SEND INTERREALM: send message from {} to {} in {}".format(usernamefrom, usernameto, group_destination))
				return self.sent_message_from_other_realm(usernamefrom, usernameto, group_destination, message)
			elif command == 'inbox':
				sessionid = j[1].strip()
				username = self.sessions[sessionid]['username']
				logging.warning("INBOX: {}".format(sessionid))
				return self.get_inbox(username)
			elif command == 'send_file':
				sessionid = j[1].strip()
				usernameto = j[2].strip()
				filename = j[3].strip()
				filecontent = " ".join(j[4:])
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("SEND_FILE: session {} send file from {} to {}".format(sessionid, usernamefrom, usernameto))
				return self.send_file(sessionid, usernamefrom, usernameto, filename, filecontent)
			elif command == 'send_group_file':
				sessionid = j[1].strip()
				usernameto = j[2].strip()
				filename = j[3].strip()
				filecontent = " ".join(j[4:])
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("SEND_GROUP_FILE: session {} send file from {} to {}".format(sessionid, usernamefrom, usernameto))
				return self.send_group_file(sessionid, usernamefrom, usernameto, usernameto,filename, filecontent)
			elif command == 'send_file_to_another_realm':
				usernamefrom = j[1].strip()
				usernameto = j[2].strip()
				group_destination = j[3].strip() if len(j) >= 5 else ''
				filename = j[4].strip()
				filecontent = " ".join(j[5:])
				logging.warning("SEND FILE INTERREALM: send file from {} to {} in {}".format(usernamefrom, usernameto, group_destination))
				return self.sent_file_from_other_realm(usernamefrom, usernameto, group_destination, filename, filecontent)
			else:
				return {'status': 'ERROR', 'message': '**Protocol Tidak Benar'}
		except KeyError as e:
			logging.error(f"KeyError: {str(e)}")
			return {'status': 'ERROR', 'message': 'Informasi tidak ditemukan'}
		except IndexError as e:
			logging.error(f"IndexError: {str(e)}")
			return {'status': 'ERROR', 'message': '--Protocol Tidak Benar'}


	def add_realm(self, server_name, server_ip, server_port):
		if server_name in self.realms:
			return {'status': 'ERROR', 'message': 'Realm Sudah Ada'}
		
		self.realms[server_name] = {
			'realm_ip': server_ip, 
			'realm_port': int(server_port)
		}
		for server_name, self_realm in self.realms.items():
			server_ip = self_realm['realm_ip']
			server_port = self_realm['realm_port']
			message = f"add_realm_to_another_realm {server_name} {server_ip} {server_port} {self.current_realm}\r\n"
			# threads = []
			for realm in self.realms:
				if realm != self.current_realm:
					TARGET_IP = self.realms.get(realm)['realm_ip']
					TARGET_PORT = self.realms.get(realm)['realm_port']
					t = threading.Thread(target=self.handle_connection, args=(message, TARGET_IP, TARGET_PORT))
					# threads.append(t)
					t.start()
			
			# for thread in threads:
			# 	thread.join()

		return {'status': 'OK', 'message': 'Realm berhasil ditambahkan'}
		

	def add_realm_to_another_realm(self, server_name, server_ip, server_port):
		if server_name in self.realms:
			return {'status': 'ERROR', 'message': 'Realm Sudah Ada'}
		
		self.realms[server_name] = {
			'realm_ip': server_ip, 
			'realm_port': int(server_port)
		}
		self.current_realm = self.get_realm_by_ip()

		return {'status': 'OK', 'message': 'Realm berhasil ditambahkan'}

	def autentikasi_user(self, username, password):
		username, dest_realm = self._parse_realm(username)
		if username not in self.users:
			return {'status': 'ERROR', 'message': 'User Tidak Ada'}
		if self.users[username]['password'] != password:
			return {'status': 'ERROR', 'message': 'Password Salah'}
		if (dest_realm != '' and dest_realm !=  self.current_realm):
			return {'status': 'ERROR', 'message': 'User tidak berada di realm yang benar'}
		if self.users[username]['realm'] != self.current_realm:
			return {'status': 'ERROR', 'message': 'User tidak berada di realm yang benar'}
		tokenid = str(uuid.uuid4())
		self.sessions[tokenid] = {'username': username, 'userdetail': self.users[username]}
		return {'status': 'OK', 'tokenid': tokenid}
		
	def logout(self, sessionid):
		if sessionid in self.sessions:
			del self.sessions[sessionid]
			return {'status': 'OK', 'message': 'Logout successful'}
		else:
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		
	def register_user(self, username, password, negara, nama):
		if username in self.users:
			return {'status': 'ERROR', 'message': 'User Sudah Ada'}
		
		self.users[username] = { 
			'nama': nama,
			'negara': negara,
			'password': password,
			'incoming': {},
			'outgoing': {},
			'realm': self.current_realm
		}
		
		for username, self_user in self.users.items():
			password = self_user['password']
			negara = self_user['negara']
			nama = self_user['nama']
			message = f"register_to_another_realm {username} {password} {negara} {self.current_realm} {nama}\r\n"
			# threads = []
			for realm in self.realms:
				if realm != self.current_realm:
					TARGET_IP = self.realms.get(realm)['realm_ip']
					TARGET_PORT = self.realms.get(realm)['realm_port']
					t = threading.Thread(target=self.handle_connection, args=(message, TARGET_IP, TARGET_PORT))
					# threads.append(t)
					t.start()
			# for thread in threads:
			# 	thread.join()
		tokenid = str(uuid.uuid4()) 
		self.sessions[tokenid] = {'username': username, 'userdetail': self.users[username]}
		return {'status': 'OK', 'tokenid': tokenid}

	
	def register_user_to_another_realm(self,username, password, negara, user_realm, nama):
		if (username in self.users):
			return { 'status': 'ERROR', 'message': 'User Sudah Ada' }
		self.users[username]={ 
			'nama': nama,
			'negara': negara,
			'password': password,
			'incoming': {},
			'outgoing': {},
			'realm': user_realm
			}
		return { 'status': 'OK', 'message':  'User berhasil ditambahkan'}
	
	def addgroup(self, sessionid, usernamefrom, groupname):
		if sessionid not in self.sessions:
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		
		usernamefrom = usernamefrom + "@" + self.current_realm
		message = f"add_group_to_another_realm {usernamefrom} {groupname}\r\n"
		
		
		if groupname not in self.groups:
			self.groups[groupname] = {
				'members': [usernamefrom],
			}
			# threads = []
			for realm in self.realms:
				if realm != self.current_realm:
					TARGET_IP = self.realms.get(realm)['realm_ip']
					TARGET_PORT = self.realms.get(realm)['realm_port']
					t = threading.Thread(target=self.handle_connection, args=(message, TARGET_IP, TARGET_PORT))
					# threads.append(t)
					t.start()
			# for thread in threads:
			# 	thread.join()
			return {'status': 'OK', 'message': 'Add group successful'}
		else:
			return {'status': 'ERROR', 'message': 'Group tidak ditemukan!'}

		
	def add_group_to_another_realm(self, usernamefrom, groupname):
		if groupname not in self.groups:
			self.groups[groupname]={
				'members': [usernamefrom],
			}
			return {'status': 'OK', 'message': 'Add group successful'}
		else:
			return {'status': 'ERROR', 'message': 'Group tidak ditemukan!'}
    
	def joingroup(self, sessionid, usernamefrom, groupname):
		if sessionid not in self.sessions:
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		if usernamefrom in self.groups[groupname]['members']:
			return {'status': 'ERROR', 'message': 'User sudah dalam group'}
		
		usernamefrom = usernamefrom + "@" + self.current_realm
		if usernamefrom not in self.groups[groupname]['members']:
			self.groups[groupname]['members'].append(usernamefrom)

		
		for groupname, self_group in self.groups.items():
			for self_member in self_group['members']:
				message = f"join_group_to_another_realm {self_member} {groupname}\r\n"
				# threads = []
				for realm in self.realms:
					if realm != self.current_realm:
						TARGET_IP = self.realms.get(realm)['realm_ip']
						TARGET_PORT = self.realms.get(realm)['realm_port']
						t = threading.Thread(target=self.handle_connection, args=(message, TARGET_IP, TARGET_PORT))
						# threads.append(t)
						t.start()
				# for thread in threads:
				# 	thread.join()
		return {'status': 'OK', 'message': 'Berhasil join grup'}

	
	def joingroup_to_another_realm(self, usernamefrom, groupname):
		if usernamefrom in self.groups[groupname]['members']:
			return {'status': 'ERROR', 'message': 'User sudah dalam group'}
		if usernamefrom not in self.groups[groupname]['members']:
			self.groups[groupname]['members'].append(usernamefrom)
		return {'status': 'OK', 'message': 'Berhasil join grup'}
	
	def leavegroup(self, sessionid, usernamefrom, groupname):
		if sessionid not in self.sessions:
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
			
		usernamefrom = usernamefrom + "@" + self.current_realm
		if usernamefrom in self.groups[groupname]['members']:
			self.groups[groupname]['members'].remove(usernamefrom)
		
		for groupname, self_group in self.groups.items():
			for self_member in self_group['members']:
				message = f"leave_group_to_another_realm {self_member} {groupname}\r\n"
				
				# threads = []
				for realm in self.realms:
					if realm != self.current_realm:
						TARGET_IP = self.realms.get(realm)['realm_ip']
						TARGET_PORT = self.realms.get(realm)['realm_port']
						t = threading.Thread(target=self.handle_connection, args=(message, TARGET_IP, TARGET_PORT))
						# threads.append(t)
						t.start()
				# for thread in threads:
				# 	thread.join()
		return {'status': 'OK', 'message': 'Berhasil leave dari grup'}

	
	def leavegroup_to_another_realm(self, usernamefrom, groupname):
		if usernamefrom not in self.groups[groupname]['members']:
			return {'status': 'ERROR', 'message': 'User sudah tidak ada di dalam group'}
		if usernamefrom in self.groups[groupname]['members']:
			self.groups[groupname]['members'].remove(usernamefrom)
		return {'status': 'OK', 'message': 'Berhasil leave dari grup'}

	def list_group_user(self,usernamefrom, group_name):
		if (group_name not in self.groups):
			return {'status':'ERROR', 'message':'Group tidak ditemukan'}
		usernamefrom = usernamefrom + "@" + self.current_realm
		if usernamefrom not in self.groups[group_name]['members']:
			return {'status':'ERROR', 'message':'Bukan anggota grup'}

		return {'status':'OK', 'message':self.groups[group_name]['members']}

	def get_user(self, username):
		if username not in self.users:
			return False
		return self.users[username]

	def handle_connection(self, command, TARGET_IP, TARGET_PORT):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_address = (TARGET_IP, TARGET_PORT)
		
		try:
			sock.connect(server_address)
			sock.sendall(command.encode())

			receivemsg = ""
			while True:
				data = sock.recv(65536)
				if data:
					receivemsg += data.decode()
					if receivemsg.endswith('\r\n\r\n'):
						print("Received full response:", receivemsg)
						return json.loads(receivemsg)
				else:
					break

		except socket.error as e:
			print(f"Socket error: {e}")
			return {'status': 'ERROR', 'message': 'Socket error'}

		except Exception as e:
			print(f"Error: {e}")
			return {'status': 'ERROR', 'message': 'Failed to send message'}

		finally:
			sock.close()

		return {'status': 'ERROR', 'message': 'Unknown error'}

	def send_message_or_file(self, username_from, username_dest, dest_realm, group_destination = '', message=None, filename=None, filecontent=None):
		TARGET_IP = self.realms.get(dest_realm)['realm_ip']
		TARGET_PORT = self.realms.get(dest_realm)['realm_port']

		if not TARGET_IP:
			return {'status': 'ERROR', 'message': 'Invalid destination realm'}

		if message is not None:
			command = f"send_to_another_realm {username_from} {username_dest} {group_destination} {message}\r\n"
		elif filename is not None and filecontent is not None:
			command = f"send_file_to_another_realm {username_from} {username_dest} {group_destination} {filename} {filecontent}\r\n"
		else:
			return {'status': 'ERROR', 'message': 'Invalid parameters'}

		thread = threading.Thread(target=self.handle_connection, args=(command, TARGET_IP, TARGET_PORT))
		thread.start()
		# thread.join()

		return {'status': 'OK', 'message': 'Message sent'} if message is not None else {'status': 'OK', 'message': 'File sent'}

	def send_message(self, sessionid, username_from, username_destination, message):
		if sessionid not in self.sessions:
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		if username_destination in self.groups:
			return self.send_group_message(sessionid, username_from, username_destination, username_destination, message)
		username_dest, dest_realm = self._parse_realm(username_destination)
		s_to = self.get_user(username_dest)
		s_fr = self.get_user(username_from)
		if not s_fr or not s_to:
			return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
		if dest_realm != s_to['realm']:
			return {"status": "ERROR", "message": "User tujuan tidak berada di realm yang benar"}
		if dest_realm != self.current_realm:
			return self.send_message_or_file(username_from, username_dest, dest_realm, message=message)
		msg = {'msg_from': s_fr['nama'], 'realm_from': s_fr['realm'], 'msg_to': s_to['nama'], 'realm_to': s_to['realm'], 'msg': message}
		return self.message_sending_process(msg, s_fr, s_to, username_dest)
			
	def send_group_message(self, sessionid, username_from, username_destination,group_destination, message):
		if sessionid not in self.sessions:
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}

		if username_destination in self.groups:
			user_test = username_from + "@" + self.get_user(username_from)['realm']
			if user_test not in self.groups[username_destination]['members']:
				logging.warning("User {} is not a member of group {} of {}".format(user_test, username_destination, self.groups[username_destination]))
				return {'status': 'ERROR', 'message': 'Bukan member'}
			# threads = []
			for member in self.groups[username_destination]['members']:
				if member != user_test:
					thread = threading.Thread(target=self.send_group_message, args=(sessionid, username_from, member, group_destination, message))
					# threads.append(thread)
					thread.start()
			# for thread in threads:
			# 	thread.join()
			return {'status': 'OK', 'message': 'Group message sent'}

		username_dest, dest_realm = self._parse_realm(username_destination)
		s_fr = self.get_user(username_from)
		s_to = self.get_user(username_dest)
		if not s_fr or not s_to:
			return {'status': 'ERROR', 'message': 'Group Tidak Ditemukan'}
		if dest_realm != s_to['realm']:
			return {"status": "ERROR", "message": "User tujuan tidak berada di realm yang benar"}
		if dest_realm != self.current_realm:
			return self.send_message_or_file(username_from, username_dest, dest_realm,group_destination=group_destination, message=message)
		msg = {'msg_from': s_fr['nama'], 'realm_from': s_fr['realm'], 'msg_to': s_to['nama'], 'realm_to': s_to['realm'], 'group': group_destination,'msg': message}
		return self.message_sending_process(msg, s_fr, s_to, username_dest)
		
	def sent_message_from_other_realm(self, username_from, username_dest,group_destination, message):
		username_dest, dest_realm = self._parse_realm(username_dest)
		s_fr = self.get_user(username_from)
		s_to = self.get_user(username_dest)
		if not s_fr or not s_to:
			return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
		
		if group_destination != '':
			msg = {'msg_from': s_fr['nama'], 'realm_from': s_fr['realm'], 'msg_to': s_to['nama'], 'realm_to': s_to['realm'], 'group': group_destination,'msg': message}
		else :
			msg = {'msg_from': s_fr['nama'], 'realm_from': s_fr['realm'], 'msg_to': s_to['nama'], 'realm_to': s_to['realm'], 'msg': message}
		return self.message_sending_process(msg, s_fr, s_to, username_dest)
				
	def message_sending_process(self, msg, s_fr, s_to, username_dest):
		outqueue_sender = s_fr['outgoing']
		inqueue_receiver = s_to['incoming']
		self._enqueue_message(outqueue_sender, inqueue_receiver, username_dest, msg)
		return {'status': 'OK', 'message': 'Message Sent'}

	def get_inbox(self, username):
		s_fr = self.get_user(username)
		incoming = s_fr['incoming']
		msgs = {user: [] for user in incoming}
		for user in incoming:
			while not incoming[user].empty():
				message = incoming[user].get_nowait()
				if isinstance(message, dict):
					for key in message:
						if isinstance(message[key], bytes):
							try:
								if key == 'filecontent':
									message[key] = base64.b64encode(message[key]).decode()
								else:
									message[key] = message[key].decode('utf-8')
							except UnicodeDecodeError:
								# message[key] = message[key].decode('utf-8', errors='replace')
								pass
				msgs[user].append(message)
		return {'status': 'OK', 'messages': msgs}
	# def get_inbox(self, username):
	# 	s_fr = self.get_user(username)
	# 	incoming = s_fr['incoming']
	# 	msgs = {user: [] for user in incoming}
	# 	for user in incoming:
	# 		while not incoming[user].empty():
	# 			message = incoming[user].get_nowait()
	# 			msgs[user].append(message)
	# 	return {'status': 'OK', 'messages': msgs}


	def send_file(self, sessionid, username_from, username_destination, filename, filecontent):
		if sessionid not in self.sessions:
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		if username_destination in self.groups:
			return self.send_group_file(sessionid, username_from, username_destination, username_destination, filename, filecontent)
		username_dest, dest_realm = self._parse_realm(username_destination)
		s_fr = self.get_user(username_from)
		s_to = self.get_user(username_dest)
		if not s_fr or not s_to:
			return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
		if dest_realm != s_to['realm']:
			return {"status": "ERROR", "message": "User tujuan tidak berada di realm yang benar"}
		if dest_realm != self.current_realm:
			return self.send_message_or_file(username_from, username_dest, dest_realm, filename = filename, filecontent = filecontent)
		filecontent = base64.b64decode(filecontent)
		file_msg = {'msg_from': s_fr['nama'], 'realm_from': s_fr['realm'], 'msg_to': s_to['nama'], 'realm_to': s_to['realm'], 'filename': filename, 'filecontent': filecontent}
		return self.file_sending_process(file_msg, s_fr, s_to, username_dest, filename, filecontent)
		
	def send_group_file(self, sessionid, username_from, username_destination, group_destination, filename, filecontent):
		if sessionid not in self.sessions:
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		if username_destination in self.groups:
			user_test = username_from + "@" + self.get_user(username_from)['realm']
			if user_test not in self.groups[username_destination]['members']:
				logging.warning("User {} is not a member of group {} of {}".format(user_test, username_destination, self.groups[username_destination]))
				return {'status': 'ERROR', 'message': 'Bukan member'}
			# threads = []
			for member in self.groups[username_destination]['members']:
				if member != user_test:
					thread = threading.Thread(target=self.send_group_file, args=(sessionid, username_from, member, group_destination, filename, filecontent))
					# threads.append(thread)
					thread.start()
			# for thread in threads:
			# 	thread.join()
			return {'status': 'OK', 'message': 'Group file sent'}
		username_dest, dest_realm = self._parse_realm(username_destination)
		s_fr = self.get_user(username_from)
		s_to = self.get_user(username_dest)
		if not s_fr or not s_to:
			return {'status': 'ERROR', 'message': 'Group Tidak Ditemukan'}
		if dest_realm != s_to['realm']:
			return {"status": "ERROR", "message": "User tujuan tidak berada di realm yang benar"}
		if dest_realm != self.current_realm:
			return self.send_message_or_file(username_from, username_dest, dest_realm,group_destination=group_destination, filename=filename, filecontent=filecontent)
		filecontent = base64.b64decode(filecontent)
		file_msg = {'msg_from': s_fr['nama'], 'realm_from': s_fr['realm'], 'msg_to': s_to['nama'], 'realm_to': s_to['realm'], 'group': group_destination, 'filename': filename, 'filecontent': filecontent}
		return self.file_sending_process(file_msg, s_fr, s_to, username_dest, filename, filecontent)
		
	def sent_file_from_other_realm(self, username_from, username_dest, group_destination, filename, filecontent):
		username_dest, dest_realm = self._parse_realm(username_dest)
		s_fr = self.get_user(username_from)
		s_to = self.get_user(username_dest)
		if not s_fr or not s_to:
			return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
		filecontent = base64.b64decode(filecontent)
		if group_destination != '':
			file_msg = {'msg_from': s_fr['nama'], 'realm_from': s_fr['realm'], 'msg_to': s_to['nama'], 'realm_to': s_to['realm'], 'group': group_destination, 'filename': filename, 'filecontent': filecontent}
		else :
			file_msg = {'msg_from': s_fr['nama'], 'realm_from': s_fr['realm'], 'msg_to': s_to['nama'], 'realm_to': s_to['realm'], 'filename': filename, 'filecontent': filecontent}
		return self.file_sending_process(file_msg, s_fr, s_to, username_dest, filename, filecontent)
		
	def file_sending_process(self, file_msg, s_fr, s_to, username_dest, filename, filecontent):
		logging.warning("filecontent: {}".format(file_msg))
		outqueue_sender = s_fr['outgoing']
		inqueue_receiver = s_to['incoming']
		self._enqueue_message(outqueue_sender, inqueue_receiver, username_dest, file_msg)
		sender_sent_dir = f"{username_dest}_sent"
		if not os.path.exists(sender_sent_dir):
			os.makedirs(sender_sent_dir)
		base_filename, file_extension = os.path.splitext(filename)
		counter = 0
		while True:
			if counter > 0:
				new_filename = f"{base_filename} ({counter}){file_extension}"
			else:
				new_filename = f"{base_filename}{file_extension}"

			filepath = os.path.join(sender_sent_dir, new_filename)
			
			if not os.path.exists(filepath):
				break
			counter += 1
		with open(filepath, 'wb') as f:
			f.write(filecontent)
		return {'status': 'OK', 'message': 'File Sent'}

if __name__ == "__main__":
	j = Chat()
	sesi = j.proses("auth messi surabaya")
	print(sesi)
	if sesi['status'] == 'OK':
		tokenid = sesi['tokenid']
		print(j.proses(f"send {tokenid} henderson hello gimana kabarnya son"))
		print(j.proses(f"send {tokenid} henderson@realm2 hello gimana kabarnya son"))
		print(j.proses(f"send {tokenid} Informatika Halo grup informatika!"))
		print(j.proses(f"inbox {tokenid}"))
		print(j.proses(f"sendfile {tokenid} henderson test.txt Ini isi file test.txt"))
		print(j.proses(f"inbox {tokenid}"))
