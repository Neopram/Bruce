"""
Bruce AI -- Plugin System
=========================
Extensible plugin architecture for Bruce AI.
Allows third-party and custom plugins to add tools, commands,
and hook into Bruce's lifecycle events.

Usage:
    from modules.plugin_system import get_plugin_manager
    pm = get_plugin_manager()
    pm.load_all()
    pm.list_plugins()
"""

import importlib
import importlib.util
import inspect
import logging
import os
import sys
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("Bruce.Plugins")

# Project root and default plugins directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = PROJECT_ROOT / "plugins"


# ============================================================
#  Plugin Base Class
# ============================================================

class BrucePlugin(ABC):
    """Base class for all Bruce AI plugins.

    Subclass this to create a plugin. At minimum, set the class
    attributes (name, version, description, author) and implement
    on_load().

    Example::

        class MyPlugin(BrucePlugin):
            name = "my_plugin"
            version = "1.0.0"
            description = "Does something useful"
            author = "Federico"

            def on_load(self, bruce):
                self.bruce = bruce

            def get_tools(self):
                return [
                    {
                        "name": "my_tool",
                        "fn": self._my_tool,
                        "description": "Does the thing",
                        "parameters": {"arg": "An argument"},
                    }
                ]

            def _my_tool(self, arg: str) -> str:
                return f"Result: {arg}"
    """

    name: str = "unnamed_plugin"
    version: str = "0.0.1"
    description: str = ""
    author: str = "Unknown"

    # Set to True by the manager after successful on_load()
    _loaded: bool = False
    _load_error: Optional[str] = None
    _loaded_at: Optional[str] = None

    @abstractmethod
    def on_load(self, bruce) -> None:
        """Called when the plugin is loaded. Receive a reference to Bruce.

        Args:
            bruce: The Bruce agent instance (or None if unavailable).
        """
        ...

    def on_unload(self) -> None:
        """Called when the plugin is unloaded. Clean up resources here."""
        pass

    def get_tools(self) -> List[dict]:
        """Return a list of tool definitions this plugin provides.

        Each tool dict should have:
            - name (str): tool name
            - fn (callable): the function to call
            - description (str): what the tool does
            - parameters (dict): parameter name -> description mapping

        Returns:
            List of tool dicts.
        """
        return []

    def get_commands(self) -> Dict[str, dict]:
        """Return CLI commands this plugin adds.

        Returns a dict mapping command name (without /) to a dict with:
            - fn (callable): function(arg: str) -> None
            - description (str): help text

        Example::

            return {
                "hello": {
                    "fn": self._cmd_hello,
                    "description": "Say hello",
                }
            }
        """
        return {}

    # ----- Hook methods (override as needed) -----

    def on_message(self, message: str) -> None:
        """Called on every user message."""
        pass

    def on_trade(self, trade_data: dict) -> None:
        """Called on every trade execution."""
        pass

    def on_alert(self, alert_data: dict) -> None:
        """Called on every alert."""
        pass

    def on_learn(self, knowledge: dict) -> None:
        """Called when Bruce learns something new."""
        pass

    def on_startup(self) -> None:
        """Called when Bruce starts up."""
        pass

    def on_shutdown(self) -> None:
        """Called when Bruce shuts down."""
        pass

    # ----- Internal helpers -----

    def __repr__(self):
        status = "loaded" if self._loaded else "not loaded"
        return f"<BrucePlugin '{self.name}' v{self.version} [{status}]>"


# ============================================================
#  Plugin Manager
# ============================================================

