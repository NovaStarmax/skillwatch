from pydantic import BaseModel


class SkillBase(BaseModel):
    name: str
    category: str


class SkillDetail(SkillBase):
    job_offer_count: int
    developer_usage_count: int
    avg_salary_eur: float | None
    training_count: int
