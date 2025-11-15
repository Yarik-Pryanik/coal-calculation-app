from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from database import get_db
import models
import schemas

router = APIRouter(prefix="/calculations", tags=["calculations"])


def perform_calculations(boiler_operation: models.BoilerOperation,
                         coal_data: models.CoalData) -> schemas.CalculationResultCreate:
    """Выполнение расчетов на основе данных котла и угля"""

    # Определяем размер котла
    size = 50 if boiler_operation.boiler_number == 7 else 75

    # Расчеты по формулам из вашего кода
    q2 = (boiler_operation.t_yx - boiler_operation.t_cold) / 2085 * (
                0.7 * (21 / (21 - boiler_operation.o2)) + 0.13) * 100
    q4 = 0.9 * (boiler_operation.g_yn / (100 - boiler_operation.g_yn) * (7800 * coal_data.ap) / coal_data.qlow)
    q5 = (0.77 * size) / boiler_operation.dx

    n = 100 - (q2 + q4 + q5)

    b = 143 / n * 100
    qist = boiler_operation.d0 * (0.79 - 0.104)
    qpr = 0.065 * (boiler_operation.h_pr * boiler_operation.d0) / 100

    bk = b * (qist + qpr) / 1000
    bnat = bk / coal_data.k

    return schemas.CalculationResultCreate(
        q2=round(q2, 2),
        q4=round(q4, 2),
        q5=round(q5, 2),
        n=round(n, 2),
        b=round(b, 2),
        qist=round(qist, 2),
        qpr=round(qpr, 2),
        bk=round(bk, 2),
        bnat=round(bnat, 2)
    )


@router.post("/calculate", response_model=schemas.CalculationResult)
def calculate_and_save(request: schemas.FullCalculationRequest, db: Session = Depends(get_db)):
    """Выполнение расчетов и сохранение результатов"""

    # Получаем данные о работе котла
    boiler_operation = db.query(models.BoilerOperation).filter(
        models.BoilerOperation.date == request.date,
        models.BoilerOperation.boiler_number == request.boiler_number
    ).first()

    if boiler_operation is None:
        raise HTTPException(status_code=404, detail=f"Данные за дату {request.date} для котла {request.boiler_number} не найдены")
    print(f"🔍 DEBUG: Найден котел с coal_date = {boiler_operation.coal_date}")  # Отладочная информация
    # Получаем данные об угле
    coal_data = db.query(models.CoalData).filter(
        models.CoalData.date == boiler_operation.coal_date
    ).first()

    if coal_data is None:
        print(f"❌ DEBUG: Уголь с датой {boiler_operation.coal_date} не найден")  # Отладочная информация
        # Проверим какие даты угля вообще есть в базе
        all_coal_dates = db.query(models.CoalData.date).all()
        print(f"📅 DEBUG: Доступные даты угля: {[str(d[0]) for d in all_coal_dates]}")
        raise HTTPException(status_code=404, detail="Данные об угле не найдены")

    # Проверяем, не существует ли уже расчет для этой комбинации
    existing_calculation = db.query(models.CalculationResult).filter(
        models.CalculationResult.date == request.date,
        models.CalculationResult.boiler_number == request.boiler_number
    ).first()

    if existing_calculation:
        # Удаляем старый расчет
        db.delete(existing_calculation)
        db.commit()

    # Выполняем расчеты
    calculation_data = perform_calculations(boiler_operation, coal_data)

    # Сохраняем результаты
    db_calculation = models.CalculationResult(
        date=request.date,
        boiler_number=request.boiler_number,
        boiler_operation_id=boiler_operation.id,
        **calculation_data.dict()
    )

    db.add(db_calculation)
    db.commit()
    db.refresh(db_calculation)

    return db_calculation


@router.get("/{calculation_date}/{boiler_number}", response_model=schemas.CalculationResult)
def get_calculation_result(calculation_date: date, boiler_number: int, db: Session = Depends(get_db)):
    """Получение результатов расчетов"""
    calculation = db.query(models.CalculationResult).filter(
        models.CalculationResult.date == calculation_date,
        models.CalculationResult.boiler_number == boiler_number
    ).first()

    if calculation is None:
        raise HTTPException(status_code=404, detail="Результаты расчетов не найдены")

    return calculation


@router.get("/", response_model=list[schemas.CalculationResult])
def get_all_calculations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получение всех результатов расчетов"""

    return db.query(models.CalculationResult).offset(skip).limit(limit).all()
