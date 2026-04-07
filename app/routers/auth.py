from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.schemas.auth import AuthTokenResponse, GitHubAuthRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/github", response_model=AuthTokenResponse)
async def github_auth(body: GitHubAuthRequest) -> AuthTokenResponse:
    result = await auth_service.exchange_code_for_token(code=body.code)
    return AuthTokenResponse(**result)


@router.get("/callback")
async def github_callback(code: str = Query(...)) -> RedirectResponse:
    """Handle GitHub OAuth redirect: exchange code and redirect to frontend with JWT."""
    result = await auth_service.exchange_code_for_token(code=code)
    token = result["access_token"]
    return RedirectResponse(
        url=f"{settings.frontend_url}/login-success?token={token}",
    )
