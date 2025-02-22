from base64 import b64encode
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from requests import HTTPError
from rich import print
from rich.table import Table

import lib

session_token: Optional[str] = None


class NotLoggedInError(Exception): ...


def print_error(msg: Any):
    print(f"[red]Error[/red]: {msg}")


def handle_http_error(e: HTTPError):
    print_error(e.response.json()["message"])


class Command: ...


@dataclass
class NewUserCommand(Command):
    username: str
    password: str
    confirm_password: str


@dataclass
class LoginCommand(Command):
    username: str
    password: str


@dataclass
class LogoutCommand(Command): ...


@dataclass
class PutCommand(Command):
    filename: str


@dataclass
class ViewCommand(Command): ...


@dataclass
class GetCommand(Command):
    filename: str
    username: Optional[str]


@dataclass
class ShareCommand(Command):
    filename: str
    username: str


@dataclass
class QuitCommand(Command): ...


def parse_command(cmd: List[str]) -> Command:
    try:
        if cmd[0] == "newuser":
            assert len(cmd) == 4
            username, password, confirm_password = cmd[1], cmd[2], cmd[3]
            return NewUserCommand(username, password, confirm_password)

        elif cmd[0] == "login":
            assert len(cmd) == 3
            username, password = cmd[1], cmd[2]
            return LoginCommand(username, password)

        elif cmd[0] == "logout":
            assert len(cmd) == 1
            return LogoutCommand()

        elif cmd[0] == "put":
            assert len(cmd) == 2
            filename = cmd[1]
            return PutCommand(filename)

        elif cmd[0] == "view":
            assert len(cmd) == 1
            return ViewCommand()

        elif cmd[0] == "get":
            assert len(cmd) == 2 or len(cmd) == 3
            filename, username = cmd[1], None
            if len(cmd) == 3:
                username = cmd[2]
            return GetCommand(filename, username)

        elif cmd[0] == "share":
            assert len(cmd) == 3
            filename, username = cmd[1], cmd[2]
            return ShareCommand(filename, username)

        elif cmd[0] == "quit":
            assert len(cmd) == 1
            return QuitCommand()

        else:
            raise ValueError("Invalid command")

    except AssertionError:
        raise ValueError("Invalid arguments")


def execute_command(cmd: Command):
    global session_token

    if isinstance(cmd, NewUserCommand):
        if cmd.password != cmd.confirm_password:
            raise ValueError("The passwords do not match.")
        lib.register(cmd.username, cmd.password)

    elif isinstance(cmd, LoginCommand):
        if session_token is not None:
            raise Exception("Already logged in.")
        session_token = lib.login(cmd.username, cmd.password)

    elif isinstance(cmd, LogoutCommand):
        if session_token is None:
            raise NotLoggedInError()
        lib.logout(session_token)
        session_token = None

    elif isinstance(cmd, PutCommand):
        if session_token is None:
            raise NotLoggedInError()
        file = Path(cmd.filename)
        lib.put_file(session_token, file.name, b64encode(file.read_bytes()).decode())

    elif isinstance(cmd, ViewCommand):
        if session_token is None:
            raise NotLoggedInError()

        files: List[Dict[str, Any]] = lib.list_files(session_token)

        table = Table("Name", "Size", "Date Modified", "Owner")
        for file in files:
            key, size, modified = file["key"], file["size"], file["modified"]

            delim_index = key.find("/")
            owner = key[:delim_index]
            filename = key[delim_index + 1 :]

            modified = datetime.fromisoformat(modified).strftime("%Y-%m-%d %H:%M:%S")

            table.add_row(filename, lib.natural_size(size), modified, owner)

        print(table)

    elif isinstance(cmd, GetCommand):
        if session_token is None:
            raise NotLoggedInError()

        content = lib.get_file(session_token, cmd.filename, cmd.username)
        with open(cmd.filename, "wb") as f:
            f.write(content)

    elif isinstance(cmd, ShareCommand):
        if session_token is None:
            raise NotLoggedInError()

        lib.share_file(session_token, cmd.filename, cmd.username)

    elif isinstance(cmd, QuitCommand):
        if session_token is not None:
            lib.logout(session_token)

        exit(0)


def main():
    BANNER = """Welcome to myDropbox Application
======================================================
Please input command (newuser username password password, login
username password, put filename, get filename, view, or logout).
If you want to quit the program just type quit.
======================================================"""
    print(BANNER)
    while True:
        cmd = input(">>")
        cmd = cmd.strip().split()

        if len(cmd) == 0:
            continue

        try:
            cmd = parse_command(cmd)
        except ValueError as e:
            print_error(e.args)
            continue

        try:
            execute_command(cmd)
        except HTTPError as e:
            handle_http_error(e)
        except Exception as e:
            print_error(e)


if __name__ == "__main__":
    main()
