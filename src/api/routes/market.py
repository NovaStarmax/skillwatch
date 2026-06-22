from fastapi import APIRouter, Depends

from src.api.core.security import get_current_user
from src.api.schemas.market import DepartmentStats, MarketSummaryItem
from src.api.services import market_service

router = APIRouter()


@router.get(
    "/summary",
    response_model=list[MarketSummaryItem],
    summary="Top 20 skills du marché",
    description="Retourne les 20 skills les plus demandés en offres d'emploi France Travail. Chaque entrée inclut le salaire moyen (converti en EUR), la popularité Stack Overflow et le département avec le plus d'offres pour ce skill.",
)
def market_summary(_: dict = Depends(get_current_user)):
    return market_service.market_summary()


@router.get(
    "/by-department",
    response_model=list[DepartmentStats],
    summary="Offres par département",
    description="Croise les offres France Travail avec les données démographiques INSEE. Retourne les 20 départements les plus actifs avec le ratio offres/million d'habitants pour neutraliser l'effet de la taille de population.",
)
def by_department(_: dict = Depends(get_current_user)):
    return market_service.by_department()
