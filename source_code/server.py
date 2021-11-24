import threading
import socket
import time

class Server:
	rooms = {}
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def __init__(self, port):
		print(f"[INFO] server is now binding to port {port}")
		self.sock.bind(('localhost', int(port)))
		self.sock.listen(1)
		print("[INFO] bind sucessfull. Now Listening")

	def handler(self, connection, address):
		while True:
			received_bytes = connection.recv(1024)
			data = received_bytes.decode("utf-8")
			if not data:
				connection.close()
				print(f"[CONNECTION TERMINATED] now active {threading.activeCount()-2}")
				break

			operation = data.split("|")[0]
			if operation == "__join__":
				connection.send(bytes(str(data.split("|")[1] in list(self.rooms.keys())), "utf-8"))

			if operation == "__add__":
				try:
					room_id = data.split("|")[1]
					nick_name = data.split("|")[2]
					self.rooms[room_id].append([connection, nick_name])
					connection.send(bytes("True", "utf-8"))
					print(f"Added a new user {nick_name} to room {room_id}")
					for people in self.rooms[room_id]:
						if people[0] != connection:
							try:
								people[0].send(bytes(f"__alert__|{nick_name}", "utf-8"))
								print(f"SENT {people[1]}")

							except:
								self.rooms[room_id].remove(people)

				except Exception as e:
					connection.send(bytes("False", "utf-8"))
					connection.send(bytes(str(e), "utf-8"))

			if operation == "__brodcast__":
				room_id = data.split("|")[1]
				name = data.split("|")[2]
				message = data.split("|")[3]
				for people in self.rooms[room_id]:
					if people[0] != connection:
						try:
							people[0].send(bytes(f"{name}|{message}", "utf-8"))
						except:
							people[0].close()
							self.rooms[room_id].remove(people)

			if operation == "__exit_event__":
				name = data.split("|")[1]
				room_id = data.split("|")[2]
				for people in self.rooms[room_id]:
					try:
						people[0].send(bytes(f"__exit_event__|{name}", "utf-8"))
					except:
						people[0].close()
						self.rooms[room_id].remove(people)
				self.rooms[room_id].remove([connection, name])
				print(f"Removed {name} from room {room_id}")

			if operation == "__create__":
				room_id = data.split("|")[1]
				nick_name = data.split("|")[2]
				self.rooms[room_id] = []
				self.rooms[room_id].append([connection, nick_name])

			if operation == "__info__":
				room_id = data.split("|")[1]	
				info = [x[1] for x in self.rooms[room_id]]
				connection.send(bytes(str("|".join(info)), "utf-8"))

	def start_listening(self):
		while True:
			conn, addr = self.sock.accept()
			print(f"[NEW CONNECTION] new client {addr} connected.")
			cThread = threading.Thread(target=self.handler, args=(conn, addr), daemon = True)
			cThread.start()
			print(f"[ACTIVE COUNT] {threading.activeCount()-1}")

if __name__ == '__main__':
	# port = input("Enter port to bind to: ")
	Server("8080").start_listening()