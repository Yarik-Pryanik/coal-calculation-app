from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from database import get_db
import models
import schemas

router = APIRouter(prefix="/coal", tags=["coal"])


@router.post("/", response_model=schemas.CoalData, status_code=status.HTTP_201_CREATED)
def create_or_update_coal_data(
        coal_data: schemas.CoalDataCreate,
        coal_date: date,
        db: Session = Depends(get_db)
):

    # Проверяем существование данных за эту дату
    existing_coal = db.query(models.CoalData).filter(models.CoalData.date == coal_date).first()

    if existing_coal:
        # Если данные уже существуют - заменяем их
        for field, value in coal_data.dict().items():
            setattr(existing_coal, field, value)

        db.commit()
        db.refresh(existing_coal)
        return existing_coal
    else:
        # Создаем новые данные
        db_coal = models.CoalData(
            date=coal_date,
            **coal_data.dict()
        )
        db.add(db_coal)
        db.commit()
        db.refresh(db_coal)
        return db_coal


@router.get("/{coal_date}", response_model=schemas.CoalData)
def get_coal_data(
        coal_date: date,
        db: Session = Depends(get_db)
):
    """Получение данных об угле за определенную дату"""
    coal_data = db.query(models.CoalData).filter(models.CoalData.date == coal_date).first()
    if coal_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Данные об угле за дату {coal_date} не найдены"
        )
    return coal_data


@router.get("/", response_model=list[schemas.CoalData])
def get_all_coal_data(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)):
    """Получение всех данных об угле"""

    return db.query(models.CoalData).offset(skip).limit(limit).all()
