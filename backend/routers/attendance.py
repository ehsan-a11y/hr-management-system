"""
HR Management System - Attendance Router
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import sys
sys.path.append("..")
from database import get_db
from models import Attendance
from schemas import AttendanceCreate, AttendanceUpdate, AttendanceOut

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("/", response_model=List[AttendanceOut])
def get_attendance(
    employee_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Attendance)
    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    if date_from:
        query = query.filter(Attendance.date >= date_from)
    if date_to:
        query = query.filter(Attendance.date <= date_to)
    if status:
        query = query.filter(Attendance.status == status)
    return query.order_by(Attendance.date.desc()).all()


@router.get("/{att_id}", response_model=AttendanceOut)
def get_attendance_record(att_id: int, db: Session = Depends(get_db)):
    record = db.query(Attendance).filter(Attendance.id == att_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return record


@router.post("/", response_model=AttendanceOut, status_code=201)
def create_attendance(att: AttendanceCreate, db: Session = Depends(get_db)):
    # Check for duplicate entry on same date
    existing = db.query(Attendance).filter(
        Attendance.employee_id == att.employee_id,
        Attendance.date == att.date
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already recorded for this date")

    new_att = Attendance(**att.dict())
    db.add(new_att)
    db.commit()
    db.refresh(new_att)
    return new_att


@router.put("/{att_id}", response_model=AttendanceOut)
def update_attendance(att_id: int, att: AttendanceUpdate, db: Session = Depends(get_db)):
    db_att = db.query(Attendance).filter(Attendance.id == att_id).first()
    if not db_att:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    for key, value in att.dict(exclude_unset=True).items():
        setattr(db_att, key, value)
    db.commit()
    db.refresh(db_att)
    return db_att


@router.delete("/{att_id}")
def delete_attendance(att_id: int, db: Session = Depends(get_db)):
    record = db.query(Attendance).filter(Attendance.id == att_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    db.delete(record)
    db.commit()
    return {"message": "Attendance record deleted"}


@router.get("/today/summary")
def today_attendance_summary(db: Session = Depends(get_db)):
    """Get today's attendance counts."""
    today = date.today()
    records = db.query(Attendance).filter(Attendance.date == today).all()
    summary = {"present": 0, "absent": 0, "late": 0, "half_day": 0, "total": len(records)}
    for r in records:
        if r.status in summary:
            summary[r.status] += 1
    return summary
