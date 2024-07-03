from chat_client import *
import flet as ft

TARGET_IP = "127.0.0.1"
TARGET_PORT = "8889"

COMMAND_LIST = """
Command List
Auth:
    auth <username> <password> - Log in with the specified username and password within the default realm.
    auth <username>@<user's realm> <password> - Log in with the specified username and password within the specified realm.
    logout - Log out.

Private Chat:
    send <receiver's username> <message> - Send a message to a user within the same realm.
    send <receiver's username>@<receiver's realm> <message> - Send a message to a user in a different realm.

Group Chat:
    send_group <group's name> <message> - Send a message to a group chat.
"""

class GroupList(ft.Container):
    def __init__(self, page, groups):  # Corrected __init__ method
        super().__init__()
        self.content = ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.icons.PERSON),
                    title=ft.Text(f"{value['nama']}"),
                    on_click=lambda _: page.go(f"/groupchat/{value['nama']}"),
                )
                for value in groups.values()
            ],
        )
        self.padding = ft.padding.symmetric(vertical=10)

"""
Send File Private Chat:
    send_file <receiver's username> <filename> - Send a file to a user within the same realm.
    send_file <receiver's username>@<receiver's realm> <filename> - Send a file to a user in a different realm.

Send File Group Chat:
    send_group_file <group's name> <filename> - Send a file to a group chat.
"""

class GroupChatRoom:
    def __init__(self, page, cc, from_user, to_group):  # Corrected __init__ method
        self.chat = ft.TextField(
            label="Write a message...",
            autofocus=True,
            expand=True,
            on_submit=self.send_click,
        )
        self.lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
        self.send = ft.IconButton(
            icon=ft.icons.SEND_ROUNDED,
            tooltip="Send message",
            on_click=self.send_click,
        )
        self.file_picker = ft.FilePicker(on_result=self.upload_files, on_upload=self.upload_server)
        self.file_pick = ft.IconButton(
            icon=ft.icons.UPLOAD_FILE_ROUNDED,
            tooltip="Send file",
            on_click=self.on_pick_file,
        )
        self.page = page
        self.cc = cc
        self.from_user = from_user
        self.to_group = to_group
        self.page.pubsub.subscribe(self.on_chat)

    def on_pick_file(self, _e_):
        self.page.overlay.append(self.file_picker)
        self.page.update()
        self.file_picker.pick_files(allow_multiple=True)

    def send_click(self, _e_):
        if not self.chat.value:
            self.chat.error_text = "Please enter message"
            self.page.update()
        else:
            command = f"sendgroup {self.to_group} {self.chat.value}"
            server_call = self.cc.proses(command)
            self.lv.controls.append(ft.Text("To {}: {}".format(self.to_group, self.chat.value)))

            if "sent" in server_call:
                self.page.pubsub.send_all(self.chat.value)

            self.chat.value = ""
            self.chat.focus()
            self.page.update()

    def on_chat(self, message):
        check_inbox_group = json.loads(self.cc.inboxgroup(self.to_group))
        for user in check_inbox_group:
            if user != self.from_user and check_inbox_group[user][0]['msg_ufrom'] is not self.from_user:
                self.lv.controls.append(ft.Text("From {}: {}".format(check_inbox_group[user][0]['msg_from'], check_inbox_group[user][0]['msg'])))
        self.page.update()

    def upload_files(self, e: ft.FilePickerResultEvent):
        upload_list = []
        if self.file_picker.result != None and self.file_picker.result.files != None:
            for f in self.file_picker.result.files:
                upload_list.append(
                    ft.FilePickerUploadFile(
                        f.name,
                        upload_url=self.page.get_upload_url(f.name, 600),
                    )
                )
            self.file_picker.upload(upload_list)
    
    def upload_server(self, e: ft.FilePickerUploadEvent):
        if(e.progress == 1):
            command = f"sendfile {self.to_group} app\\client\\upload\\{e.file_name}"
            print(command)
            server_call = self.cc.proses(command)
            print(server_call)
            self.lv.controls.append(ft.Text("To {}: Berhasil mengirim file {}".format(self.to_group, e.file_name)))

            if "sent" in server_call:
                self.page.pubsub.send_all(self.chat.value)

            self.chat.value = ""
            self.chat.focus()
            self.page.update()

def main(page):
    def btn_click(e):
        if not cmd.value:
            cmd.error_text = "Please enter a command"
            page.update()
        else:
            command_text = cmd.value
            lv.controls.append(ft.Text(f"Command: {command_text}"))
            response_text = cc.proses(command_text)
            lv.controls.append(ft.Text(f"Result {cc.tokenid}: {response_text}"))
            cmd.value = ""
            page.update()

    def show_help_dialog(e):
        help_dialog.open = True
        page.dialog = help_dialog
        page.update()

    def close_help_dialog(e):
        help_dialog.open = False
        page.update()

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        page.update()

    cc = ChatClient()
    help_dialog = ft.AlertDialog(
        title=ft.Text("Command List"),
        content=ft.Text(COMMAND_LIST, selectable=True),
        actions=[ft.TextButton("Close", on_click=close_help_dialog)],
        on_dismiss=close_help_dialog
    )
    lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
    cmd = ft.TextField(label="Your command", expand=True)
    send_button = ft.ElevatedButton("Send", on_click=btn_click)
    help_icon = ft.IconButton(icon=ft.icons.HELP, on_click=show_help_dialog)
    theme_toggle = ft.IconButton(icon=ft.icons.BRIGHTNESS_6, on_click=toggle_theme)
    
    from_user = "user1" 
    to_group = "group1"  
    group_chat_room = GroupChatRoom(page, cc, from_user, to_group)
    
    page.add(
        ft.Column(
            [
                ft.Row([ft.Text("Chat Application", style="headlineMedium"), ft.Row([help_icon, theme_toggle])], alignment="spaceBetween"),
                lv,
                ft.Row([cmd, send_button], alignment="spaceBetween"),
                group_chat_room.lv,  # ListView for GroupChatRoom
                ft.Row([group_chat_room.chat, group_chat_room.send, group_chat_room.file_pick], alignment="spaceBetween"),
            ],
            expand=True,
        )
    )
    page.theme_mode = ft.ThemeMode.LIGHT
    groups = {
			'messi': { 'nama': 'Lionel Messi', 'negara': 'Argentina', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm1'},
			'henderson': { 'nama': 'Jordan Henderson', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm2'},
			'lineker': { 'nama': 'Gary Lineker', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm3'},
			'ilham1': { 'nama': 'Ilham Satu', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm1'},
			'ilham2': { 'nama': 'Ilham Dua', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm2'},
			'ilham3': { 'nama': 'Ilham Tiga', 'negara': 'Indonesia', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}, 'realm': 'realm3'}
		}
    # result = cc.get_groups()
    # if isinstance(result, str):
    #     try:
    #         groups = json.loads(result)  
    #     except json.JSONDecodeError as e:
    #         logging.warning(f"JSON decoding failed: {e}")
    # elif isinstance(result, dict):
    #     groups = result 
    # groups = json.loads(cc.get_groups())
    page.add(GroupList(page, groups))


if __name__ == '__main__':
    ft.app(target=main)
