"""
HR Management System - Leaves Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import sys
sys.path.append("..")
from database import get_db
from models import Leave
from schemas import LeaveCreate, LeaveUpdate, LeaveOut

router = APIRouter(prefix="/leaves", tags=["Leaves"])


@router.get("/", response_model=List[LeaveOut])
def get_leaves(
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Leave)
    if employee_id:
        query = query.filter(Leave.employee_id == employee_id)
    if status:
        query = query.filter(Leave.status == status)
    return query.order_by(Leave.created_at.desc()).all()


@router.get("/{leave_id}", response_model=LeaveOut)
def get_leave(leave_id: int, db: Session = Depends(get_db)):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return leave


@router.post("/", response_model=LeaveOut, status_code=201)
def create_leave(leave: LeaveCreate, db: Session = Depends(get_db)):
    if leave.end_date < leave.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    new_leave = Leave(**leave.dict())
    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)
    return new_leave


@router.put("/{leave_id}", response_model=LeaveOut)
def update_leave(leave_id: int, leave: LeaveUpdate, db: Session = Depends(get_db)):
    db_leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not db_leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    for key, value in leave.dict(exclude_unset=True).items():
        setattr(db_leave, key, value)
    db.commit()
    db.refresh(db_leave)
    return db_leave


@router.patch("/{leave_id}/approve")
def approve_leave(leave_id: int, approved_by: int = 1, db: Session = Depends(get_db)):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    leave.status = "approved"
    leave.approved_by = approved_by
    db.commit()
    return {"message": "Leave approved"}


@router.patch("/{leave_id}/reject")
def reject_leave(leave_id: int, db: Session = Depends(get_db)):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    leave.status = "rejected"
    db.commit()
    return {"message": "Leave rejected"}


@router.delete("/{leave_id}")
def delete_leave(leave_id: int, db: Session = Depends(get_db)):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    db.delete(leave)
    db.commit()
    return {"message": "Leave request deleted"}
