from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
from .subscription_models import now_utc


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="RESTRICT"), index=True)
    method: Mapped[str] = mapped_column(String(30))
    amount: Mapped[float] = mapped_column(Float)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)