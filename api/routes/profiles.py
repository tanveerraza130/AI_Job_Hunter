"""
Profiles API routes
"""

from fastapi import APIRouter

from api.schemas import ProfileListResponse, ProfileResponse
from jobs.profiles.loader import ConfigLoader
from jobs.registry.connector_factory import ConnectorFactory

router = APIRouter()


@router.get("/profiles")
async def list_profiles() -> ProfileListResponse:
    """List all available enabled profiles."""

    profiles = []

    for profile_dir in sorted(ConfigLoader.PROFILES_PATH.iterdir()):
        if not profile_dir.is_dir():
            continue

        profile_id = profile_dir.name

        if profile_id.startswith(".") or profile_id.startswith("__"):
            continue

        try:
            profile = ConfigLoader.load_profile(profile_id)
        except ValueError:
            continue

        if profile.enabled:
            profiles.append(profile.profile_id or profile_id)

    return ProfileListResponse(profiles=profiles)


@router.get("/profiles/{profile_id}")
async def get_profile(
    profile_id: str,
) -> ProfileResponse:
    """Get profile details."""

    profile = ConfigLoader.load_profile(profile_id)

    skills = [
        {"name": skill, "weight": 1.0}
        for skill in profile.skills
    ]

    return ProfileResponse(
        profile_id=profile.profile_id or profile_id,
        profile_name=profile.profile_name,
        skills=skills,
        tools=profile.tools,
        experience_min=profile.experience_min,
        experience_max=profile.experience_max,
        salary_min=profile.salary_min,
        salary_max=profile.salary_max,
        work_modes=profile.work_modes,
    )

@router.get("/portals")
async def list_portals() -> dict[str, list[str]]:
    """List portals backed by discovered connector implementations."""

    ConnectorFactory.discover()

    portals = sorted(
        {
            portal.value
            for portal, _connector_type
            in ConnectorFactory.get_registered_connectors()
        }
    )

    return {"portals": portals}