class PluginManager:
    """Discovers, loads, and manages Bruce AI plugins.

    Plugins are Python files in the plugins/ directory that contain
    at least one class inheriting from BrucePlugin.
    """

    def __init__(self, plugins_dir: Optional[str] = None, bruce=None):
        """
        Args:
            plugins_dir: Path to the plugins directory. Defaults to <project>/plugins/.
            bruce: Reference to the Bruce agent instance.
        """
        self.plugins_dir = Path(plugins_dir) if plugins_dir else PLUGINS_DIR
        self.bruce = bruce
        self._plugins: Dict[str, BrucePlugin] = {}
        self._module_cache: Dict[str, Any] = {}
        self._hooks: Dict[str, List[Callable]] = {
            "on_message": [],
            "on_trade": [],
            "on_alert": [],
            "on_learn": [],
            "on_startup": [],
            "on_shutdown": [],
        }

    # ---- Discovery ----

    def discover(self) -> List[str]:
        """Scan the plugins directory for Python plugin files.

        Returns:
            List of file paths to discovered plugin files.
        """
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return []

        plugin_files = []
        for f in sorted(self.plugins_dir.iterdir()):
            if f.suffix == ".py" and f.name != "__init__.py" and not f.name.startswith("_"):
                plugin_files.append(str(f))

        logger.info(f"Discovered {len(plugin_files)} plugin file(s) in {self.plugins_dir}")
        return plugin_files

    # ---- Loading ----

    def load_plugin(self, path: str) -> Optional[BrucePlugin]:
        """Load a single plugin from a file path.

        The file is imported as a module. The first class found that
        inherits from BrucePlugin is instantiated and loaded.

        Args:
            path: Absolute or relative path to the plugin .py file.

        Returns:
            The loaded BrucePlugin instance, or None on failure.
        """
        path = str(Path(path).resolve())
        module_name = Path(path).stem

        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(
                f"bruce_plugins.{module_name}", path
            )
            if spec is None or spec.loader is None:
                logger.error(f"Cannot load plugin spec from {path}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[f"bruce_plugins.{module_name}"] = module
            spec.loader.exec_module(module)

            # Find the plugin class
            plugin_cls = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    inspect.isclass(attr)
                    and issubclass(attr, BrucePlugin)
                    and attr is not BrucePlugin
                ):
                    plugin_cls = attr
                    break

            if plugin_cls is None:
                logger.warning(f"No BrucePlugin subclass found in {path}")
                return None

            # Instantiate and load
            plugin = plugin_cls()

            # Check for name conflicts
            if plugin.name in self._plugins:
                logger.warning(
                    f"Plugin '{plugin.name}' already loaded. "
                    f"Unload it first or use reload_plugin()."
                )
                return None

            # Call on_load with error isolation
            try:
                plugin.on_load(self.bruce)
                plugin._loaded = True
                plugin._loaded_at = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                plugin._loaded = False
                plugin._load_error = str(e)
                logger.error(
                    f"Plugin '{plugin.name}' on_load() failed: {e}\n"
                    f"{traceback.format_exc()}"
                )
                return None

            # Register the plugin
            self._plugins[plugin.name] = plugin
            self._module_cache[plugin.name] = {
                "module": module,
                "path": path,
                "spec": spec,
            }

            # Register hooks
            self._register_hooks(plugin)

            logger.info(
                f"Loaded plugin: {plugin.name} v{plugin.version} "
                f"by {plugin.author}"
            )
            return plugin

        except Exception as e:
            logger.error(
                f"Failed to load plugin from {path}: {e}\n"
                f"{traceback.format_exc()}"
            )
            return None

    def load_all(self) -> Dict[str, bool]:
        """Discover and load all plugins from the plugins directory.

        Returns:
            Dict mapping plugin file name to success boolean.
        """
        results = {}
        for path in self.discover():
            name = Path(path).stem
            plugin = self.load_plugin(path)
            results[name] = plugin is not None
        return results

    # ---- Unloading ----

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin by name.

        Calls the plugin's on_unload() and removes it from the registry.

        Args:
            name: Plugin name.

        Returns:
            True if successfully unloaded.
        """
        if name not in self._plugins:
            logger.warning(f"Plugin '{name}' is not loaded")
            return False

        plugin = self._plugins[name]

        # Call on_unload with error isolation
        try:
            plugin.on_unload()
        except Exception as e:
            logger.error(f"Plugin '{name}' on_unload() error: {e}")

        # Remove hooks
        self._unregister_hooks(plugin)

        # Remove from registries
        plugin._loaded = False
        del self._plugins[name]

        # Clean up module from sys.modules
        module_key = f"bruce_plugins.{name}"
        if module_key in sys.modules:
            del sys.modules[module_key]

        if name in self._module_cache:
            del self._module_cache[name]

        logger.info(f"Unloaded plugin: {name}")
        return True

    # ---- Reload ----

    def reload_plugin(self, name: str) -> Optional[BrucePlugin]:
        """Hot-reload a plugin by name.

        Unloads the current instance and re-loads from the original file.

        Args:
            name: Plugin name.

        Returns:
            The reloaded BrucePlugin instance, or None on failure.
        """
        if name not in self._plugins:
            logger.warning(f"Plugin '{name}' is not loaded, cannot reload")
            return None

        cached = self._module_cache.get(name)
        if not cached:
            logger.error(f"No cached module path for plugin '{name}'")
            return None

        path = cached["path"]
        self.unload_plugin(name)
        return self.load_plugin(path)

    # ---- Query ----

    def get_plugin(self, name: str) -> Optional[BrucePlugin]:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> List[dict]:
        """List all loaded plugins with their status.

        Returns:
            List of plugin info dicts.
        """
        result = []
        for name, plugin in self._plugins.items():
            tools = []
            commands = []
            try:
                tools = [t.get("name", "?") for t in plugin.get_tools()]
            except Exception:
                pass
            try:
                commands = list(plugin.get_commands().keys())
            except Exception:
                pass

            result.append({
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
                "loaded": plugin._loaded,
                "loaded_at": plugin._loaded_at,
                "error": plugin._load_error,
                "tools": tools,
                "commands": commands,
            })
        return result

    @property
    def loaded_count(self) -> int:
        """Number of currently loaded plugins."""
        return len(self._plugins)

    # ---- Tools & Commands ----

    def get_all_tools(self) -> List[dict]:
        """Collect tools from all loaded plugins.

        Returns:
            List of tool dicts (name, fn, description, parameters).
        """
        all_tools = []
        for name, plugin in self._plugins.items():
            try:
                tools = plugin.get_tools()
                for tool in tools:
                    # Tag tools with their source plugin
                    tool["source_plugin"] = name
                    all_tools.append(tool)
            except Exception as e:
                logger.error(f"Error getting tools from plugin '{name}': {e}")
        return all_tools

    def get_all_commands(self) -> Dict[str, dict]:
        """Collect CLI commands from all loaded plugins.

        Returns:
            Dict mapping command name to command dict.
        """
        all_cmds = {}
        for name, plugin in self._plugins.items():
            try:
                cmds = plugin.get_commands()
                for cmd_name, cmd_info in cmds.items():
                    cmd_info["source_plugin"] = name
                    all_cmds[cmd_name] = cmd_info
            except Exception as e:
                logger.error(f"Error getting commands from plugin '{name}': {e}")
        return all_cmds

    def register_tools_to_registry(self, registry) -> int:
        """Register all plugin tools into a ToolRegistry.

        Args:
            registry: A ToolRegistry instance (from tools.py).

        Returns:
            Number of tools registered.
        """
        count = 0
        for tool in self.get_all_tools():
            try:
                registry.register(
                    name=tool["name"],
                    fn=tool["fn"],
                    description=tool.get("description", ""),
                    parameters=tool.get("parameters", {}),
                )
                count += 1
                logger.info(
                    f"Registered plugin tool: {tool['name']} "
                    f"(from {tool.get('source_plugin', '?')})"
                )
            except Exception as e:
                logger.error(f"Failed to register tool '{tool.get('name')}': {e}")
        return count

    # ---- Hooks ----

    def _register_hooks(self, plugin: BrucePlugin) -> None:
        """Register a plugin's hook methods."""
        for hook_name in self._hooks:
            method = getattr(plugin, hook_name, None)
            if method and callable(method):
                # Only register if the plugin has overridden the default
                base_method = getattr(BrucePlugin, hook_name, None)
                if base_method is None or method.__func__ is not base_method:
                    self._hooks[hook_name].append(method)

    def _unregister_hooks(self, plugin: BrucePlugin) -> None:
        """Remove a plugin's hook methods."""
        for hook_name in self._hooks:
            self._hooks[hook_name] = [
                h for h in self._hooks[hook_name]
                if not (hasattr(h, "__self__") and h.__self__ is plugin)
            ]

    def fire_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Fire a hook, calling all registered handlers.

        Errors in individual handlers are caught and logged so one
        bad plugin does not crash Bruce.

        Args:
            hook_name: Name of the hook (e.g. "on_message").
            *args, **kwargs: Arguments to pass to each handler.

        Returns:
            List of return values from handlers (None for errors).
        """
        if hook_name not in self._hooks:
            logger.warning(f"Unknown hook: {hook_name}")
            return []

        results = []
        for handler in self._hooks[hook_name]:
            try:
                result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                plugin_name = "unknown"
                if hasattr(handler, "__self__"):
                    plugin_name = getattr(handler.__self__, "name", "unknown")
                logger.error(
                    f"Hook '{hook_name}' error in plugin '{plugin_name}': {e}\n"
                    f"{traceback.format_exc()}"
                )
                results.append(None)
        return results

    # Convenience methods for common hooks

    def fire_on_message(self, message: str) -> None:
        """Fire the on_message hook."""
        self.fire_hook("on_message", message)

    def fire_on_trade(self, trade_data: dict) -> None:
        """Fire the on_trade hook."""
        self.fire_hook("on_trade", trade_data)

    def fire_on_alert(self, alert_data: dict) -> None:
        """Fire the on_alert hook."""
        self.fire_hook("on_alert", alert_data)

    def fire_on_learn(self, knowledge: dict) -> None:
        """Fire the on_learn hook."""
        self.fire_hook("on_learn", knowledge)

    def fire_on_startup(self) -> None:
        """Fire the on_startup hook."""
        self.fire_hook("on_startup")

    def fire_on_shutdown(self) -> None:
        """Fire the on_shutdown hook."""
        self.fire_hook("on_shutdown")


# ============================================================
#  Singleton
# ============================================================

_manager: Optional[PluginManager] = None


def get_plugin_manager(bruce=None, plugins_dir: Optional[str] = None) -> PluginManager:
    """Get or create the global PluginManager singleton.

    Args:
        bruce: Bruce agent instance (optional, set once).
        plugins_dir: Override the plugins directory path.

    Returns:
        The PluginManager instance.
    """
    global _manager
    if _manager is None:
        _manager = PluginManager(plugins_dir=plugins_dir, bruce=bruce)
    elif bruce is not None and _manager.bruce is None:
        _manager.bruce = bruce
    return _manager
