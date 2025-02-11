from base64 import b64encode
from datetime import datetime
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import lib
import typer
from typing_extensions import Annotated
from rich import print
from rich.table import Table

app = typer.Typer()


session_file = Path("~/.mydropbox-session").expanduser().resolve()


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
        if os.path.exists(session_file):
            print("[red]Error[/red]: Already logged in.")
            return
        token = lib.login(username, password)

        with open(session_file, "w") as f:
            f.write(token)
    except:
        print("[red]Error[/red]: Failed to login.")
        exit(1)


@app.command()
def logout():
    try:
        with open(session_file) as f:
            token = f.read()
        lib.logout(token)
        os.remove(session_file)
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
        with open(session_file) as f:
            token = f.read()

        lib.put_file(token, file.name, b64encode(file.read_bytes()).decode())
    except:
        print("[red]Error[/red]: Failed to add file.")
        exit(1)


@app.command()
def get(
    file: Annotated[str, typer.Argument()],
    user: Optional[str] = None,
):
    try:
        with open(session_file) as f:
            token = f.read()
        content = lib.get_file(token, file, user)
        with open(file, "wb") as f:
            f.write(content)
    except Exception:
        print("[red]Error[/red]: Failed to get file.")
        exit(1)


@app.command()
def ls():
    try:
        with open(session_file) as f:
            token = f.read()

        files: List[Dict[str, Any]] = lib.list_files(token)

        table = Table("Name", "Size", "Date Modified", "Owner")
        for file in files:
            key, size, modified = file["key"], file["size"], file["modified"]

            delim_index = key.find("/")
            owner = key[:delim_index]
            filename = key[delim_index + 1 :]

            modified = datetime.fromisoformat(modified).strftime("%Y-%m-%d %H:%M:%S")

            table.add_row(filename, str(size), modified, owner)

        print(table)
    except Exception:
        print("[red]Error[/red]: Failed to list files.")
        exit(1)


@app.command()
def share(
    file: Annotated[str, typer.Argument()],
    username: Annotated[str, typer.Argument()],
):
    try:
        with open(session_file) as f:
            token = f.read()

        lib.share_file(token, file, username)
    except:
        print("[red]Error[/red]: Failed to share file.")
        exit(1)


if __name__ == "__main__":
    app()
