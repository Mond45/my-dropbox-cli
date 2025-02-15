from base64 import b64encode
from datetime import datetime
from pathlib import Path

import requests
import typer
from requests import HTTPError
from rich import print
from rich.table import Table
from typing_extensions import Annotated

API_BASE_URL = "https://b6cdy6h1yg.execute-api.ap-southeast-1.amazonaws.com/stage"


def natural_size(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


app = typer.Typer()


@app.command()
def put(
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
        r = requests.put(
            f"{API_BASE_URL}/file",
            json={
                "file_name": file.name,
                "content": b64encode(file.read_bytes()).decode(),
            },
        )
        r.raise_for_status()
    except HTTPError as e:
        print(f"[red]Error[/red]: {e.response.json()['message']}")
        exit(1)


@app.command()
def get(
    file: Annotated[str, typer.Argument()],
):
    try:
        r = requests.get(
            f"{API_BASE_URL}/file",
            params={"file_name": file},
        )
        r.raise_for_status()

        content = r.content
        with open(file, "wb") as f:
            f.write(content)
    except HTTPError as e:
        print(f"[red]Error[/red]: {e.response.json()['message']}")
        exit(1)


@app.command()
def view():
    try:
        r = requests.get(f"{API_BASE_URL}/files")
        r.raise_for_status()
        files = r.json()

        table = Table("Name", "Size", "Date Modified", "Owner")
        for file in files:
            key, size, modified = file["key"], file["size"], file["modified"]

            delim_index = key.find("/")
            owner = key[:delim_index]
            filename = key[delim_index + 1 :]

            modified = datetime.fromisoformat(modified).strftime("%Y-%m-%d %H:%M:%S")

            table.add_row(filename, natural_size(size), modified, owner)

        print(table)
    except HTTPError as e:
        print(f"[red]Error[/red]: {e.response.json()['message']}")
        exit(1)


if __name__ == "__main__":
    app()
