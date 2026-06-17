from fastapi import APIRouter, Depends

from src.api.core.security import get_current_user
from src.api.schemas.market import DepartmentStats, MarketSummaryItem
from src.api.services import market_service

router = APIRouter()


@router.get("/summary", response_model=list[MarketSummaryItem])
def market_summary(_: dict = Depends(get_current_user)):
    return market_service.market_summary()


@router.get("/by-department", response_model=list[DepartmentStats])
def by_department(_: dict = Depends(get_current_user)):
    return market_service.by_department()
