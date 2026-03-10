"""
HR Management System - Pydantic Schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime


# --- Department Schemas ---

class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    manager_id: Optional[int] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(DepartmentBase):
    name: Optional[str] = None


class DepartmentOut(DepartmentBase):
    id: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# --- Employee Schemas ---

class EmployeeBase(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    position: str
    department_id: Optional[int] = None
    hire_date: date
    salary: float
    status: Optional[str] = "active"
    address: Optional[str] = None
    avatar_url: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department_id: Optional[int] = None
    salary: Optional[float] = None
    status: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None


class EmployeeOut(EmployeeBase):
    id: int
    created_at: Optional[datetime]
    department: Optional[DepartmentOut] = None

    class Config:
        from_attributes = True


# --- Attendance Schemas ---

class AttendanceBase(BaseModel):
    employee_id: int
    date: date
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: Optional[str] = "present"
    hours_worked: Optional[float] = 0.0
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: Optional[str] = None
    hours_worked: Optional[float] = None
    notes: Optional[str] = None


class AttendanceOut(AttendanceBase):
    id: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# --- Leave Schemas ---

class LeaveBase(BaseModel):
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    days: int
    reason: Optional[str] = None


class LeaveCreate(LeaveBase):
    pass


class LeaveUpdate(BaseModel):
    status: Optional[str] = None
    approved_by: Optional[int] = None
    reason: Optional[str] = None


class LeaveOut(LeaveBase):
    id: int
    status: str
    approved_by: Optional[int]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# --- Payroll Schemas ---

class PayrollBase(BaseModel):
    employee_id: int
    month: int
    year: int
    basic_salary: float
    bonus: Optional[float] = 0.0
    deductions: Optional[float] = 0.0
    tax: Optional[float] = 0.0
    net_salary: float
    payment_date: Optional[date] = None
    payment_status: Optional[str] = "pending"
    notes: Optional[str] = None


class PayrollCreate(PayrollBase):
    pass


class PayrollUpdate(BaseModel):
    bonus: Optional[float] = None
    deductions: Optional[float] = None
    tax: Optional[float] = None
    net_salary: Optional[float] = None
    payment_date: Optional[date] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None


class PayrollOut(PayrollBase):
    id: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# --- Dashboard Stats Schema ---

class DashboardStats(BaseModel):
    total_employees: int
    active_employees: int
    departments: int
    pending_leaves: int
    present_today: int
    total_payroll_month: float
