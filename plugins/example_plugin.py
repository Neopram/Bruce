"""
Example Plugin for Bruce AI
============================
Demonstrates the plugin API:
  - Adding a CLI command (/hello)
  - Adding a tool (hello_world)
  - Hooking into on_message to log all messages
  - Hooking into on_startup / on_shutdown

Use this as a template for your own plugins.
"""

import logging
import os
from datetime import datetime, timezone

from modules.plugin_system import BrucePlugin

logger = logging.getLogger("Bruce.Plugins.Example")

# Log file location (relative to project root)
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "plugin_logs")


class ExamplePlugin(BrucePlugin):
    """A working example plugin that shows all plugin capabilities."""

    name = "example_plugin"
    version = "1.0.0"
    description = "Example plugin: /hello command, hello_world tool, message logger"
    author = "Bruce AI"

    def __init__(self):
        self.bruce = None
        self._log_file = None
        self._message_count = 0

    # ---- Lifecycle ----

    def on_load(self, bruce) -> None:
        """Initialize the plugin. Opens the message log file."""
        self.bruce = bruce

        # Ensure log directory exists
        os.makedirs(LOG_DIR, exist_ok=True)
        self._log_path = os.path.join(LOG_DIR, "messages.log")
        self._log_file = open(self._log_path, "a", encoding="utf-8")

        logger.info(f"ExamplePlugin loaded. Logging messages to {self._log_path}")

    def on_unload(self) -> None:
        """Clean up: close the log file."""
        if self._log_file and not self._log_file.closed:
            self._log_file.close()
        logger.info("ExamplePlugin unloaded.")

    # ---- Tools ----

    def get_tools(self) -> list:
        """Provide the hello_world tool."""
        return [
            {
                "name": "hello_world",
                "fn": self._tool_hello_world,
                "description": "A friendly greeting tool from the example plugin. "
                               "Optionally takes a name to greet.",
                "parameters": {
                    "name": "Name to greet (optional, defaults to 'World')",
                },
            },
        ]

    def _tool_hello_world(self, name: str = "World") -> str:
        """The hello_world tool implementation."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return (
            f"Hello, {name}! This is the example plugin for Bruce AI. "
            f"Current time: {timestamp}. "
            f"Messages logged this session: {self._message_count}."
        )

    # ---- CLI Commands ----

    def get_commands(self) -> dict:
        """Provide the /hello command."""
        return {
            "hello": {
                "fn": self._cmd_hello,
                "description": "Say hello (example plugin)",
            },
        }

    def _cmd_hello(self, arg: str) -> None:
        """Handle the /hello command."""
        name = arg.strip() if arg.strip() else "Federico"
        print(f"\033[36m  [ExamplePlugin] Hello, {name}!\033[0m")
        print(f"\033[90m  Messages logged this session: {self._message_count}\033[0m")
        print(f"\033[90m  Log file: {self._log_path}\033[0m")

    # ---- Hooks ----

    def on_message(self, message: str) -> None:
        """Log every user message to a file."""
        self._message_count += 1
        timestamp = datetime.now(timezone.utc).isoformat()
        if self._log_file and not self._log_file.closed:
            self._log_file.write(f"[{timestamp}] {message}\n")
            self._log_file.flush()

    def on_startup(self) -> None:
        """Called when Bruce starts."""
        timestamp = datetime.now(timezone.utc).isoformat()
        if self._log_file and not self._log_file.closed:
            self._log_file.write(f"[{timestamp}] === Bruce started ===\n")
            self._log_file.flush()
        logger.info("ExamplePlugin: Bruce startup detected.")

    def on_shutdown(self) -> None:
        """Called when Bruce shuts down."""
        timestamp = datetime.now(timezone.utc).isoformat()
        if self._log_file and not self._log_file.closed:
            self._log_file.write(f"[{timestamp}] === Bruce shutdown ===\n")
            self._log_file.flush()
        logger.info("ExamplePlugin: Bruce shutdown detected.")
