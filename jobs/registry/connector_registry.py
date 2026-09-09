"""
Connector registry for AI Job Hunter.

Centralizes connector definitions. Version information is owned by
the connector implementations themselves, not the registry.
"""

from __future__ import annotations

from dataclasses import dataclass

from jobs.enums import ConnectorType, Portal


@dataclass(frozen=True)
class ConnectorInfo:
    """
    Information about a connector.

    Attributes:
        portal: The portal this connector works with.
        connector_type: The type of connector implementation.
        default: Whether this is the default connector for this portal.

    Note: Connector version is owned by the connector implementation,
    not the registry. Each connector class exposes its own VERSION attribute.
    """
    portal: Portal
    connector_type: ConnectorType
    default: bool = False


# Registry of all available connectors - dictionary for O(1) lookup
CONNECTOR_REGISTRY: dict[tuple[Portal, ConnectorType], ConnectorInfo] = {
    # Naukri
    (Portal.NAUKRI, ConnectorType.API): ConnectorInfo(
        portal=Portal.NAUKRI,
        connector_type=ConnectorType.API,
        default=True,
    ),
    (Portal.NAUKRI, ConnectorType.PLAYWRIGHT): ConnectorInfo(
        portal=Portal.NAUKRI,
        connector_type=ConnectorType.PLAYWRIGHT,
        default=False,
    ),

    # IIMJobs
    (Portal.IIMJOBS, ConnectorType.API): ConnectorInfo(
        portal=Portal.IIMJOBS,
        connector_type=ConnectorType.API,
        default=True,
    ),

    # LinkedIn
    (Portal.LINKEDIN, ConnectorType.API): ConnectorInfo(
        portal=Portal.LINKEDIN,
        connector_type=ConnectorType.API,
        default=False,
    ),

    # LinkedIn Hiring Posts
    (Portal.LINKEDIN_POST, ConnectorType.API): ConnectorInfo(
        portal=Portal.LINKEDIN_POST,
        connector_type=ConnectorType.API,
        default=True,
    ),
    (Portal.LINKEDIN, ConnectorType.PLAYWRIGHT): ConnectorInfo(
        portal=Portal.LINKEDIN,
        connector_type=ConnectorType.PLAYWRIGHT,
        default=True,
    ),

    # Indeed
    (Portal.INDEED, ConnectorType.API): ConnectorInfo(
        portal=Portal.INDEED,
        connector_type=ConnectorType.API,
        default=False,
    ),
    (Portal.INDEED, ConnectorType.PLAYWRIGHT): ConnectorInfo(
        portal=Portal.INDEED,
        connector_type=ConnectorType.PLAYWRIGHT,
        default=True,
    ),

    # Foundit
    (Portal.FOUNDIT, ConnectorType.API): ConnectorInfo(
        portal=Portal.FOUNDIT,
        connector_type=ConnectorType.API,
        default=True,
    ),

    # Instahyre
    (Portal.INSTAHYRE, ConnectorType.API): ConnectorInfo(
        portal=Portal.INSTAHYRE,
        connector_type=ConnectorType.API,
        default=True,
    ),

    # Cutshort
    (Portal.CUTSHORT, ConnectorType.API): ConnectorInfo(
        portal=Portal.CUTSHORT,
        connector_type=ConnectorType.API,
        default=True,
    ),

    # Wellfound
    (Portal.WELLFOUND, ConnectorType.API): ConnectorInfo(
        portal=Portal.WELLFOUND,
        connector_type=ConnectorType.API,
        default=True,
    ),

    # Greenhouse
    (Portal.GREENHOUSE, ConnectorType.API): ConnectorInfo(
        portal=Portal.GREENHOUSE,
        connector_type=ConnectorType.API,
        default=True,
    ),

    # Lever
    (Portal.LEVER, ConnectorType.API): ConnectorInfo(
        portal=Portal.LEVER,
        connector_type=ConnectorType.API,
        default=True,
    ),

    # Ashby
    (Portal.ASHBY, ConnectorType.API): ConnectorInfo(
        portal=Portal.ASHBY,
        connector_type=ConnectorType.API,
        default=True,
    ),

    # Company career pages
    (Portal.COMPANY, ConnectorType.PLAYWRIGHT): ConnectorInfo(
        portal=Portal.COMPANY,
        connector_type=ConnectorType.PLAYWRIGHT,
        default=True,
    ),
}


def get_connector_info(
    portal: Portal,
    connector_type: ConnectorType,
) -> ConnectorInfo | None:
    """
    Get connector information.

    Args:
        portal: The portal.
        connector_type: The connector type.

    Returns:
        ConnectorInfo or None: The connector info, if found.
    """
    return CONNECTOR_REGISTRY.get((portal, connector_type))


def get_default_connector(portal: Portal) -> ConnectorInfo | None:
    """
    Get the default connector for a portal.

    Args:
        portal: The portal.

    Returns:
        ConnectorInfo or None: The default connector, if any.
    """
    for (p, ct), info in CONNECTOR_REGISTRY.items():
        if p == portal and info.default:
            return info
    return None


# =============================================================================
# END OF FILE
# =============================================================================