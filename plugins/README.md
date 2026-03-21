# Bruce AI Plugins

## Creating a Plugin

1. Create a new `.py` file in this `plugins/` directory.
2. Import and subclass `BrucePlugin`:

```python
from modules.plugin_system import BrucePlugin

class MyPlugin(BrucePlugin):
    name = "my_plugin"           # Unique identifier
    version = "1.0.0"
    description = "What it does"
    author = "Your Name"

    def on_load(self, bruce) -> None:
        """Called when the plugin is loaded. 'bruce' is the agent instance."""
        self.bruce = bruce

    def on_unload(self) -> None:
        """Called when the plugin is unloaded. Clean up resources."""
        pass
```

## Adding Tools

Tools are functions that Bruce (and the MCP server) can call:

```python
def get_tools(self) -> list:
    return [
        {
            "name": "my_tool_name",
            "fn": self._my_function,
            "description": "What this tool does",
            "parameters": {"param1": "Description of param1"},
        }
    ]

def _my_function(self, param1: str) -> str:
    return f"Result: {param1}"
```

## Adding CLI Commands

Commands are available in the interactive CLI with the `/` prefix:

```python
def get_commands(self) -> dict:
    return {
        "mycommand": {
            "fn": self._cmd_handler,
            "description": "Help text shown in /help",
        }
    }

def _cmd_handler(self, arg: str) -> None:
    print(f"You said: {arg}")
```

## Lifecycle Hooks

Override any of these methods to hook into Bruce's events:

| Hook                         | When it fires                     |
|------------------------------|-----------------------------------|
| `on_message(message)`        | Every user message                |
| `on_trade(trade_data)`       | Every trade execution             |
| `on_alert(alert_data)`       | Every alert                       |
| `on_learn(knowledge)`        | When Bruce learns something       |
| `on_startup()`               | When Bruce starts                 |
| `on_shutdown()`              | When Bruce stops                  |

## Error Isolation

Each plugin runs in isolation. If your plugin raises an exception:
- Other plugins continue working normally.
- The error is logged but does not crash Bruce.
- The plugin remains loaded (hooks that fail are skipped).

## Plugin Discovery

Any `.py` file in this directory (except `__init__.py` and files starting
with `_`) is automatically discovered. The file must contain at least one
class that inherits from `BrucePlugin`.

## Managing Plugins at Runtime

From the CLI:
- `/plugins` -- list all loaded plugins
- `/plugins load <name>` -- load a specific plugin
- `/plugins unload <name>` -- unload a plugin
- `/plugins reload <name>` -- hot-reload a plugin

From the MCP server:
- `manage_plugins(action="list")` -- list plugins
- `manage_plugins(action="load")` -- load all or a specific plugin
- `manage_plugins(action="reload", name="...")` -- hot-reload

## Example

See `example_plugin.py` in this directory for a complete working example
that demonstrates tools, commands, hooks, and lifecycle methods.
