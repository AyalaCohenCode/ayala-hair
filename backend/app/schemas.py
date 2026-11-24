"""הצורה של המידע שנכנס ויוצא מהשרת (Pydantic)."""
import re
from datetime import date, time

from pydantic import BaseModel, Field, field_validator

from .config import TREATMENTS


class FreeSlot(BaseModel):
    id: int
    day: date
    start: time


class BookingIn(BaseModel):
    slot_id: int
    name: str = Field(min_length=2, max_length=80)
    phone: str = Field(min_length=9, max_length=20)
    treatment: str

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("צריך למלא שם")
        return v

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if not 9 <= len(digits) <= 12:
            raise ValueError("מספר טלפון לא תקין")
        return digits

    @field_validator("treatment")
    @classmethod
    def known_treatment(cls, v: str) -> str:
        if v not in TREATMENTS:
            raise ValueError("סוג טיפול לא מוכר")
        return v


class BookingOut(BaseModel):
    id: int
    day: date
    start: time
    treatment: str


class LoginIn(BaseModel):
    password: str = Field(max_length=200)


class TokenOut(BaseModel):
    token: str


class SlotsIn(BaseModel):
    day: date
    times: list[time] = Field(min_length=1, max_length=30)


class AdminBooking(BaseModel):
    id: int
    name: str
    phone: str
    treatment: str
    paid: bool


class AdminSlot(BaseModel):
    id: int
    day: date
    start: time
    booking: AdminBooking | None = None


class PaidIn(BaseModel):
    paid: bool
