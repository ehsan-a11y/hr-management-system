"""
HR Management System — Vercel Serverless (FastAPI)
All routes prefixed with /api/
SQLite stored in /tmp/ (ephemeral, seeded on cold start)
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime, timedelta
import os

# ─── Database ────────────────────────────────────────────────────────────────
DB_PATH = "/tmp/hr_management.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Models ──────────────────────────────────────────────────────────────────
class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    manager_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    employees = relationship("Employee", back_populates="department")


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    position = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    hire_date = Column(Date, nullable=False)
    salary = Column(Float, nullable=False)
    status = Column(String(20), default="active")
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    department = relationship("Department", back_populates="employees")
    attendance = relationship("Attendance", back_populates="employee")
    leaves = relationship("Leave", back_populates="employee")
    payroll = relationship("Payroll", back_populates="employee")


class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(String(10), nullable=True)
    check_out = Column(String(10), nullable=True)
    status = Column(String(20), default="present")
    hours_worked = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    employee = relationship("Employee", back_populates="attendance")


class Leave(Base):
    __tablename__ = "leaves"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    approved_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    employee = relationship("Employee", back_populates="leaves")


class Payroll(Base):
    __tablename__ = "payroll"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    basic_salary = Column(Float, nullable=False)
    bonus = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    net_salary = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=True)
    payment_status = Column(String(20), default="pending")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    employee = relationship("Employee", back_populates="payroll")


# ─── Pydantic Schemas ────────────────────────────────────────────────────────
class DeptOut(BaseModel):
    id: int; name: str; description: Optional[str] = None; manager_id: Optional[int] = None; created_at: Optional[datetime] = None
    class Config: from_attributes = True

class DeptCreate(BaseModel):
    name: str; description: Optional[str] = None; manager_id: Optional[int] = None

class EmpOut(BaseModel):
    id: int; employee_id: str; first_name: str; last_name: str; email: str
    phone: Optional[str] = None; position: str; department_id: Optional[int] = None
    hire_date: date; salary: float; status: Optional[str] = "active"
    address: Optional[str] = None; created_at: Optional[datetime] = None
    department: Optional[DeptOut] = None
    class Config: from_attributes = True

class EmpCreate(BaseModel):
    employee_id: str; first_name: str; last_name: str; email: str
    phone: Optional[str] = None; position: str; department_id: Optional[int] = None
    hire_date: date; salary: float; status: Optional[str] = "active"; address: Optional[str] = None

class EmpUpdate(BaseModel):
    first_name: Optional[str] = None; last_name: Optional[str] = None; email: Optional[str] = None
    phone: Optional[str] = None; position: Optional[str] = None; department_id: Optional[int] = None
    salary: Optional[float] = None; status: Optional[str] = None; address: Optional[str] = None

class AttOut(BaseModel):
    id: int; employee_id: int; date: date; check_in: Optional[str] = None
    check_out: Optional[str] = None; status: Optional[str] = None
    hours_worked: Optional[float] = None; notes: Optional[str] = None; created_at: Optional[datetime] = None
    class Config: from_attributes = True

class AttCreate(BaseModel):
    employee_id: int; date: date; check_in: Optional[str] = None; check_out: Optional[str] = None
    status: Optional[str] = "present"; hours_worked: Optional[float] = 0.0; notes: Optional[str] = None

class AttUpdate(BaseModel):
    check_in: Optional[str] = None; check_out: Optional[str] = None
    status: Optional[str] = None; hours_worked: Optional[float] = None; notes: Optional[str] = None

class LeaveOut(BaseModel):
    id: int; employee_id: int; leave_type: str; start_date: date; end_date: date
    days: int; reason: Optional[str] = None; status: str; approved_by: Optional[int] = None
    created_at: Optional[datetime] = None
    class Config: from_attributes = True

class LeaveCreate(BaseModel):
    employee_id: int; leave_type: str; start_date: date; end_date: date
    days: int; reason: Optional[str] = None

class PayrollOut(BaseModel):
    id: int; employee_id: int; month: int; year: int; basic_salary: float
    bonus: float = 0.0; deductions: float = 0.0; tax: float = 0.0; net_salary: float
    payment_date: Optional[date] = None; payment_status: Optional[str] = None
    notes: Optional[str] = None; created_at: Optional[datetime] = None
    class Config: from_attributes = True

class PayrollCreate(BaseModel):
    employee_id: int; month: int; year: int; basic_salary: float
    bonus: float = 0.0; deductions: float = 0.0; tax: float = 0.0; net_salary: float
    payment_date: Optional[date] = None; payment_status: Optional[str] = "pending"; notes: Optional[str] = None

class PayrollUpdate(BaseModel):
    bonus: Optional[float] = None; deductions: Optional[float] = None; tax: Optional[float] = None
    net_salary: Optional[float] = None; payment_date: Optional[date] = None
    payment_status: Optional[str] = None; notes: Optional[str] = None


# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(title="HR Management System API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Create tables + seed data
Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        if db.query(Department).count() > 0:
            return
        depts = [
            Department(name="Engineering", description="Software Development"),
            Department(name="Human Resources", description="HR & Recruitment"),
            Department(name="Finance", description="Accounting & Finance"),
            Department(name="Marketing", description="Marketing & Sales"),
            Department(name="Operations", description="Operations & Logistics"),
        ]
        for d in depts:
            db.add(d)
        db.commit()

        today = date.today()
        emps = [
            Employee(employee_id="EMP001", first_name="Alice", last_name="Johnson",
                email="alice@company.com", phone="555-0101", position="Senior Developer",
                department_id=1, hire_date=date(2020, 3, 15), salary=85000, status="active"),
            Employee(employee_id="EMP002", first_name="Bob", last_name="Smith",
                email="bob@company.com", phone="555-0102", position="HR Manager",
                department_id=2, hire_date=date(2019, 7, 1), salary=72000, status="active"),
            Employee(employee_id="EMP003", first_name="Carol", last_name="Williams",
                email="carol@company.com", phone="555-0103", position="Financial Analyst",
                department_id=3, hire_date=date(2021, 1, 10), salary=68000, status="active"),
            Employee(employee_id="EMP004", first_name="David", last_name="Brown",
                email="david@company.com", phone="555-0104", position="Marketing Lead",
                department_id=4, hire_date=date(2022, 5, 20), salary=65000, status="active"),
            Employee(employee_id="EMP005", first_name="Eve", last_name="Davis",
                email="eve@company.com", phone="555-0105", position="Junior Developer",
                department_id=1, hire_date=date(2023, 9, 1), salary=55000, status="active"),
        ]
        for e in emps:
            db.add(e)
        db.commit()

        statuses = ["present", "present", "present", "late", "absent"]
        for i, s in enumerate(statuses, 1):
            db.add(Attendance(
                employee_id=i, date=today,
                check_in="09:00" if s != "absent" else None,
                check_out="18:00" if s == "present" else None,
                status=s, hours_worked=9.0 if s == "present" else 0
            ))
        db.commit()

        db.add(Leave(employee_id=5, leave_type="sick",
            start_date=today, end_date=today + timedelta(days=2), days=3,
            reason="Flu", status="pending"))
        db.add(Leave(employee_id=4, leave_type="annual",
            start_date=today + timedelta(days=5), end_date=today + timedelta(days=9), days=5,
            reason="Vacation", status="approved", approved_by=2))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
    finally:
        db.close()


seed()

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/api")
@app.get("/api/")
def root():
    return {"message": "HR Management System API", "status": "running"}


# Dashboard
@app.get("/api/dashboard/stats")
def dashboard_stats():
    db = SessionLocal()
    try:
        today = date.today()
        return {
            "total_employees": db.query(Employee).count(),
            "active_employees": db.query(Employee).filter(Employee.status == "active").count(),
            "departments": db.query(Department).count(),
            "pending_leaves": db.query(Leave).filter(Leave.status == "pending").count(),
            "present_today": db.query(Attendance).filter(
                Attendance.date == today, Attendance.status == "present").count(),
            "total_payroll_month": round(sum(
                p.net_salary for p in db.query(Payroll).filter(
                    Payroll.month == today.month, Payroll.year == today.year).all()
            ), 2)
        }
    finally:
        db.close()


# ── Departments ──
@app.get("/api/departments/", response_model=List[DeptOut])
def get_departments():
    db = SessionLocal()
    try: return db.query(Department).all()
    finally: db.close()

@app.get("/api/departments/{dept_id}", response_model=DeptOut)
def get_department(dept_id: int):
    db = SessionLocal()
    try:
        d = db.query(Department).filter(Department.id == dept_id).first()
        if not d: raise HTTPException(404, "Not found")
        return d
    finally: db.close()

@app.post("/api/departments/", response_model=DeptOut, status_code=201)
def create_department(dept: DeptCreate):
    db = SessionLocal()
    try:
        if db.query(Department).filter(Department.name == dept.name).first():
            raise HTTPException(400, "Department already exists")
        obj = Department(**dept.dict())
        db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/departments/{dept_id}", response_model=DeptOut)
def update_department(dept_id: int, dept: DeptCreate):
    db = SessionLocal()
    try:
        obj = db.query(Department).filter(Department.id == dept_id).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in dept.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.delete("/api/departments/{dept_id}")
def delete_department(dept_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Department).filter(Department.id == dept_id).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()


# ── Employees ──
@app.get("/api/employees/", response_model=List[EmpOut])
def get_employees(search: Optional[str] = None, department_id: Optional[int] = None, status: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Employee)
        if search:
            q = q.filter(
                (Employee.first_name.ilike(f"%{search}%")) |
                (Employee.last_name.ilike(f"%{search}%")) |
                (Employee.email.ilike(f"%{search}%")) |
                (Employee.employee_id.ilike(f"%{search}%"))
            )
        if department_id: q = q.filter(Employee.department_id == department_id)
        if status: q = q.filter(Employee.status == status)
        return q.all()
    finally: db.close()

@app.get("/api/employees/{emp_id}", response_model=EmpOut)
def get_employee(emp_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Employee).filter(Employee.id == emp_id).first()
        if not obj: raise HTTPException(404, "Not found")
        return obj
    finally: db.close()

@app.post("/api/employees/", response_model=EmpOut, status_code=201)
def create_employee(emp: EmpCreate):
    db = SessionLocal()
    try:
        if db.query(Employee).filter(Employee.email == emp.email).first():
            raise HTTPException(400, "Email already registered")
        if db.query(Employee).filter(Employee.employee_id == emp.employee_id).first():
            raise HTTPException(400, "Employee ID already exists")
        obj = Employee(**emp.dict()); db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/employees/{emp_id}", response_model=EmpOut)
def update_employee(emp_id: int, emp: EmpUpdate):
    db = SessionLocal()
    try:
        obj = db.query(Employee).filter(Employee.id == emp_id).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in emp.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.delete("/api/employees/{emp_id}")
def delete_employee(emp_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Employee).filter(Employee.id == emp_id).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()


# ── Attendance ──
@app.get("/api/attendance/", response_model=List[AttOut])
def get_attendance(employee_id: Optional[int] = None, date_from: Optional[date] = None,
                   date_to: Optional[date] = None, status: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Attendance)
        if employee_id: q = q.filter(Attendance.employee_id == employee_id)
        if date_from: q = q.filter(Attendance.date >= date_from)
        if date_to: q = q.filter(Attendance.date <= date_to)
        if status: q = q.filter(Attendance.status == status)
        return q.order_by(Attendance.date.desc()).all()
    finally: db.close()

@app.post("/api/attendance/", response_model=AttOut, status_code=201)
def create_attendance(att: AttCreate):
    db = SessionLocal()
    try:
        if db.query(Attendance).filter(
            Attendance.employee_id == att.employee_id, Attendance.date == att.date
        ).first(): raise HTTPException(400, "Attendance already recorded for this date")
        obj = Attendance(**att.dict()); db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/attendance/{att_id}", response_model=AttOut)
def update_attendance(att_id: int, att: AttUpdate):
    db = SessionLocal()
    try:
        obj = db.query(Attendance).filter(Attendance.id == att_id).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in att.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.delete("/api/attendance/{att_id}")
def delete_attendance(att_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Attendance).filter(Attendance.id == att_id).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()


# ── Leaves ──
@app.get("/api/leaves/", response_model=List[LeaveOut])
def get_leaves(employee_id: Optional[int] = None, status: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Leave)
        if employee_id: q = q.filter(Leave.employee_id == employee_id)
        if status: q = q.filter(Leave.status == status)
        return q.order_by(Leave.created_at.desc()).all()
    finally: db.close()

@app.get("/api/leaves/{leave_id}", response_model=LeaveOut)
def get_leave(leave_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Leave).filter(Leave.id == leave_id).first()
        if not obj: raise HTTPException(404, "Not found")
        return obj
    finally: db.close()

@app.post("/api/leaves/", response_model=LeaveOut, status_code=201)
def create_leave(leave: LeaveCreate):
    db = SessionLocal()
    try:
        if leave.end_date < leave.start_date: raise HTTPException(400, "End date must be after start date")
        obj = Leave(**leave.dict()); db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/leaves/{leave_id}", response_model=LeaveOut)
def update_leave(leave_id: int, leave: dict):
    db = SessionLocal()
    try:
        obj = db.query(Leave).filter(Leave.id == leave_id).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in leave.items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.patch("/api/leaves/{leave_id}/approve")
def approve_leave(leave_id: int, approved_by: int = 1):
    db = SessionLocal()
    try:
        obj = db.query(Leave).filter(Leave.id == leave_id).first()
        if not obj: raise HTTPException(404, "Not found")
        obj.status = "approved"; obj.approved_by = approved_by
        db.commit(); return {"message": "Leave approved"}
    finally: db.close()

@app.patch("/api/leaves/{leave_id}/reject")
def reject_leave(leave_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Leave).filter(Leave.id == leave_id).first()
        if not obj: raise HTTPException(404, "Not found")
        obj.status = "rejected"; db.commit(); return {"message": "Leave rejected"}
    finally: db.close()

@app.delete("/api/leaves/{leave_id}")
def delete_leave(leave_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Leave).filter(Leave.id == leave_id).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()


# ── Payroll ──
@app.get("/api/payroll/summary/{month}/{year}")
def payroll_summary(month: int, year: int):
    db = SessionLocal()
    try:
        recs = db.query(Payroll).filter(Payroll.month == month, Payroll.year == year).all()
        return {
            "month": month, "year": year,
            "total_employees": len(recs),
            "total_basic_salary": round(sum(r.basic_salary for r in recs), 2),
            "total_bonus": round(sum(r.bonus for r in recs), 2),
            "total_tax": round(sum(r.tax for r in recs), 2),
            "total_net_salary": round(sum(r.net_salary for r in recs), 2)
        }
    finally: db.close()

@app.get("/api/payroll/", response_model=List[PayrollOut])
def get_payroll(employee_id: Optional[int] = None, month: Optional[int] = None, year: Optional[int] = None):
    db = SessionLocal()
    try:
        q = db.query(Payroll)
        if employee_id: q = q.filter(Payroll.employee_id == employee_id)
        if month: q = q.filter(Payroll.month == month)
        if year: q = q.filter(Payroll.year == year)
        return q.order_by(Payroll.year.desc(), Payroll.month.desc()).all()
    finally: db.close()

@app.post("/api/payroll/", response_model=PayrollOut, status_code=201)
def create_payroll(payroll: PayrollCreate):
    db = SessionLocal()
    try:
        if db.query(Payroll).filter(
            Payroll.employee_id == payroll.employee_id,
            Payroll.month == payroll.month,
            Payroll.year == payroll.year
        ).first(): raise HTTPException(400, "Payroll already exists for this period")
        obj = Payroll(**payroll.dict()); db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/payroll/{payroll_id}", response_model=PayrollOut)
def update_payroll(payroll_id: int, payroll: PayrollUpdate):
    db = SessionLocal()
    try:
        obj = db.query(Payroll).filter(Payroll.id == payroll_id).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in payroll.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.delete("/api/payroll/{payroll_id}")
def delete_payroll(payroll_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Payroll).filter(Payroll.id == payroll_id).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()

@app.post("/api/payroll/generate/{month}/{year}")
def generate_payroll(month: int, year: int):
    db = SessionLocal()
    try:
        employees = db.query(Employee).filter(Employee.status == "active").all()
        created = skipped = 0
        for emp in employees:
            if db.query(Payroll).filter(
                Payroll.employee_id == emp.id, Payroll.month == month, Payroll.year == year
            ).first():
                skipped += 1; continue
            tax = emp.salary * 0.1
            db.add(Payroll(
                employee_id=emp.id, month=month, year=year,
                basic_salary=emp.salary, bonus=0.0, deductions=0.0,
                tax=round(tax, 2), net_salary=round(emp.salary - tax, 2),
                payment_status="pending"
            ))
            created += 1
        db.commit()
        return {"message": f"Payroll generated: {created} created, {skipped} skipped"}
    finally: db.close()
