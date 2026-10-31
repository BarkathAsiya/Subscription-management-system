import calendar
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
import smtplib
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import User, UserRole
from ..config import settings
from ..subscription_models import (Quotation, QuotationItem, Subscription, SubscriptionItem, Invoice, InvoiceItem,
    SubscriptionStatus, InvoiceStatus, BillingPeriod)
from ..subscription_schemas import QuotationCreate, SubscriptionCreate, StatusUpdate, InvoiceStatusUpdate, QuotationConvert

router = APIRouter(prefix="/api", tags=["Subscriptions and invoices"])
STAFF = require_roles(UserRole.admin, UserRole.staff)


def money(value: float) -> float:
    return round(float(value) + 1e-9, 2)

def calc_line(line):
    gross = line.quantity * line.unit_price
    dtype = line.discount_type
    dvalue = line.discount_value or 0
    if dtype == "percent" and dvalue > 100:
        raise HTTPException(422, "Line discount percentage cannot exceed 100.")
    discount = min(gross, gross * dvalue / 100 if dtype == "percent" else dvalue if dtype == "fixed" else 0)
    taxable = max(0, gross - discount)
    tax = taxable * line.tax_percent / 100
    return money(gross), money(discount), money(tax), money(taxable + tax)

def totals(items):
    subtotal = discount = tax = total = 0.0
    for item in items:
        gross, disc, tax_part, line_total = calc_line(item)
        subtotal += gross; discount += disc; tax += tax_part; total += line_total
    return money(subtotal), money(discount), money(tax), money(total)

def validate_customer(db: Session, customer_id: int):
    customer = db.query(User).filter(User.id == customer_id, User.role == UserRole.customer, User.is_active.is_(True)).first()
    if not customer:
        raise HTTPException(404, "Active customer account not found.")
    return customer

def can_view(user: User, customer_id: int):
    if user.role == UserRole.customer and user.id != customer_id:
        raise HTTPException(403, "Customers can only access their own records.")

def add_items(parent, lines, item_class):
    for line in lines:
        _, disc, _, line_total = calc_line(line)
        parent.items.append(item_class(product_id=line.product_id, product_name=line.product_name.strip(),
            quantity=line.quantity, unit_price=line.unit_price, tax_percent=line.tax_percent,
            discount_type=line.discount_type, discount_value=line.discount_value, line_total=line_total))

def invoice_from_subscription(db: Session, sub: Subscription, cycle_key: str, issue_date: datetime):
    # The unique (subscription_id, cycle_key) constraint is the final idempotency guard.
    existing = db.query(Invoice).filter(Invoice.subscription_id == sub.id, Invoice.cycle_key == cycle_key).first()
    if existing:
        return existing, False
    invoice = Invoice(invoice_number=f"INV-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:6].upper()}",
        customer_id=sub.customer_id, subscription_id=sub.id, cycle_key=cycle_key,
        issue_date=issue_date, due_date=issue_date + timedelta(days=7), status=InvoiceStatus.draft,
        notes=f"Automatically generated for {sub.subscription_number}")
    for item in sub.items:
        gross = item.quantity * item.unit_price
        discount = min(gross, gross * item.discount_value / 100 if item.discount_type == "percent" else item.discount_value if item.discount_type == "fixed" else 0)
        taxable = max(0, gross - discount)
        tax = taxable * item.tax_percent / 100
        invoice.items.append(InvoiceItem(product_id=item.product_id, product_name=item.product_name,
            quantity=item.quantity, unit_price=item.unit_price, tax_percent=item.tax_percent,
            discount_amount=money(discount), line_total=money(taxable + tax)))
    invoice.subtotal = money(sum(x.quantity * x.unit_price for x in sub.items))
    invoice.discount_amount = money(sum(x.discount_amount for x in invoice.items))
    invoice.tax_amount = money(sum((x.quantity*x.unit_price-x.discount_amount)*x.tax_percent/100 for x in invoice.items))
    invoice.total = money(sum(x.line_total for x in invoice.items))
    db.add(invoice)
    return invoice, True

