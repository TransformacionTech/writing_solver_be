from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    mensaje: str
    post_actual: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    respuesta: str
    post_modificado: bool
