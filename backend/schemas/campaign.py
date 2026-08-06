from pydantic import BaseModel


class CampaignResponse(BaseModel):
    id: int
    name: str
    department: str
    status: str
    