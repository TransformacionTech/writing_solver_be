import httpx

from app.core.config import settings
from app.core.security import create_access_token

_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"


async def exchange_code_for_token(code: str) -> dict:
    """Exchange GitHub OAuth code for access token, fetch user profile, return JWT."""
    async with httpx.AsyncClient() as client:
        # Exchange code for GitHub access token
        token_resp = await client.post(
            _GITHUB_TOKEN_URL,
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        gh_access_token = token_data["access_token"]

        # Fetch GitHub user profile
        user_resp = await client.get(
            _GITHUB_USER_URL,
            headers={"Authorization": f"Bearer {gh_access_token}"},
        )
        user_resp.raise_for_status()
        user = user_resp.json()

    jwt_token = create_access_token(
        data={
            "sub": str(user["id"]),
            "username": user["login"],
            "email": user.get("email", ""),
            "avatar_url": user.get("avatar_url", ""),
        },
    )

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["id"]),
            "username": user["login"],
            "email": user.get("email", ""),
            "avatar_url": user.get("avatar_url", ""),
        },
    }
