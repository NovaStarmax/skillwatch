from fastapi import APIRouter, Depends

from src.api.core.security import get_current_user
from src.api.schemas.trainings import Training
from src.api.services import trainings_service

router = APIRouter()


@router.get(
    "",
    response_model=list[Training],
    summary="Liste toutes les formations",
    description="Retourne toutes les formations OpenClassrooms scrapées, filtrées sur les domaines tech (Data, Développement, Systèmes & Réseaux, Cybersécurité). Triées par domaine puis titre.",
)
def list_trainings(_: dict = Depends(get_current_user)):
    return trainings_service.list_trainings()


@router.get(
    "/skill/{skill_name}",
    response_model=list[Training],
    summary="Formations pour un skill",
    description="Retourne les formations disponibles pour apprendre un skill spécifique. La recherche est insensible à la casse. Retourne une liste vide si aucune formation ne couvre ce skill.",
)
def trainings_by_skill(skill_name: str, _: dict = Depends(get_current_user)):
    return trainings_service.trainings_by_skill(skill_name)
