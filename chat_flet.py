from chat_client import *
import flet as ft

TARGET_IP = "127.0.0.1"
TARGET_PORT = "8889"

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
    "get_group",
    "send_group",
    "send_file",
    "send_group_file",
    "add_realm",
    "set_server",
    "list_server_data",
    "exit"
]

def main(page):
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

    cc = ChatClient()
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
    page.add(
        ft.Column(
            [
                ft.Row([ft.Text("Chat Application", style="headlineMedium"), ft.Row([help_icon, theme_toggle])], alignment="spaceBetween"),
                lv,
                ft.Row([dropdown, cmd, send_button], alignment="start", spacing=0)
            ],
            expand=True,
        )
    )
    page.theme_mode = ft.ThemeMode.LIGHT

if __name__ == '__main__':
    ft.app(target=main)
