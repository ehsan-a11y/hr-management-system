"""
HR Management System - Payroll Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import sys
sys.path.append("..")
from database import get_db
from models import Payroll, Employee
from schemas import PayrollCreate, PayrollUpdate, PayrollOut

router = APIRouter(prefix="/payroll", tags=["Payroll"])


@router.get("/", response_model=List[PayrollOut])
def get_payroll(
    employee_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Payroll)
    if employee_id:
        query = query.filter(Payroll.employee_id == employee_id)
    if month:
        query = query.filter(Payroll.month == month)
    if year:
        query = query.filter(Payroll.year == year)
    return query.order_by(Payroll.year.desc(), Payroll.month.desc()).all()


@router.get("/{payroll_id}", response_model=PayrollOut)
def get_payroll_record(payroll_id: int, db: Session = Depends(get_db)):
    record = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    return record


@router.post("/", response_model=PayrollOut, status_code=201)
def create_payroll(payroll: PayrollCreate, db: Session = Depends(get_db)):
    # Check for duplicate payroll entry
    existing = db.query(Payroll).filter(
        Payroll.employee_id == payroll.employee_id,
        Payroll.month == payroll.month,
        Payroll.year == payroll.year
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Payroll already exists for this period")

    new_payroll = Payroll(**payroll.dict())
    db.add(new_payroll)
    db.commit()
    db.refresh(new_payroll)
    return new_payroll


@router.put("/{payroll_id}", response_model=PayrollOut)
def update_payroll(payroll_id: int, payroll: PayrollUpdate, db: Session = Depends(get_db)):
    db_payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not db_payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    for key, value in payroll.dict(exclude_unset=True).items():
        setattr(db_payroll, key, value)
    db.commit()
    db.refresh(db_payroll)
    return db_payroll


@router.delete("/{payroll_id}")
def delete_payroll(payroll_id: int, db: Session = Depends(get_db)):
    record = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    db.delete(record)
    db.commit()
    return {"message": "Payroll record deleted"}


@router.post("/generate/{month}/{year}")
def generate_monthly_payroll(month: int, year: int, db: Session = Depends(get_db)):
    """Auto-generate payroll for all active employees for a given month/year."""
    employees = db.query(Employee).filter(Employee.status == "active").all()
    created = 0
    skipped = 0

    for emp in employees:
        existing = db.query(Payroll).filter(
            Payroll.employee_id == emp.id,
            Payroll.month == month,
            Payroll.year == year
        ).first()
        if existing:
            skipped += 1
            continue

        tax = emp.salary * 0.1   # 10% tax
        net = emp.salary - tax
        payroll = Payroll(
            employee_id=emp.id,
            month=month,
            year=year,
            basic_salary=emp.salary,
            bonus=0.0,
            deductions=0.0,
            tax=round(tax, 2),
            net_salary=round(net, 2),
            payment_status="pending"
        )
        db.add(payroll)
        created += 1

    db.commit()
    return {"message": f"Payroll generated: {created} created, {skipped} skipped"}


@router.get("/summary/{month}/{year}")
def payroll_summary(month: int, year: int, db: Session = Depends(get_db)):
    """Get total payroll summary for a month."""
    records = db.query(Payroll).filter(
        Payroll.month == month,
        Payroll.year == year
    ).all()
    total_basic = sum(r.basic_salary for r in records)
    total_bonus = sum(r.bonus for r in records)
    total_tax = sum(r.tax for r in records)
    total_net = sum(r.net_salary for r in records)
    return {
        "month": month, "year": year,
        "total_employees": len(records),
        "total_basic_salary": round(total_basic, 2),
        "total_bonus": round(total_bonus, 2),
        "total_tax": round(total_tax, 2),
        "total_net_salary": round(total_net, 2)
    }
