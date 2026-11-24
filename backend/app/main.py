"""השרת של מערכת התורים של איילה.

נתיבים ללקוחות:
  GET  /api/slots         - שעות פנויות
  POST /api/bookings      - קביעת תור

נתיבים למנהלת (צריך כניסה):
  POST   /api/admin/login
  GET    /api/admin/slots
  POST   /api/admin/slots
  DELETE /api/admin/slots/{id}
  PATCH  /api/admin/bookings/{id}   - סימון "שולם"
  DELETE /api/admin/bookings/{id}   - ביטול תור (השעה חוזרת להיות פנויה)
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from . import auth
from .config import ALLOWED_ORIGINS, DAYS_AHEAD, TIMEZONE
from .database import Base, engine, get_db
from .models import Booking, Slot
from .schemas import (
    AdminBooking, AdminSlot, BookingIn, BookingOut, FreeSlot, LoginIn, PaidIn, SlotsIn, TokenOut,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # יוצר את הטבלאות במסד הנתונים בפעם הראשונה שהשרת עולה
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Ayala booking API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


def now_local() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE)).replace(tzinfo=None)


def is_future(slot: Slot) -> bool:
    return datetime.combine(slot.day, slot.start) > now_local()


# ---------- בדיקה שהשרת חי ----------

@app.get("/health")
def health(db_check: bool = False, db: Session = Depends(get_db)):
    if db_check:
        db.execute(text("SELECT 1"))
    return {"ok": True}


# ---------- לקוחות ----------

@app.get("/api/slots", response_model=list[FreeSlot])
def free_slots(db: Session = Depends(get_db)):
    now = now_local()
    last_day = (now + timedelta(days=DAYS_AHEAD)).date()
    rows = db.scalars(
        select(Slot)
        .outerjoin(Booking)
        .where(Booking.id.is_(None), Slot.day >= now.date(), Slot.day <= last_day)
        .order_by(Slot.day, Slot.start)
    ).all()
    return [FreeSlot(id=s.id, day=s.day, start=s.start) for s in rows if is_future(s)]


@app.post("/api/bookings", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def book(data: BookingIn, db: Session = Depends(get_db)):
    slot = db.get(Slot, data.slot_id)
    if slot is None or not is_future(slot):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "השעה הזאת כבר לא זמינה")
    booking = Booking(slot_id=slot.id, name=data.name, phone=data.phone, treatment=data.treatment)
    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        # מישהי אחרת הספיקה לקבוע את השעה הזאת רגע לפני
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "מישהי הספיקה לקבוע את השעה הזאת. בחרי שעה אחרת.")
    return BookingOut(id=booking.id, day=slot.day, start=slot.start, treatment=booking.treatment)


# ---------- מנהלת ----------

@app.post("/api/admin/login", response_model=TokenOut)
async def login(data: LoginIn):
    if not auth.check_password(data.password):
        await asyncio.sleep(1)  # מאט ניסיונות לנחש סיסמה
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "הסיסמה לא נכונה")
    return TokenOut(token=auth.make_token())


def to_admin(slot: Slot) -> AdminSlot:
    b = slot.booking
    return AdminSlot(
        id=slot.id, day=slot.day, start=slot.start,
        booking=AdminBooking(id=b.id, name=b.name, phone=b.phone, treatment=b.treatment, paid=b.paid) if b else None,
    )


@app.get("/api/admin/slots", response_model=list[AdminSlot], dependencies=[Depends(auth.require_admin)])
def admin_slots(include_past: bool = False, db: Session = Depends(get_db)):
    q = select(Slot).options(selectinload(Slot.booking)).order_by(Slot.day, Slot.start)
    if not include_past:
        q = q.where(Slot.day >= now_local().date())
    return [to_admin(s) for s in db.scalars(q).all()]


@app.post("/api/admin/slots", response_model=list[AdminSlot], status_code=status.HTTP_201_CREATED,
          dependencies=[Depends(auth.require_admin)])
def add_slots(data: SlotsIn, db: Session = Depends(get_db)):
    existing = set(db.scalars(select(Slot.start).where(Slot.day == data.day)).all())
    created = []
    for t in sorted(set(data.times)):
        t = t.replace(second=0, microsecond=0)
        if t in existing:
            continue
        slot = Slot(day=data.day, start=t)
        db.add(slot)
        created.append(slot)
        existing.add(t)
    db.commit()
    return [to_admin(s) for s in created]


@app.delete("/api/admin/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT,
            dependencies=[Depends(auth.require_admin)])
def delete_slot(slot_id: int, force: bool = False, db: Session = Depends(get_db)):
    slot = db.get(Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "השעה לא נמצאה")
    if slot.booking is not None and not force:
        raise HTTPException(status.HTTP_409_CONFLICT, "יש תור בשעה הזאת. קודם בטלי את התור.")
    db.delete(slot)
    db.commit()


@app.patch("/api/admin/bookings/{booking_id}", response_model=AdminBooking,
           dependencies=[Depends(auth.require_admin)])
def set_paid(booking_id: int, data: PaidIn, db: Session = Depends(get_db)):
    b = db.get(Booking, booking_id)
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "התור לא נמצא")
    b.paid = data.paid
    db.commit()
    return AdminBooking(id=b.id, name=b.name, phone=b.phone, treatment=b.treatment, paid=b.paid)


@app.delete("/api/admin/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT,
            dependencies=[Depends(auth.require_admin)])
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    b = db.get(Booking, booking_id)
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "התור לא נמצא")
    db.delete(b)
    db.commit()
