from fastapi import APIRouter, Depends, HTTPException

from src.api.core.security import get_current_user
from src.api.schemas.skills import SkillDetail
from src.api.services import skills_service

router = APIRouter()


@router.get("", response_model=list[SkillDetail])
def list_skills(_: dict = Depends(get_current_user)):
    return skills_service.list_skills()


@router.get("/{name}", response_model=SkillDetail)
def get_skill(name: str, _: dict = Depends(get_current_user)):
    skill = skills_service.get_skill_by_name(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' introuvable")
    return skill
