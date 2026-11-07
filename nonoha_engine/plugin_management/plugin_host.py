from pathlib import Path
import logging
import importlib
import importlib.util
import sys
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple

from nonoha_core.node_registry import NodeRegistry

logger = logging.getLogger(__name__)


class PluginHost:
    """
    Plugin host that manages plugin loading and lifecycle.
    Supports manifest.json for plugin configuration and async finalization.
    """

    def __init__(self):
        self._loaded_plugins: Dict[str, Any] = {}  # plugin_name -> module
        self._plugin_configs: List[Dict[str, Any]] = []

    def load_builtin_plugins(
        self, builtin_plugins: Tuple[Any, ...], registry: NodeRegistry
    ) -> None:
        """
        Load builtin plugins from already imported modules.

        Args:
            builtin_plugins: Tuple of already imported plugin modules (optional)
            registry: Node registry to register plugin nodes
        """
        logger.info(f"Loading {len(builtin_plugins)} builtin plugin(s)")
        for module in builtin_plugins:
            self._load_builtin_plugin(module, registry)

    def load_plugins(
        self,
        plugin_directory: Path,
        registry: NodeRegistry,
    ) -> None:
        """
        Load plugins from directory and/or builtin modules.

        Args:
            plugin_directory: Directory containing manifest.json and plugin folders (optional)
            registry: Node registry to register plugin nodes
        """

        if not plugin_directory.exists():
            logger.info(f"Plugin directory not found: {plugin_directory}")
            return

        if not plugin_directory.is_dir():
            logger.error(f"Plugin path is not a directory: {plugin_directory}")
            return

        # Load manifest.json (required for directory-based plugins)
        manifest_path = plugin_directory / "manifest.json"

        if not manifest_path.exists():
            logger.info(
                f"No manifest.json found in {plugin_directory}, skipping directory plugin loading"
            )
            return

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                plugin_configs = manifest.get("plugins", [])

                if not plugin_configs:
                    logger.info("No plugins configured in manifest.json")
                    return

                logger.info(f"Found {len(plugin_configs)} plugin(s) in manifest.json")

                # Process each plugin in manifest
                for config in plugin_configs:
                    plugin_name = config.get("name", "")
                    if not plugin_name:
                        logger.warning(
                            f"Invalid plugin config (missing name): {config}"
                        )
                        continue

                    # Skip disabled plugins
                    if not config.get("enabled", True):
                        logger.info(f"Skipping disabled plugin: {plugin_name}")
                        continue

                    # Check if plugin directory exists
                    plugin_dir = plugin_directory / plugin_name
                    if not plugin_dir.exists():
                        logger.warning(f"Plugin directory not found: {plugin_dir}")
                        continue

                    if not plugin_dir.is_dir():
                        logger.warning(f"Plugin path is not a directory: {plugin_dir}")
                        continue

                    # Load the plugin
                    self._load_single_plugin(plugin_dir, plugin_name, registry)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in manifest.json: {e}")
            return
        except Exception as e:
            logger.error(f"Failed to process manifest.json: {e}")
            return

    def _load_builtin_plugin(self, module: Any, registry: NodeRegistry) -> None:
        """
        Load a builtin plugin from an already imported module.

        Args:
            module: Already imported plugin module
            registry: Node registry to register nodes
        """
        try:
            # Get module name for logging
            plugin_name = getattr(module, "__name__", str(module))

            # Call register_nodes function if it exists
            if hasattr(module, "register_nodes"):
                module.register_nodes(registry)

                # Store loaded plugin for lifecycle management
                self._loaded_plugins[plugin_name] = module

                logger.info(f"✓ Successfully loaded builtin plugin: {plugin_name}")
            else:
                logger.warning(
                    f"register_nodes function not found in builtin plugin: {plugin_name}"
                )

        except Exception as e:
            plugin_name = getattr(module, "__name__", str(module))
            logger.error(
                f"Failed to load builtin plugin {plugin_name}: {e}", exc_info=True
            )

    def _load_single_plugin(
        self, plugin_dir: Path, plugin_name: str, registry: NodeRegistry
    ) -> None:
        """
        Load a single plugin from directory.

        Args:
            plugin_dir: Plugin directory path
            plugin_name: Plugin name
            registry: Node registry to register nodes
        """
        try:
            # Convert plugin-name to plugin_name for Python module naming
            module_folder_name = plugin_name.replace("-", "_")

            # Check for new structure: plugin-name/plugin_name/__init__.py
            init_file = plugin_dir / module_folder_name / "__init__.py"

            if not init_file.exists():
                logger.warning(f"__init__.py not found in plugin: {plugin_name}")
                logger.warning(
                    f"Searched: {plugin_dir / module_folder_name / '__init__.py'} and {plugin_dir / '__init__.py'}"
                )
                return

            # Create isolated module name for security
            # Prevents path traversal via relative imports
            module_name = f"_plugin_{plugin_name}_{id(plugin_dir)}"

            spec = importlib.util.spec_from_file_location(module_name, init_file)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create module spec for: {plugin_name}")
                return

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module

            # Execute module
            spec.loader.exec_module(module)

            # Call register_nodes function
            if not hasattr(module, "register_nodes"):
                logger.warning(
                    f"register_nodes function not found in plugin: {plugin_name}"
                )
                return

            module.register_nodes(registry)

            # Store loaded plugin for lifecycle management
            self._loaded_plugins[plugin_name] = module

            logger.info(f"✓ Successfully loaded plugin: {plugin_name}")

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}", exc_info=True)

    async def finalize(self) -> None:
        """
        Finalize all loaded plugins.
        Calls finalize() function if available in each plugin.
        Processes plugins one by one in sequence (not in parallel).
        """
        logger.info("Finalizing plugins...")

        for plugin_name, module in self._loaded_plugins.items():
            if hasattr(module, "finalize"):
                finalize_func = getattr(module, "finalize")

                try:
                    # Check if it's a coroutine function (async)
                    if asyncio.iscoroutinefunction(finalize_func):
                        logger.debug(
                            f"Calling async finalize for plugin: {plugin_name}"
                        )
                        await finalize_func()
                        logger.debug(f"✓ Finalized plugin: {plugin_name}")
                    else:
                        # Call sync finalize directly
                        logger.debug(f"Calling sync finalize for plugin: {plugin_name}")
                        finalize_func()
                        logger.debug(f"✓ Finalized plugin: {plugin_name}")
                except Exception as e:
                    logger.error(
                        f"Error finalizing plugin {plugin_name}: {e}", exc_info=True
                    )
                    # Continue with other plugins even if one fails

        # Clear loaded plugins
        self._loaded_plugins.clear()
        logger.info("Plugin finalization complete")

    def get_loaded_plugins(self) -> List[str]:
        """
        Get list of currently loaded plugin names.

        Returns:
            List of loaded plugin names
        """
        return list(self._loaded_plugins.keys())

    def get_plugin_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all loaded plugins.

        Returns:
            List of plugin information
        """
        return [{"name": name, "loaded": True} for name in self._loaded_plugins.keys()]
