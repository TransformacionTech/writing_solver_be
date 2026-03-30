from pydantic import BaseModel


class PipelineRunRequest(BaseModel):
    topic: str
    context: str | None = None
    user_id: str


class PipelineProgressEvent(BaseModel):
    type: str = "progress"
    agent: str
    message: str


class PipelineResultEvent(BaseModel):
    type: str = "result"
    post: str
    score: int


class PipelineDoneEvent(BaseModel):
    type: str = "done"
