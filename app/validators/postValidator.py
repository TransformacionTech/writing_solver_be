from pydantic import BaseModel


class PostValidationResult(BaseModel):
    score: int
    is_valid: bool
    feedback: str


MINIMUM_SCORE = 8


def validate_post(score: int, feedback: str = "") -> PostValidationResult:
    return PostValidationResult(
        score=score,
        is_valid=score >= MINIMUM_SCORE,
        feedback=feedback,
    )
