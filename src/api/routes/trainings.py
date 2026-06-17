from fastapi import APIRouter, Depends

from src.api.core.security import get_current_user
from src.api.schemas.trainings import Training
from src.api.services import trainings_service

router = APIRouter()


@router.get("", response_model=list[Training])
def list_trainings(_: dict = Depends(get_current_user)):
    return trainings_service.list_trainings()


@router.get("/skill/{skill_name}", response_model=list[Training])
def trainings_by_skill(skill_name: str, _: dict = Depends(get_current_user)):
    return trainings_service.trainings_by_skill(skill_name)
