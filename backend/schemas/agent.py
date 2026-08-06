from pydantic import BaseModel


class AgentResponse(BaseModel):
    id: int
    name: str
    status: str