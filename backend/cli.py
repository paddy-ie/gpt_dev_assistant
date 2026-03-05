import os
from typing import Any

import httpx
import typer

API_URL_DEFAULT = "http://127.0.0.1:8000/api"

app = typer.Typer(help="Agent3 management CLI (skeleton)")
automations_app = typer.Typer(help="Automation helpers")
runs_app = typer.Typer(help="Run helpers")

app.add_typer(automations_app, name="automations")
app.add_typer(runs_app, name="runs")


def _get_base_url() -> str:
    return os.getenv("AGENT3_API_URL", API_URL_DEFAULT).rstrip("/")


def _get_token(token_option: str | None = None) -> str:
    token = token_option or os.getenv("AGENT3_ACCESS_TOKEN")
    if not token:
        raise typer.BadParameter("Set AGENT3_ACCESS_TOKEN or pass --token")
    return token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _print_table(items: list[dict[str, Any]], columns: list[str]) -> None:
    if not items:
        typer.echo("No records found")
        return
    widths = {col: max(len(col), *(len(str(item.get(col, ""))) for item in items)) for col in columns}
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    typer.echo(header)
    typer.echo("-+-".join("-" * widths[col] for col in columns))
    for item in items:
        row = " | ".join(str(item.get(col, "")).ljust(widths[col]) for col in columns)
        typer.echo(row)


@automations_app.command("list")
def list_automations(token: str = typer.Option(None, help="Bearer token")) -> None:
    """List registered automations."""
    base_url = _get_base_url()
    auth_token = _get_token(token)
    with httpx.Client(timeout=10) as client:
        response = client.get(f"{base_url}/automations", headers=_auth_headers(auth_token))
        response.raise_for_status()
        items = response.json()
    _print_table(items, ["id", "name", "state", "updated_at", "version"])


@automations_app.command("trigger")
def trigger_automation(
    automation_id: int,
    token: str = typer.Option(None, help="Bearer token"),
    schedule: str = typer.Option(None, help="ISO datetime to schedule"),
) -> None:
    """Trigger an automation run immediately (or schedule)."""
    base_url = _get_base_url()
    auth_token = _get_token(token)
    payload: dict[str, Any] = {}
    if schedule:
        payload["scheduled_for"] = schedule
    with httpx.Client(timeout=15) as client:
        response = client.post(
            f"{base_url}/automations/{automation_id}/runs",
            headers=_auth_headers(auth_token),
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    typer.echo(f"Queued automation run {data['id']} for automation {automation_id}")


@runs_app.command("list")
def list_runs(token: str = typer.Option(None, help="Bearer token")) -> None:
    """List recent autonomous coding runs."""
    base_url = _get_base_url()
    auth_token = _get_token(token)
    with httpx.Client(timeout=10) as client:
        response = client.get(f"{base_url}/runs", headers=_auth_headers(auth_token))
        response.raise_for_status()
        items = response.json()
    _print_table(items, ["id", "repo_label", "status", "created_at", "updated_at"])


if __name__ == "__main__":
    app()
