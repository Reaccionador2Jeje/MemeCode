"""Textual terminal interface for MemeCode."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, Static

try:
    from . import agent
except ImportError:
    import agent


class ApprovalScreen(ModalScreen[bool]):
    CSS = """
    ApprovalScreen { align: center middle; }
    #approval-box { width: 92%; max-width: 72; height: 82%; border: round $warning; padding: 1 2; background: $surface; }
    #approval-details { height: 1fr; }
    #approval-actions { height: 3; align-horizontal: right; }
    """

    def __init__(self, prompt: str) -> None:
        super().__init__()
        self.prompt = prompt

    def compose(self) -> ComposeResult:
        with Container(id="approval-box"):
            yield Label("MemeCode necesita tu autorización")
            with VerticalScroll(id="approval-details"):
                yield Static(self.prompt, markup=False)
            with Horizontal(id="approval-actions"):
                yield Button("Rechazar", id="deny")
                yield Button("Aprobar", id="approve", variant="success")

    @on(Button.Pressed)
    def choose(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "approve")


class ProviderScreen(ModalScreen[dict[str, str] | None]):
    CSS = """
    ProviderScreen { align: center middle; }
    #provider-box { width: 92%; max-width: 70; height: auto; border: round $accent; padding: 1 2; background: $surface; }
    #provider-actions { height: 3; align-horizontal: right; }
    """

    def __init__(self) -> None:
        super().__init__()
        self.values = agent._read_config(agent.config_file())

    def compose(self) -> ComposeResult:
        with Container(id="provider-box"):
            yield Label("Configuración del proveedor (opcional)")
            yield Static("El protocolo se detecta automáticamente según la URL: OpenAI-compatible, Anthropic o Gemini. Usa /test después de guardar.")
            yield Label("Modelo")
            yield Input(value=self.values.get("MEMECODE_MODEL", "gpt-4o-mini"), id="model")
            yield Label("API base URL (detección automática)")
            yield Input(value=self.values.get("MEMECODE_BASE_URL", agent.DEFAULT_BASE_URL), id="base-url")
            yield Label("API key (entrada oculta)")
            yield Input(value=self.values.get("MEMECODE_API_KEY", ""), password=True, id="api-key")
            with Horizontal(id="provider-actions"):
                yield Button("Cancelar", id="cancel")
                yield Button("Guardar", id="save", variant="primary")

    @on(Button.Pressed)
    def choose(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        model = self.query_one("#model", Input).value.strip()
        base_url = self.query_one("#base-url", Input).value.strip()
        key = self.query_one("#api-key", Input).value.strip()
        if not model or any(char.isspace() for char in model):
            self.app.notify("El modelo no puede estar vacío ni contener espacios.", severity="error")
            return
        if not base_url.startswith(("https://", "http://")):
            self.app.notify("La URL debe comenzar con https:// o http://.", severity="error")
            return
        self.dismiss({
            "MEMECODE_MODEL": model,
            "MEMECODE_BASE_URL": base_url.rstrip("/"),
            "MEMECODE_API_KEY": key,
        })


class MemeCodeApp(App[None]):
    TITLE = "MemeCode"
    SUB_TITLE = "Coding Agent"
    BINDINGS = [("ctrl+c", "quit", "Salir"), ("ctrl+l", "clear_chat", "Limpiar")]
    CSS = """
    Screen { background: $background; }
    #messages { height: 1fr; padding: 1 2; }
    .message { width: 100%; height: auto; margin-bottom: 1; padding: 1 2; border: round $primary-background; }
    .user-message { border-left: solid $success; }
    .agent-message { border-left: solid $accent; }
    .system-message { border-left: solid $warning; color: $text-muted; }
    #prompt { dock: bottom; margin: 0 1 1 1; }
    """

    def __init__(self, workspace: str = ".") -> None:
        super().__init__()
        self.workspace = workspace
        self.busy = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(id="messages")
        yield Input(placeholder="Escribe una tarea…  (/setup, /test, /help, /exit)", id="prompt")
        yield Footer()

    def on_mount(self) -> None:
        self.write_message("Sistema", f"Workspace: {Path(self.workspace).expanduser().resolve()}", "system-message")
        settings = agent.provider_settings(interactive=False)
        if settings.get("MEMECODE_API_KEY"):
            self.write_message("Sistema", "Proveedor configurado. ¡Listo para trabajar!", "system-message")
        else:
            self.write_message("Sistema", "No hay proveedor configurado. Usa /setup para añadir uno; la configuración no es necesaria para abrir MemeCode.", "system-message")
        self.query_one("#prompt", Input).focus()

    def write_message(self, author: str, message: str, css_class: str) -> None:
        panel = self.query_one("#messages", VerticalScroll)
        panel.mount(Static(f"{author}\n{message}", classes=f"message {css_class}", markup=False))
        panel.scroll_end(animate=False)

    @on(Input.Submitted, "#prompt")
    async def submit_prompt(self, event: Input.Submitted) -> None:
        task = event.value.strip()
        event.input.value = ""
        if not task:
            return
        if task.lower() in {"/exit", "/quit"}:
            self.exit()
            return
        if task.lower() == "/help":
            self.write_message("Sistema", "Escribe una tarea para el agente. /setup configura el proveedor, /test comprueba la conexión, /clear limpia el chat y /exit sale.", "system-message")
            return
        if task.lower() == "/clear":
            await self.query_one("#messages", VerticalScroll).remove_children()
            return
        if task.lower() == "/setup":
            self.push_screen(ProviderScreen(), self.save_provider)
            return
        if task.lower() == "/test":
            if self.busy:
                self.notify("Espera a que termine la tarea actual.", severity="warning")
                return
            settings = agent.provider_settings(interactive=False)
            if not settings.get("MEMECODE_API_KEY"):
                self.write_message("Sistema", "Primero configura el proveedor con /setup.", "system-message")
                return
            self.write_message("Sistema", "Probando conexión, autenticación y respuesta del modelo…", "system-message")
            self.busy = True
            self.query_one("#prompt", Input).disabled = True
            self.test_provider(settings)
            return
        if self.busy:
            self.notify("Espera a que termine la tarea actual.", severity="warning")
            return
        settings = agent.provider_settings(interactive=False)
        if not settings.get("MEMECODE_API_KEY"):
            self.write_message("Sistema", "Falta una API key. Usa /setup para configurarla. La instalación y la TUI funcionan sin ella.", "system-message")
            return
        self.write_message("Tú", task, "user-message")
        self.busy = True
        self.query_one("#prompt", Input).disabled = True
        self.run_task(task, settings)

    def save_provider(self, values: dict[str, str] | None) -> None:
        if values is None:
            return
        try:
            agent._write_config(agent.config_file(), values)
            self.write_message("Sistema", "Configuración guardada de forma privada.", "system-message")
        except OSError as exc:
            self.notify(f"No se pudo guardar: {exc}", severity="error")

    def _show_approval(self, prompt: str, event: threading.Event, decision: dict[str, bool]) -> None:
        def finished(value: bool) -> None:
            decision["approved"] = bool(value)
            event.set()
        self.push_screen(ApprovalScreen(prompt), finished)

    def request_approval(self, prompt: str) -> bool:
        event = threading.Event()
        decision: dict[str, bool] = {"approved": False}
        self.call_from_thread(self._show_approval, prompt, event, decision)
        event.wait()
        return decision["approved"]

    @work(thread=True, exclusive=True)
    def run_task(self, task: str, settings: dict[str, str]) -> None:
        try:
            root = agent.workspace_root(self.workspace)
            memecode_root = Path(agent.__file__).resolve().parents[1]
            core = agent.load_memingo_core(memecode_root)
            system_prompt = agent.build_system_prompt(core)
            answer = agent.run_agent(
                task, root,
                api_key=settings["MEMECODE_API_KEY"],
                model=settings["MEMECODE_MODEL"],
                base_url=settings["MEMECODE_BASE_URL"],
                system_prompt=system_prompt,
                approval_fn=self.request_approval,
                output_fn=self.report_output,
            )
            self.call_from_thread(self.write_message, "MemeCode", answer or "(Sin respuesta)", "agent-message")
        except Exception as exc:
            self.call_from_thread(self.write_message, "Error", str(exc), "system-message")
        finally:
            self.call_from_thread(self._task_finished)

    @work(thread=True, exclusive=True)
    def test_provider(self, settings: dict[str, str]) -> None:
        try:
            message = agent.provider_request(
                [{"role": "user", "content": "Responde exactamente: MemeCode conectado."}],
                api_key=settings["MEMECODE_API_KEY"],
                model=settings["MEMECODE_MODEL"],
                base_url=settings["MEMECODE_BASE_URL"],
                tools_enabled=False,
            )
            answer = agent._response_text(message.get("content"))
            if not answer:
                raise agent.AgentError("El proveedor respondió sin texto.")
            self.call_from_thread(
                self.write_message, "Prueba de conexión",
                f"Conexión correcta. Modelo: {settings['MEMECODE_MODEL']}\nRespuesta: {answer}",
                "system-message",
            )
        except Exception as exc:
            self.call_from_thread(self.write_message, "Prueba de conexión fallida", str(exc), "system-message")
        finally:
            self.call_from_thread(self._task_finished)

    def report_output(self, message: str) -> None:
        self.call_from_thread(self.write_message, "Salida de comando", message, "system-message")

    def _task_finished(self) -> None:
        self.busy = False
        self.query_one("#prompt", Input).disabled = False
        self.query_one("#prompt", Input).focus()

    async def action_clear_chat(self) -> None:
        await self.query_one("#messages", VerticalScroll).remove_children()


def run_tui(workspace: str = ".") -> int:
    MemeCodeApp(workspace).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tui())
