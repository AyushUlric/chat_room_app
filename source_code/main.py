import sys
import socket
import screens
from threading import Thread
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.screenmanager import SlideTransition
from kivymd.uix.button import MDFillRoundFlatButton, MDRectangleFlatButton

# Main class
class ChatApp(MDApp):
	chat = True
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	room_id = ""
	name = ""

	# Overriding the default constructor to bind window and keyboard events.
	def __init__(self, **kwargs):
		super(ChatApp, self).__init__(**kwargs)
		Window.bind(on_keyboard=self.events)


	# Build the GUI according to the kv file.
	def build(self):
		Window.keyboard_anim_args = {'d':.2,'t':'in_out_expo'}
		Window.softinput_mode = "below_target"
		self.theme_cls.primary_palette = "Indigo"
		master = Builder.load_file("main.kv")
		return master

	# Attempt connection to the server on startup.
	def connect_to_server(self, url, port):
		try:
			self.sock.connect((url, int(port)))
			self.sock.send(bytes(socket.gethostname(), "utf-8"))
			self.root.current = 'home_screen'
			toast("Connected")
		except:
			toast("Unable to connect to the server. Please make sure it is running and restart the application")

	# To handle keyboard events, in this case, send message when enter is pressed.
	def events(self, window, key, *args):
		if key==13:
			if self.root.current == 'chat_room':
				self.send_message(self.root.ids.chat_room.ids.message.text)
		return True

	# Receive data from server.
	def receive(self):
		data = self.sock.recv(1024).decode("utf-8")
		return data

	# Send data to server.
	def send(self, text):
		self.sock.send(bytes(text, "utf-8"))

	# Check weather a room exists or not.
	def _join_room(self, room_id):
		self.send(f"__join__|{room_id}")
		room_exists = eval(self.receive())
		if room_exists:
			self.root.current = "join_room"
			self.room_id = room_id
			self.root.ids.join_room.ids.nickname.text = socket.gethostname()
		else:
			print("room not exists")
			MDDialog(title="Room does not exist", text="You may create your own room.").open()

	# Join a room.
	def join_room(self, nickname):
		self.send(f"__add__|{self.room_id}|{nickname}")
		status = self.receive()
		if status == "False":
			error_msg = self.receive()
			MDDialog(title="Error", text=error_msg).open()
			return 
		self.root.ids.chat_room.ids.toolbar.title = "Room " + self.room_id
		self.root.current = "chat_room"
		self.name = nickname
		self.chat_thread = Thread(target=self.chat, daemon=True)
		self.chat_thread.start()

	# A thread which listens to the server infinitely (Until explicitly destroyed)
	def chat(self):
		while True:
			message = self.sock.recv(1024).decode("utf-8")
			if not self.chat: sys.exit()
			if not message : break
			try:
				if message.split("|")[0] == "__alert__":
					toast(message.split("|")[1] + " joined")
				elif message.split("|")[0] == "__exit_event__":
					toast(message.split("|")[1] + " left")
				elif message.count("|")==1:
					message_bubble = MDFillRoundFlatButton(text=f"{message.split('|')[0].upper()}\n\n"+message.split('|')[1], size_hint=(None,None), md_bg_color = (74/255,67/255,156/255,1))
					root_card = MDAnchorLayout(size_hint=(1, None), anchor_x="left")
					primary_box = MDBoxLayout(orientation="vertical", size_hint=(None, None), width=self.root.width)
					primary_box.add_widget(root_card)
					root_card.add_widget(message_bubble)
					self.root.ids.chat_room.ids.chat_list.add_widget(primary_box)
				self.scroll_bottom()
			except Exception as e:
				print("EXCEPTION WHILE CALLING chat(): ", e)

	# Brodcast a message to all the people in current rom.
	def send_message(self, message):
		if message:
			self.send(f"__brodcast__|{self.room_id}|{self.name}|{message}")
			self.root.ids.chat_room.ids.message.text = ""
			message_bubble = MDFillRoundFlatButton(text="Me\n"+message, size_hint=(None,None), md_bg_color = (50/255,32/255,250/255,1))
			root_card = MDAnchorLayout(size_hint=(1, None), anchor_x="right")
			primary_box = MDBoxLayout(orientation="vertical", size_hint=(None, None), width=self.root.width)
			primary_box.add_widget(root_card)
			root_card.add_widget(message_bubble)
			self.root.ids.chat_room.ids.chat_list.add_widget(primary_box)
			self.root.ids.chat_room.ids.message.focus = True
			self.scroll_bottom()

	# Bring a new message in focus by scrolling down.
	def scroll_bottom(self):
		if self.root.ids.chat_room.ids.chat_view.scroll_y!=0:
			Animation.cancel_all(self.root.ids.chat_room.ids.chat_view, 'scroll_y')
			Animation(scroll_y=0, t='out_quad', d=.5).start(self.root.ids.chat_room.ids.chat_view)

	# Create and join a room.
	def create_room(self, room_id, nickname):
		self.send(f"__join__|{room_id}|{nickname}")
		status = eval(self.receive())
		if status:
			toast("Room already exists")
			return 
		self.send(f"__create__|{room_id}|{nickname}")
		self.root.ids.chat_room.ids.toolbar.title = "Room " + room_id
		self.root.current = "chat_room"
		self.name = nickname
		self.room_id = room_id
		self.chat_thread = Thread(target=self.chat, daemon=True)
		self.chat_thread.start()

	# Notify the server about an exit event.
	def exit_room(self):
		self.chat = False
		print("HCAT FASLE")
		self.send(f"__exit_event__|{self.name}|{self.room_id}")
		self.root.current = "join_room"

	# Get the names of all peoples in the room.
	def get_room_info(self):
		Thread(target=self._get_room_info, daemon=True).start()

	def _get_room_info(self):
		self.send(f"__info__|{self.room_id}")
		room_info = self.receive()
		MDDialog(title="People in room", text=room_info.replace("|","\n")).open()

if __name__ == '__main__':
	ChatApp().run()