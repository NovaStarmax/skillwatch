from pydantic import BaseModel


class MarketSummaryItem(BaseModel):
    skill: str
    category: str
    job_offer_count: int
    developer_usage_count: int
    avg_salary_eur: float | None
    training_count: int
    top_dept: str | None = None
    top_dept_name: str | None = None
    top_dept_population: int | None = None


class DepartmentStats(BaseModel):
    dept_code: str
    dept_name: str
    population: int
    job_count: int
    jobs_per_million_hab: float
