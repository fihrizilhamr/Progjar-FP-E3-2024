from chat_client import *
import flet as ft
import base64
import json

TARGET_IP = os.getenv("SERVER_IP") or "127.0.0.1"
TARGET_PORT = os.getenv("SERVER_PORT") or "8889"

HINT_LIST = """
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
        list_my_groups
            - List user's group chat.
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
        list_users
            - List user from the server.
        exit
            - Quits the program.
    """

COMMAND_LIST = [
    " ",
    "register",
    "auth",
    "inbox",
    "logout",
    "send",
    "add_group",
    "join_group",
    "leave_group",
    "list_group",
    "list_my_groups",
    "get_group",
    "send_group",
    "send_file",
    "send_group_file",
    "add_realm",
    "set_server",
    "list_server_data",
    "list_users",
    "exit"
]

def main(page: ft.Page):
    cc = ChatClient()
    selected_file_path = None

    def login_user(e):
        username = login_username.value
        password = login_password.value
        response = cc.proses(f"auth {username} {password}")
        if "logged in" in response:
            page.session.set("token", cc.tokenid)
            show_chat_view()
        else:
            login_error.value = response
            page.update()

    def register_user(e):
        username = register_username.value
        password = register_password.value
        country = register_country.value
        name = register_name.value
        response = cc.proses(f"register {username} {password} {country} {name}")
        if "register in" in response:
            page.session.set("token", cc.tokenid)
            show_chat_view()
        else:
            register_error.value = response
            page.update()

    def btn_click(e):
        if not cmd.value and not dropdown.value:
            cmd.error_text = "Please enter a command"
            page.update()
        else:
            if dropdown.value is not None and dropdown.value.strip() != "":
                command_text = dropdown.value + " " + cmd.value
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

    def show_login_view():
        page.clean()
        page.add(
            ft.Row([ft.Text("Chat Application", style="headlineMedium"), ft.Row([help_icon, theme_toggle])], alignment="spaceBetween"),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Login", style="headlineMedium"),
                        login_username,
                        login_password,
                        ft.ElevatedButton("Login", on_click=login_user),
                        login_error,
                        ft.ElevatedButton("Back", on_click=lambda e: show_home_view())
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        )
        page.update()

    def show_register_view():
        page.clean()
        page.add(
            ft.Row([ft.Text("Chat Application", style="headlineMedium"), ft.Row([help_icon, theme_toggle])], alignment="spaceBetween"),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Register", style="headlineMedium"),
                        register_username,
                        register_password,
                        register_country,
                        register_name,
                        ft.ElevatedButton("Register", on_click=register_user),
                        register_error,
                        ft.ElevatedButton("Back", on_click=lambda e: show_home_view())
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        )
        page.update()

        
    



    def show_private_chat_view():
        user_list = cc.list_users()
        user_options = [ft.dropdown.Option(user) for user in user_list]
        def update_view(e):
            if action_dropdown.value == "Send Message":
                message_container.visible = True
                file_container.visible = False
            elif action_dropdown.value == "Send File":
                message_container.visible = False
                file_container.visible = True
            page.update()

        action_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Send Message"),
                ft.dropdown.Option("Send File")
            ],
            on_change=update_view
        )

        # Message input fields
        private_chat_receiver = ft.Dropdown(label="Receiver's Username", options=user_options)
        private_chat_message = ft.TextField(label="Message")
        private_chat_send_button = ft.ElevatedButton("Send", on_click=lambda e: send_private_message(private_chat_receiver.value, private_chat_message.value))
        message_container = ft.Container(
            content=ft.Column(
                [
                    private_chat_receiver,
                    private_chat_message,
                    private_chat_send_button
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )

        # File input fields
        private_chat_receiver_file = ft.Dropdown(label="Receiver's Username", options=user_options)
        private_chat_file = ft.TextField(label="Filename")
        private_chat_send_file_button = ft.ElevatedButton("Send File", on_click=lambda e: send_private_file(private_chat_receiver_file.value, private_chat_file.value))
        file_container = ft.Container(
            content=ft.Column(
                [
                    private_chat_receiver_file,
                    private_chat_file,
                    private_chat_send_file_button
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            visible=False
        )

        private_chat_view = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Private Chat", style="headlineMedium"),
                    action_dropdown,
                    message_container,
                    file_container,
                    ft.ElevatedButton("Back", on_click=lambda e: show_chat_view())
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True
        )
        page.clean()
        page.add(ft.Row([ft.Text("Chat Application", style="headlineMedium"), ft.Row([help_icon, theme_toggle])], alignment="spaceBetween"))
        page.add(lv)
        page.add(private_chat_view)
        page.update()

    def send_private_message(receiver, message):
        response = cc.proses(f"send {receiver} {message}")
        lv.controls.append(ft.Text(f"To {receiver}: {message}"))
        lv.controls.append(ft.Text(f"Server response: {response}"))
        page.update()

    def send_private_file(receiver, file):
        response = cc.proses(f"send_file {receiver} {file}")
        lv.controls.append(ft.Text(f"To {receiver}: Sent file {file}"))
        lv.controls.append(ft.Text(f"Server response: {response}"))
        page.update()

    def show_group_chat_view():
        group_list = cc.list_my_groups()
        group_options = [ft.dropdown.Option(group) for group in group_list]
        def update_view(e):
            if action_dropdown.value == "Send Message":
                message_container.visible = True
                file_container.visible = False
            elif action_dropdown.value == "Send File":
                message_container.visible = False
                file_container.visible = True
            page.update()

        action_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Send Message"),
                ft.dropdown.Option("Send File")
            ],
            on_change=update_view
        )

        # Message input fields
        group_chat_name = ft.Dropdown(label="Group Name", options=group_options)
        group_chat_message = ft.TextField(label="Message")
        group_chat_send_button = ft.ElevatedButton("Send", on_click=lambda e: send_group_message(group_chat_name.value, group_chat_message.value))
        message_container = ft.Container(
            content=ft.Column(
                [
                    group_chat_name,
                    group_chat_message,
                    group_chat_send_button
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )

        # File input fields
        group_chat_name_file = ft.Dropdown(label="Group Name", options=group_options)
        group_chat_file = ft.TextField(label="Filename")
        group_chat_send_file_button = ft.ElevatedButton("Send File", on_click=lambda e: send_group_file(group_chat_name_file.value, group_chat_file.value))
        file_container = ft.Container(
            content=ft.Column(
                [
                    group_chat_name_file,
                    group_chat_file,
                    group_chat_send_file_button
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            visible=False
        )

        group_chat_view = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Group Chat", style="headlineMedium"),
                    action_dropdown,
                    message_container,
                    file_container,
                    ft.ElevatedButton("Back", on_click=lambda e: show_chat_view())
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True
        )

        page.clean()
        page.add(ft.Row([ft.Text("Chat Application", style="headlineMedium"), ft.Row([help_icon, theme_toggle])], alignment="spaceBetween"))
        page.add(lv)
        page.add(group_chat_view)
        page.update()

    def send_group_message(group_name, message):
        response = cc.proses(f"send_group {group_name} {message}")
        lv.controls.append(ft.Text(f"To group {group_name}: {message}"))
        lv.controls.append(ft.Text(f"Server response: {response}"))
        page.update()

    def send_group_file(group_name, file):
        response = cc.proses(f"send_group_file {group_name} {file}")
        lv.controls.append(ft.Text(f"To group {group_name}: Sent file {file}"))
        lv.controls.append(ft.Text(f"Server response: {response}"))
        page.update()

    def parse_inbox(data):
        parsed_data = json.loads(data)
        private_messages = []
        group_messages = []

        for user, messages in parsed_data.items():
            for msg in messages:
                if "group" in msg:
                    group_messages.append(msg)
                else:
                    private_messages.append(msg)

        return private_messages, group_messages

    def display_inbox_view():
        inbox_data = cc.proses(f"inbox")
        private_messages, group_messages = parse_inbox(inbox_data)

        def create_message_view(msg):
            controls = [
                ft.Text(f"From: {msg['msg_from']}", style="subtitle1"),
                ft.Text(f"Realm From: {msg['realm_from']}", style="subtitle2"),
                ft.Text(f"To: {msg['msg_to']}", style="subtitle1"),
                ft.Text(f"Realm To: {msg['realm_to']}", style="subtitle2")
            ]

            if "msg" in msg:
                controls.append(ft.Text(f"Message: {msg['msg']}", style="body1"))

            if "filename" in msg and "filecontent" in msg:
                try:
                    image = ft.Image(
                        src_base64=f"{msg['filecontent']}",
                        width=300,
                        height=300,
                        fit=ft.ImageFit.CONTAIN
                    )
                    controls.append(ft.Text(f"Filename: {msg['filename']}", style="subtitle2"))
                    controls.append(image)
                except Exception as e:
                    controls.append(ft.Text(f"Error displaying file: {e}", style="body2"))

            return ft.Column(controls, spacing=10)

        def create_chat_view(messages, title):
            message_views = [
                ft.Card(
                    content=ft.Column(
                        [
                            ft.Text(msg['msg_from'] if 'msg_from' in msg else "Unknown", style="headlineSmall"),
                            create_message_view(msg)
                        ],
                        
                        spacing=10,
                    ),
                    margin=10,
                    elevation=3
                )
                for msg in messages
            ]
            return ft.ListView(
                message_views,
                spacing=10,
                padding=10,
                auto_scroll=True,  
                # expand=True
            )

        page.clean()
        page.add(
            ft.Column(
                [
                    ft.Row([ft.Text("Chat Application", style="headlineMedium"), ft.Row([help_icon, theme_toggle])], alignment="spaceBetween"),
                    ft.ElevatedButton("Back", on_click=lambda e: show_chat_view()),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Private Messages", style="headlineMedium"),
                                create_chat_view(private_messages, "Private Messages")
                            ],
                        ),
                        # padding=ft.Padding(left=10, right=10, top=10, bottom=10),
                        border=ft.BorderSide(width=1, color="black"),
                        # border_radius=ft.BorderRadius(5, 5, 5, 5),
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Group Messages", style="headlineMedium"),
                                create_chat_view(group_messages, "Group Messages")
                            ],
                        ),
                        # padding=ft.Padding(left=10, right=10, top=10, bottom=10),
                        border=ft.BorderSide(width=1, color="black"),
                        # border_radius=ft.BorderRadius(5, 5, 5, 5),
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                scroll=True,
                expand=True
            )
        )
        page.update()




# ft.ElevatedButton("Back", on_click=lambda e: show_chat_view())
    def show_chat_view():
        page.clean()
        page.add(
            ft.Row([ft.Text("Chat Application", style="headlineMedium"),ft.Row([help_icon, theme_toggle])],alignment="spaceBetween"),
            ft.Column(
                [
                    lv,
                    ft.Row([dropdown, cmd, send_button], alignment="start", spacing=0),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.ElevatedButton("Private Chat", on_click=lambda e: show_private_chat_view(), width=page.width,),
                                ft.ElevatedButton("Group Chat", on_click=lambda e: show_group_chat_view(), width=page.width,),
                                ft.ElevatedButton("Inbox", on_click=lambda e: display_inbox_view(), width=page.width,),
                                ft.ElevatedButton("Logout", on_click=logout_user, width=page.width)
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        alignment=ft.alignment.center
                    ),
                    
                ],
                expand=True,
            )
        )
        page.update()

    def logout_user(e):
        response = cc.proses("logout")
        lv.controls.append(ft.Text(f"Logout response: {response}"))
        # Clear login form fields
        login_username.value = ""
        login_password.value = ""
        login_error.value = ""

        # Clear register form fields
        register_username.value = ""
        register_password.value = ""
        register_country.value = ""
        register_name.value = ""
        register_error.value = ""
        page.session.remove("token")
        show_home_view()

    def show_home_view():
        page.clean()
        page.add(
            ft.Row([ft.Text("Chat Application", style="headlineMedium"), ft.Row([help_icon, theme_toggle])], alignment="spaceBetween"),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Welcome to Chat Application", style="headlineMedium"),
                        ft.ElevatedButton("Login", on_click=lambda e: show_login_view()),
                        ft.ElevatedButton("Register", on_click=lambda e: show_register_view()),

                        # ft.ElevatedButton("Toggle Theme", on_click=toggle_theme)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        )
        page.update()

    help_dialog = ft.AlertDialog(
        title=ft.Text("Command List"),
        content=ft.Text(HINT_LIST, selectable=True),
        actions=[ft.TextButton("Close", on_click=close_help_dialog)],
        on_dismiss=close_help_dialog
    )
    lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
    dropdown = ft.Dropdown(
        label="Select command",
        options=[ft.dropdown.Option(command) for command in COMMAND_LIST],
    )
    cmd = ft.TextField(
        label="Your command",
        text_style=ft.TextStyle(overflow=ft.TextOverflow.ELLIPSIS),
        expand=True
    )
    send_button = ft.ElevatedButton("Send", on_click=btn_click)
    help_icon = ft.IconButton(icon=ft.icons.HELP, on_click=show_help_dialog)
    theme_toggle = ft.IconButton(icon=ft.icons.BRIGHTNESS_6, on_click=toggle_theme)

    login_username = ft.TextField(label="Username")
    login_password = ft.TextField(label="Password", password=True, can_reveal_password=True)
    login_error = ft.Text(color=ft.colors.RED)

    register_username = ft.TextField(label="Username")
    register_password = ft.TextField(label="Password", password=True, can_reveal_password=True)
    register_country = ft.TextField(label="Country")
    register_name = ft.TextField(label="Name")
    register_error = ft.Text(color=ft.colors.RED)

    page.theme_mode = ft.ThemeMode.LIGHT

    show_home_view()

if __name__ == '__main__':
    ft.app(target=main)