def add_period(value: datetime, period: BillingPeriod):
    if period == BillingPeriod.daily: return value + timedelta(days=1)
    if period == BillingPeriod.weekly: return value + timedelta(weeks=1)
    if period == BillingPeriod.yearly:
        year = value.year + 1
        day = min(value.day, calendar.monthrange(year, value.month)[1])
        return value.replace(year=year, day=day)
    month = value.month + 1
    year = value.year + (1 if month > 12 else 0)
    month = 1 if month > 12 else month
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)

def quotation_out(q: Quotation):
    return {"id": q.id, "quotation_number": q.quotation_number, "customer_id": q.customer_id, "title": q.title,
        "status": q.status, "valid_until": q.valid_until, "notes": q.notes, "subtotal": q.subtotal,
        "discount_amount": q.discount_amount, "tax_amount": q.tax_amount, "total": q.total,
        "created_at": q.created_at, "items": [{"id": i.id, "product_id": i.product_id, "product_name": i.product_name,
        "quantity": i.quantity, "unit_price": i.unit_price, "tax_percent": i.tax_percent,
        "discount_type": i.discount_type, "discount_value": i.discount_value, "line_total": i.line_total} for i in q.items]}

def subscription_out(s: Subscription):
    return {"id": s.id, "subscription_number": s.subscription_number, "customer_id": s.customer_id,
        "quotation_id": s.quotation_id, "plan_id": s.plan_id, "plan_name": s.plan_name,
        "billing_period": s.billing_period.value, "start_date": s.start_date, "expiry_date": s.expiry_date,
        "next_billing_date": s.next_billing_date, "status": s.status.value, "payment_terms": s.payment_terms,
        "auto_renew": s.auto_renew, "notes": s.notes, "created_at": s.created_at,
        "items": [{"id": i.id, "product_id": i.product_id, "product_name": i.product_name, "quantity": i.quantity,
        "unit_price": i.unit_price, "tax_percent": i.tax_percent, "discount_type": i.discount_type,
        "discount_value": i.discount_value, "line_total": i.line_total} for i in s.items]}

def invoice_out(i: Invoice):
    return {"id": i.id, "invoice_number": i.invoice_number, "customer_id": i.customer_id,
        "subscription_id": i.subscription_id, "cycle_key": i.cycle_key, "issue_date": i.issue_date,
        "due_date": i.due_date, "status": i.status.value, "subtotal": i.subtotal,
        "discount_amount": i.discount_amount, "tax_amount": i.tax_amount, "total": i.total,
        "notes": i.notes, "items": [{"id": x.id, "product_name": x.product_name, "quantity": x.quantity,
        "unit_price": x.unit_price, "tax_percent": x.tax_percent, "discount_amount": x.discount_amount,
        "line_total": x.line_total} for x in i.items]}

@router.get("/billing/customers")
def list_billing_customers(db: Session = Depends(get_db), user: User = Depends(STAFF)):
    rows = db.query(User).filter(User.role == UserRole.customer, User.is_active.is_(True)).order_by(User.full_name.asc()).all()
    return [{"id": x.id, "full_name": x.full_name, "email": x.email} for x in rows]

@router.post("/quotations", status_code=201)
def create_quotation(payload: QuotationCreate, db: Session = Depends(get_db), user: User = Depends(STAFF)):
    validate_customer(db, payload.customer_id)
    subtotal, discount, tax, total = totals(payload.items)
    q = Quotation(quotation_number=f"QUO-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:6].upper()}",
        customer_id=payload.customer_id, title=payload.title, valid_until=payload.valid_until, notes=payload.notes,
        subtotal=subtotal, discount_amount=discount, tax_amount=tax, total=total)
    add_items(q, payload.items, QuotationItem)
    db.add(q); db.commit(); db.refresh(q)
    return quotation_out(q)

