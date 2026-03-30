from fastapi import APIRouter

from app.schemas.auth import AuthTokenResponse, GitHubAuthRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/github", response_model=AuthTokenResponse)
async def github_auth(body: GitHubAuthRequest) -> AuthTokenResponse:
    result = await auth_service.exchange_code_for_token(code=body.code)
    return AuthTokenResponse(**result)
