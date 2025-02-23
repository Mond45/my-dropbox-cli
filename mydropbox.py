from base64 import b64encode
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests import HTTPError

API_BASE_URL = "<API_URL>"


# Session token is stored in-memory
session_token: Optional[str] = None


# Utility function for displaying error information
def print_error(msg):
    if isinstance(msg, list) or isinstance(msg, tuple):
        print(f"Error: {', '.join([ str(e) for e in msg ])}")
    else:
        print(f"Error: {msg}")


# Natural file size for `view` command
def natural_size(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


class NotLoggedInError(Exception): ...


# The base class for storing options for each command (newuser, login, ...)
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
    # validate the number of arguments, return a Command dataclass
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

        r = requests.post(
            f"{API_BASE_URL}/register",
            json={"username": cmd.username, "password": cmd.password},
        )
        r.raise_for_status()

    elif isinstance(cmd, LoginCommand):
        if session_token is not None:
            raise Exception("Already logged in.")

        r = requests.post(
            f"{API_BASE_URL}/login",
            json={"username": cmd.username, "password": cmd.password},
        )
        r.raise_for_status()
        session_token = r.json()["token"]

    elif isinstance(cmd, LogoutCommand):
        if session_token is None:
            raise NotLoggedInError()

        r = requests.post(
            f"{API_BASE_URL}/logout", headers={"x-session-token": session_token}
        )
        r.raise_for_status()
        session_token = None

    elif isinstance(cmd, PutCommand):
        if session_token is None:
            raise NotLoggedInError()

        file = Path(cmd.filename)
        r = requests.put(
            f"{API_BASE_URL}/file",
            headers={"x-session-token": session_token},
            json={
                "file_name": file.name,
                "content": b64encode(file.read_bytes()).decode(),
            },
        )
        r.raise_for_status()

    elif isinstance(cmd, ViewCommand):
        if session_token is None:
            raise NotLoggedInError()

        r = requests.get(
            f"{API_BASE_URL}/files", headers={"x-session-token": session_token}
        )
        r.raise_for_status()

        files: List[Dict[str, Any]] = r.json()

        for file in files:
            key, size, modified = file["key"], file["size"], file["modified"]

            # the first path segment indicates the file owner, assuming users don't have / in their names
            delim_index = key.find("/")
            owner = key[:delim_index]
            filename = key[delim_index + 1 :]

            print(f"{filename}\t{natural_size(size)}\t{modified}\t{owner}")

    elif isinstance(cmd, GetCommand):
        if session_token is None:
            raise NotLoggedInError()

        r = requests.get(
            f"{API_BASE_URL}/file",
            headers={"x-session-token": session_token},
            params={"file_name": cmd.filename, "username": cmd.username},
        )
        r.raise_for_status()

        content = r.content
        with open(cmd.filename, "wb") as f:
            f.write(content)

    elif isinstance(cmd, ShareCommand):
        if session_token is None:
            raise NotLoggedInError()

        r = requests.post(
            f"{API_BASE_URL}/share",
            headers={"x-session-token": session_token},
            json={"file_name": cmd.filename, "username": cmd.username},
        )
        r.raise_for_status()

    elif isinstance(cmd, QuitCommand):
        if session_token is not None:
            # automatically logout upon exiting
            r = requests.post(
                f"{API_BASE_URL}/logout", headers={"x-session-token": session_token}
            )


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
            if isinstance(cmd, QuitCommand):
                break
        except NotLoggedInError:
            print_error("Not logged in")
        except HTTPError as e:
            try:
                msg = e.response.json()["message"]
            except:
                msg = str(e)
            print_error(msg)
        except BaseException as e:
            print_error(str(e))
        except:
            print("An unhandled exception occurred")


if __name__ == "__main__":
    main()
