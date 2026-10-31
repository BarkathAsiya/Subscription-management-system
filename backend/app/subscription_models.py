import enum
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Float, Text, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def now_utc():
    return datetime.now(timezone.utc)

class SubscriptionStatus(str, enum.Enum):
    draft = "draft"
    quotation = "quotation"
    confirmed = "confirmed"
    active = "active"
    closed = "closed"

class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    confirmed = "confirmed"
    paid = "paid"
    cancelled = "cancelled"

class BillingPeriod(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"

class Quotation(Base):
    __tablename__ = "quotations"
    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(160), default="Subscription quotation")
    status: Mapped[str] = mapped_column(String(24), default="quotation", index=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    items: Mapped[list["QuotationItem"]] = relationship(cascade="all, delete-orphan", back_populates="quotation")

class QuotationItem(Base):
    __tablename__ = "quotation_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[int] = mapped_column(ForeignKey("quotations.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)  # owned by Person 2; snapshot kept below
    product_name: Mapped[str] = mapped_column(String(160))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    tax_percent: Mapped[float] = mapped_column(Float, default=0)
    discount_type: Mapped[str | None] = mapped_column(String(12))
    discount_value: Mapped[float] = mapped_column(Float, default=0)
    line_total: Mapped[float] = mapped_column(Float, default=0)
    quotation: Mapped[Quotation] = relationship(back_populates="items")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    quotation_id: Mapped[int | None] = mapped_column(ForeignKey("quotations.id", ondelete="SET NULL"), nullable=True)
    plan_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)  # owned by Person 2
    plan_name: Mapped[str] = mapped_column(String(160), default="Custom plan")
    billing_period: Mapped[BillingPeriod] = mapped_column(Enum(BillingPeriod), default=BillingPeriod.monthly)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_billing_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.draft, index=True)
    payment_terms: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    items: Mapped[list["SubscriptionItem"]] = relationship(cascade="all, delete-orphan", back_populates="subscription")
    __table_args__ = (Index("ix_sub_customer_status", "customer_id", "status"),)

class SubscriptionItem(Base):
    __tablename__ = "subscription_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    product_name: Mapped[str] = mapped_column(String(160))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    tax_percent: Mapped[float] = mapped_column(Float, default=0)
    discount_type: Mapped[str | None] = mapped_column(String(12))
    discount_value: Mapped[float] = mapped_column(Float, default=0)
    line_total: Mapped[float] = mapped_column(Float, default=0)
    subscription: Mapped[Subscription] = relationship(back_populates="items")

class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    cycle_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.draft, index=True)
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    items: Mapped[list["InvoiceItem"]] = relationship(cascade="all, delete-orphan", back_populates="invoice")
    __table_args__ = (UniqueConstraint("subscription_id", "cycle_key", name="uq_invoice_subscription_cycle"), Index("ix_invoice_customer_status", "customer_id", "status"))

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    product_name: Mapped[str] = mapped_column(String(160))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    tax_percent: Mapped[float] = mapped_column(Float, default=0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0)
    line_total: Mapped[float] = mapped_column(Float, default=0)
    invoice: Mapped[Invoice] = relationship(back_populates="items")