@router.post("/quotations/{quotation_id}/convert", status_code=201)
def convert_quotation(quotation_id: int, payload: QuotationConvert, db: Session = Depends(get_db), user: User = Depends(STAFF)):
    quotation = db.query(Quotation).options(joinedload(Quotation.items)).filter(Quotation.id == quotation_id).first()
    if not quotation: raise HTTPException(404, "Quotation not found.")
    if quotation.status == "converted": raise HTTPException(409, "This quotation has already been converted.")
    if quotation.valid_until and quotation.valid_until < datetime.now(timezone.utc):
        raise HTTPException(409, "This quotation has expired.")
    if payload.expiry_date and payload.expiry_date <= payload.start_date:
        raise HTTPException(422, "Expiry date must be after start date.")
    sub = Subscription(subscription_number=f"SUB-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:6].upper()}",
        customer_id=quotation.customer_id, quotation_id=quotation.id, plan_name=payload.plan_name,
        billing_period=payload.billing_period, start_date=payload.start_date, expiry_date=payload.expiry_date,
        next_billing_date=payload.start_date, status=SubscriptionStatus.draft, payment_terms=payload.payment_terms,
        auto_renew=payload.auto_renew, notes=f"Created from {quotation.quotation_number}")
    for item in quotation.items:
        sub.items.append(SubscriptionItem(product_id=item.product_id, product_name=item.product_name,
            quantity=item.quantity, unit_price=item.unit_price, tax_percent=item.tax_percent,
            discount_type=item.discount_type, discount_value=item.discount_value, line_total=item.line_total))
    quotation.status = "converted"
    db.add(sub); db.commit(); db.refresh(sub)
    return subscription_out(sub)

@router.get("/quotations")
def list_quotations(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Quotation).options(joinedload(Quotation.items))
    if user.role == UserRole.customer: query = query.filter(Quotation.customer_id == user.id)
    rows = query.order_by(Quotation.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"items": [quotation_out(x) for x in rows], "page": page, "page_size": page_size}

@router.post("/subscriptions", status_code=201)
def create_subscription(payload: SubscriptionCreate, db: Session = Depends(get_db), user: User = Depends(STAFF)):
    validate_customer(db, payload.customer_id)
    if payload.expiry_date and payload.expiry_date <= payload.start_date:
        raise HTTPException(422, "Expiry date must be after start date.")
    quotation = None
    if payload.quotation_id:
        quotation = db.query(Quotation).filter(Quotation.id == payload.quotation_id).first()
        if not quotation: raise HTTPException(404, "Quotation not found.")
        if quotation.customer_id != payload.customer_id: raise HTTPException(422, "Quotation belongs to a different customer.")
        if not payload.items: raise HTTPException(422, "At least one subscription line is required.")
    sub = Subscription(subscription_number=f"SUB-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:6].upper()}",
        customer_id=payload.customer_id, quotation_id=payload.quotation_id, plan_id=payload.plan_id,
        plan_name=payload.plan_name, billing_period=payload.billing_period, start_date=payload.start_date,
        expiry_date=payload.expiry_date, next_billing_date=payload.start_date, status=SubscriptionStatus.draft,
        payment_terms=payload.payment_terms, notes=payload.notes, auto_renew=payload.auto_renew)
    add_items(sub, payload.items, SubscriptionItem)
    db.add(sub)
    if quotation: quotation.status = "converted"
    db.commit(); db.refresh(sub)
    return subscription_out(sub)

@router.get("/subscriptions")
def list_subscriptions(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status: SubscriptionStatus | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Subscription).options(joinedload(Subscription.items))
    if user.role == UserRole.customer: query = query.filter(Subscription.customer_id == user.id)
    if status: query = query.filter(Subscription.status == status)
    rows = query.order_by(Subscription.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"items": [subscription_out(x) for x in rows], "page": page, "page_size": page_size}

@router.patch("/subscriptions/{subscription_id}/status")
def update_subscription_status(subscription_id: int, payload: StatusUpdate, db: Session = Depends(get_db), user: User = Depends(STAFF)):
    sub = db.query(Subscription).options(joinedload(Subscription.items)).filter(Subscription.id == subscription_id).first()
    if not sub: raise HTTPException(404, "Subscription not found.")
    allowed = {SubscriptionStatus.draft: {SubscriptionStatus.quotation},
        SubscriptionStatus.quotation: {SubscriptionStatus.confirmed, SubscriptionStatus.draft},
        SubscriptionStatus.confirmed: {SubscriptionStatus.active, SubscriptionStatus.closed},
        SubscriptionStatus.active: {SubscriptionStatus.closed}, SubscriptionStatus.closed: set()}
    if payload.status not in allowed[sub.status]:
        raise HTTPException(409, f"Cannot move subscription from {sub.status.value} to {payload.status.value}.")
    sub.status = payload.status
    if payload.status == SubscriptionStatus.active and not sub.next_billing_date: sub.next_billing_date = sub.start_date
    db.commit(); db.refresh(sub)
    return subscription_out(sub)

