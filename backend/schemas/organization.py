from pydantic import BaseModel


class OrganizationResponse(BaseModel):
    id: int
    name: str
    state: str