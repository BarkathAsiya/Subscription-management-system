from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_roles
from ..models import UserRole
from ..payment_models import Payment
from ..subscription_models import Invoice, InvoiceStatus, Subscription, SubscriptionStatus

STAFF_ROLES = [r for r in UserRole if r.value != "customer"]
router = APIRouter(
    tags=["Payments & Reports"],
    dependencies=[Depends(require_roles(*STAFF_ROLES))],
)
Method = Literal["cash", "card", "bank_transfer", "upi", "other"]


class PaymentIn(BaseModel):
    invoice_id: int
    method: Method
    amount: float = Field(gt=0)
    payment_date: datetime | None = None
    note: str | None = None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    invoice_id: int
    method: str
    amount: float
    payment_date: datetime
    note: str | None = None


class InvoiceRow(BaseModel):
    id: int
    invoice_number: str
    customer_id: int
    subscription_id: int | None
    issue_date: datetime
    due_date: datetime | None
    status: str
    total: float
    amount_paid: float
    balance: float
    is_overdue: bool


class InvoicePage(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[InvoiceRow]


def _aware(dt):
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _date_conds(col, date_from, date_to):
    conds = []
    if date_from:
        conds.append(col >= date_from)
    if date_to:
        conds.append(col <= date_to)
    return conds


@router.post("/payments", response_model=PaymentOut, status_code=201)
def record_payment(body: PaymentIn, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, body.invoice_id)
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    if invoice.status == InvoiceStatus.paid:
        raise HTTPException(400, "Invoice is already paid")
    if invoice.status != InvoiceStatus.confirmed:
        raise HTTPException(400, "Only confirmed invoices can receive payments")
    paid = db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.invoice_id == invoice.id))
    balance = round(invoice.total - paid, 2)
    if body.amount > balance + 0.005:
        raise HTTPException(400, f"Amount exceeds the remaining balance of {balance}")
    when = body.payment_date
    if when is not None and when.tzinfo is not None:
        when = when.astimezone(timezone.utc)
    payment = Payment(
        invoice_id=invoice.id,
        method=body.method,
        amount=body.amount,
        payment_date=when or datetime.now(timezone.utc),
        note=body.note,
    )
    db.add(payment)
    if round(paid + body.amount, 2) >= round(invoice.total, 2):
        invoice.status = InvoiceStatus.paid
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/payments", response_model=list[PaymentOut])
def list_payments(
    invoice_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = select(Payment).order_by(Payment.payment_date.desc(), Payment.id.desc())
    if invoice_id:
        q = q.where(Payment.invoice_id == invoice_id)
    return db.scalars(q.offset(skip).limit(limit)).all()


@router.get("/reports/invoices", response_model=InvoicePage)
def invoice_report(
    status_filter: Literal["paid", "outstanding", "overdue"] | None = Query(None, alias="status"),
    customer_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    conds = _date_conds(Invoice.issue_date, date_from, date_to)
    if customer_id:
        conds.append(Invoice.customer_id == customer_id)
    if status_filter == "paid":
        conds.append(Invoice.status == InvoiceStatus.paid)
    elif status_filter == "outstanding":
        conds.append(Invoice.status == InvoiceStatus.confirmed)
    elif status_filter == "overdue":
        conds += [Invoice.status == InvoiceStatus.confirmed, Invoice.due_date < now]

    paid_sub = (
        select(Payment.invoice_id.label("invoice_id"), func.sum(Payment.amount).label("paid"))
        .group_by(Payment.invoice_id)
        .subquery()
    )
    total = db.scalar(select(func.count(Invoice.id)).where(*conds)) or 0
    rows = db.execute(
        select(Invoice, func.coalesce(paid_sub.c.paid, 0))
        .outerjoin(paid_sub, paid_sub.c.invoice_id == Invoice.id)
        .where(*conds)
        .order_by(Invoice.due_date.asc(), Invoice.id.asc())
        .offset(skip)
        .limit(limit)
    ).all()

    items = []
    for inv, paid in rows:
        due = _aware(inv.due_date)
        items.append(InvoiceRow(
            id=inv.id,
            invoice_number=inv.invoice_number,
            customer_id=inv.customer_id,
            subscription_id=inv.subscription_id,
            issue_date=inv.issue_date,
            due_date=inv.due_date,
            status=inv.status.value,
            total=inv.total,
            amount_paid=round(float(paid), 2),
            balance=round(inv.total - float(paid), 2),
            is_overdue=bool(inv.status == InvoiceStatus.confirmed and due and due < now),
        ))
    return InvoicePage(total=total, skip=skip, limit=limit, items=items)


def _owed(db, *conds):
    base = (Invoice.status == InvoiceStatus.confirmed, *conds)
    count = db.scalar(select(func.count(Invoice.id)).where(*base)) or 0
    billed = db.scalar(select(func.coalesce(func.sum(Invoice.total), 0)).where(*base))
    paid = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .select_from(Payment)
        .join(Invoice, Invoice.id == Payment.invoice_id)
        .where(*base)
    )
    return count, round(float(billed) - float(paid), 2)


@router.get("/reports/summary")
def summary(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    inv_dates = _date_conds(Invoice.issue_date, date_from, date_to)
    pay_dates = _date_conds(Payment.payment_date, date_from, date_to)

    active = db.scalar(
        select(func.count(Subscription.id)).where(Subscription.status == SubscriptionStatus.active)
    ) or 0
    revenue, pay_count = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0), func.count(Payment.id)).where(*pay_dates)
    ).one()
    out_count, out_amount = _owed(db, *inv_dates)
    od_count, od_amount = _owed(db, Invoice.due_date < now, *inv_dates)
    by_status = {
        k.value: v
        for k, v in db.execute(
            select(Invoice.status, func.count(Invoice.id)).where(*inv_dates).group_by(Invoice.status)
        ).all()
    }
    return {
        "active_subscriptions": active,
        "revenue_collected": round(float(revenue), 2),
        "payments_count": pay_count,
        "outstanding_invoices": out_count,
        "amount_owed": out_amount,
        "overdue_invoices": od_count,
        "overdue_amount": od_amount,
        "invoices_by_status": by_status,
    }