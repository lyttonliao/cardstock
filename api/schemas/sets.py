from pydantic import BaseModel


class SetSummary(BaseModel):
    set_id: str
    name: str
    series: str
    image_logo: str | None
    image_symbol: str | None

class SetListResponse(BaseModel):
    total: int
    items: list[SetSummary]
