"""
Connector factory for AI Job Hunter.

Uses registration pattern to avoid if/elif chains.
New connectors register themselves, keeping the factory open for extension.
"""

from __future__ import annotations

import importlib
import inspect
import logging
from pathlib import Path
from typing import Any, TypeVar

from jobs.base import BaseConnector
from jobs.enums import ConnectorType, Portal
from jobs.registry.connector_registry import get_connector_info

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ConnectorFactory:
    """
    Factory for creating connector instances.

    Connectors register themselves with the factory.
    No if/elif chains - the factory uses a registry.
    """

    _registry: dict[tuple[Portal, ConnectorType], type] = {}

    @classmethod
    def discover(cls) -> None:
        """
        Discover connector implementations automatically.

        Connector modules own their implementation and metadata.
        The generic factory does not contain portal-specific logic.
        """
        connectors_root = (
            Path(__file__).resolve().parents[1] / "connectors"
        )

        for connector_file in connectors_root.glob("*/connector.py"):
            module_name = (
                f"jobs.connectors."
                f"{connector_file.parent.name}.connector"
            )

            try:
                module = importlib.import_module(module_name)
            except Exception as exc:
                logger.warning(
                    "Unable to load connector module %s: %s",
                    module_name,
                    exc,
                )
                continue

            for _, connector_class in inspect.getmembers(
                module,
                inspect.isclass,
            ):
                if (
                    connector_class is BaseConnector
                    or not issubclass(
                        connector_class,
                        BaseConnector,
                    )
                ):
                    continue

                portal = getattr(
                    connector_class,
                    "PORTAL",
                    Portal.UNKNOWN,
                )

                connector_type = getattr(
                    connector_class,
                    "CONNECTOR_TYPE",
                    ConnectorType.UNKNOWN,
                )

                if (
                    portal == Portal.UNKNOWN
                    or connector_type == ConnectorType.UNKNOWN
                ):
                    continue

                cls.register(
                    portal=portal,
                    connector_type=connector_type,
                    connector_class=connector_class,
                )

    @classmethod
    def register(
        cls,
        portal: Portal,
        connector_type: ConnectorType,
        connector_class: type,
    ) -> None:
        """
        Register a connector class with the factory.

        Args:
            portal: The portal this connector works with.
            connector_type: The type of connector.
            connector_class: The connector class (must have a VERSION attribute).
        """
        cls._registry[(portal, connector_type)] = connector_class
        version = getattr(connector_class, "VERSION", "0.0.0")
        logger.debug(
            "Registered connector: %s %s v%s",
            portal.value,
            connector_type.value,
            version,
        )

    @classmethod
    def create(
        cls,
        portal: Portal,
        connector_type: ConnectorType,
        context: Any = None,
    ) -> tuple[Any, str]:
        """
        Create a connector instance and return it with its version.

        Args:
            portal: The portal to connect to.
            connector_type: The type of connector to use.
            context: Optional context (e.g., BrowserContext) for the connector.

        Returns:
            tuple[Any, str]: (connector_instance, version)

        Raises:
            RuntimeError: If connector is not registered.
        """
        info = get_connector_info(portal, connector_type)
        if info is None:
            raise RuntimeError(
                f"Unsupported connector: {portal.value} {connector_type.value}"
            )

        connector_class = cls._registry.get((portal, connector_type))
        if connector_class is None:
            raise RuntimeError(
                f"Connector not registered: {portal.value} {connector_type.value}"
            )

        version = getattr(connector_class, "VERSION", "0.0.0")

        if context is not None:
            connector = connector_class(context)
        else:
            connector = connector_class()

        return connector, version

    @classmethod
    def get_registered_connectors(
        cls,
    ) -> list[tuple[Portal, ConnectorType]]:
        """
        Return all connector implementations discovered
        and registered with the factory.
        """
        return list(cls._registry.keys())

    @classmethod
    def is_registered(
        cls,
        portal: Portal,
        connector_type: ConnectorType,
    ) -> bool:
        """
        Check if a connector is registered.

        Args:
            portal: The portal.
            connector_type: The connector type.

        Returns:
            bool: True if registered.
        """
        return (portal, connector_type) in cls._registry


# =============================================================================
# END OF FILE
# =============================================================================