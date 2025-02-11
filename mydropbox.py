import os
from base64 import b64encode
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated

import lib
from constants import SESSION_FILE_PATH

app = typer.Typer()


@app.command()
def register(
    username: Annotated[str, typer.Option(prompt=True)],
    password: Annotated[
        str, typer.Option(prompt=True, confirmation_prompt=True, hide_input=True)
    ],
):
    try:
        lib.register(username, password)
    except:
        print("[red]Error[/red]: Failed to register user.")
        exit(1)


@app.command()
def login(
    username: Annotated[str, typer.Option(prompt=True)],
    password: Annotated[str, typer.Option(prompt=True, hide_input=True)],
):
    try:
        if os.path.exists(SESSION_FILE_PATH):
            print("[red]Error[/red]: Already logged in.")
            return
        token = lib.login(username, password)

        with open(SESSION_FILE_PATH, "w") as f:
            f.write(token)
    except:
        print("[red]Error[/red]: Failed to login.")
        exit(1)


@app.command()
def logout():
    try:
        token = lib.retrieve_token()

        lib.logout(token)
        os.remove(SESSION_FILE_PATH)
    except lib.NotLoggedInError:
        print("[red]Error[/red]: Not logged in.")
    except:
        print("[red]Error[/red]: Failed to logout.")
        exit(1)


@app.command()
def add(
    file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ]
):
    try:
        token = lib.retrieve_token()

        lib.put_file(token, file.name, b64encode(file.read_bytes()).decode())
    except lib.NotLoggedInError:
        print("[red]Error[/red]: Not logged in.")
    except:
        print("[red]Error[/red]: Failed to add file.")
        exit(1)


@app.command()
def get(
    file: Annotated[str, typer.Argument()],
    user: Optional[str] = None,
):
    try:
        token = lib.retrieve_token()

        content = lib.get_file(token, file, user)
        with open(file, "wb") as f:
            f.write(content)
    except lib.NotLoggedInError:
        print("[red]Error[/red]: Not logged in.")
    except Exception:
        print("[red]Error[/red]: Failed to get file.")
        exit(1)


@app.command()
def ls():
    try:
        token = lib.retrieve_token()

        files: List[Dict[str, Any]] = lib.list_files(token)

        table = Table("Name", "Size", "Date Modified", "Owner")
        for file in files:
            key, size, modified = file["key"], file["size"], file["modified"]

            delim_index = key.find("/")
            owner = key[:delim_index]
            filename = key[delim_index + 1 :]

            modified = datetime.fromisoformat(modified).strftime("%Y-%m-%d %H:%M:%S")

            table.add_row(filename, lib.natural_size(size), modified, owner)

        print(table)
    except lib.NotLoggedInError:
        print("[red]Error[/red]: Not logged in.")
    except Exception:
        print("[red]Error[/red]: Failed to list files.")
        exit(1)


@app.command()
def share(
    file: Annotated[str, typer.Argument()],
    username: Annotated[str, typer.Argument()],
):
    try:
        token = lib.retrieve_token()

        lib.share_file(token, file, username)
    except lib.NotLoggedInError:
        print("[red]Error[/red]: Not logged in.")
    except:
        print("[red]Error[/red]: Failed to share file.")
        exit(1)


if __name__ == "__main__":
    app()
