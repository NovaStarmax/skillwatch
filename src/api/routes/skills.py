from fastapi import APIRouter, Depends, HTTPException

from src.api.core.security import get_current_user
from src.api.schemas.skills import SkillDetail
from src.api.services import skills_service

router = APIRouter()


@router.get(
    "",
    response_model=list[SkillDetail],
    summary="Liste tous les skills",
    description="Retourne tous les skills connus avec leurs statistiques de marché agrégées (offres, usage développeurs, salaire moyen, formations). Triés par nombre d'offres décroissant, skills sans offres en fin de liste.",
    responses={401: {"description": "Token JWT manquant ou invalide"}},
)
def list_skills(_: dict = Depends(get_current_user)):
    return skills_service.list_skills()


@router.get(
    "/{name}",
    response_model=SkillDetail,
    summary="Détail d'un skill",
    description="Retourne le détail complet d'un skill par son nom canonique. La recherche est insensible à la casse (ILIKE). Retourne 404 si le skill n'existe pas.",
    responses={401: {"description": "Token JWT manquant ou invalide"}},
)
def get_skill(name: str, _: dict = Depends(get_current_user)):
    skill = skills_service.get_skill_by_name(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' introuvable")
    return skill
