from pydantic import BaseModel


class Training(BaseModel):
    title: str
    domain: str
    level: str
    duration_months: int | None
    provider: str
    url: str | None
