"""הטבלאות במסד הנתונים.

slots    - שעות פנויות שהמנהלת מוסיפה
bookings - תורים שלקוחות קבעו. לכל שעה יכול להיות לכל היותר תור אחד
           (unique על slot_id) - כך אי אפשר לקבוע את אותה שעה פעמיים,
           גם אם שתי לקוחות לוחצות "אישור" באותו רגע.
"""
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (UniqueConstraint("day", "start", name="uq_slot_day_start"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    start: Mapped[time] = mapped_column(Time)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    booking: Mapped["Booking | None"] = relationship(
        back_populates="slot", uselist=False, cascade="all, delete-orphan"
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str] = mapped_column(String(20))
    treatment: Mapped[str] = mapped_column(String(60))
    paid: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    slot: Mapped[Slot] = relationship(back_populates="booking")