@router.post("/billing/run")
def run_billing(db: Session = Depends(get_db), user: User = Depends(STAFF)):
    """Generate all due invoices. Safe to run repeatedly: one invoice per subscription billing cycle."""
    now = datetime.now(timezone.utc)
    due = db.query(Subscription).options(joinedload(Subscription.items)).filter(
        Subscription.status == SubscriptionStatus.active, Subscription.next_billing_date <= now).all()
    created, skipped = [], 0
    for sub in due:
        cycle = sub.next_billing_date.date().isoformat()
        invoice, was_created = invoice_from_subscription(db, sub, cycle, now)
        if was_created: created.append(invoice.invoice_number)
        else: skipped += 1
        next_date = add_period(sub.next_billing_date, sub.billing_period)
        if sub.expiry_date and next_date > sub.expiry_date:
            sub.status = SubscriptionStatus.closed
            sub.next_billing_date = None
        elif not sub.auto_renew:
            sub.status = SubscriptionStatus.closed
            sub.next_billing_date = None
        else:
            sub.next_billing_date = next_date
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A billing cycle was already processed concurrently. Run billing again to process remaining subscriptions.")
    return {"created_count": len(created), "skipped_existing_count": skipped, "invoice_numbers": created}

@router.get("/invoices")
def list_invoices(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status: InvoiceStatus | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Invoice).options(joinedload(Invoice.items))
    if user.role == UserRole.customer: query = query.filter(Invoice.customer_id == user.id)
    if status: query = query.filter(Invoice.status == status)
    rows = query.order_by(Invoice.issue_date.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"items": [invoice_out(x) for x in rows], "page": page, "page_size": page_size}

@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    invoice = db.query(Invoice).options(joinedload(Invoice.items)).filter(Invoice.id == invoice_id).first()
    if not invoice: raise HTTPException(404, "Invoice not found.")
    can_view(user, invoice.customer_id)
    return invoice_out(invoice)

@router.patch("/invoices/{invoice_id}/status")
def update_invoice_status(invoice_id: int, payload: InvoiceStatusUpdate, db: Session = Depends(get_db), user: User = Depends(STAFF)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice: raise HTTPException(404, "Invoice not found.")
    allowed = {InvoiceStatus.draft: {InvoiceStatus.confirmed, InvoiceStatus.cancelled},
        InvoiceStatus.confirmed: {InvoiceStatus.paid, InvoiceStatus.cancelled},
        InvoiceStatus.paid: set(), InvoiceStatus.cancelled: set()}
    if payload.status not in allowed[invoice.status]:
        raise HTTPException(409, f"Cannot move invoice from {invoice.status.value} to {payload.status.value}.")
    invoice.status = payload.status
    db.commit(); db.refresh(invoice)
    return invoice_out(invoice)

@router.post("/invoices/{invoice_id}/send")
def send_invoice(invoice_id: int, db: Session = Depends(get_db), user: User = Depends(STAFF)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice: raise HTTPException(404, "Invoice not found.")
    customer = db.query(User).filter(User.id == invoice.customer_id).first()
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from]):
        raise HTTPException(503, "Email is not configured. Add SMTP settings to backend/.env.")
    message = EmailMessage(); message["Subject"] = f"SubSentry AI invoice {invoice.invoice_number}"
    message["From"] = settings.smtp_from; message["To"] = customer.email
    message.set_content(f"Hello {customer.full_name},\n\nYour invoice {invoice.invoice_number} totals ₹{invoice.total:.2f}.\nDue date: {invoice.due_date}.\n\nPlease contact the billing team for payment assistance.")
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls(); server.login(settings.smtp_username, settings.smtp_password); server.send_message(message)
    except Exception as exc:
        raise HTTPException(502, "Invoice email could not be sent. Check SMTP settings.") from exc
    return {"message": f"Invoice sent to {customer.email}."}
