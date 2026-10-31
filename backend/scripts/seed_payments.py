import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import Base, engine
from app import models, subscription_models, payment_models  # noqa: F401
from app.subscription_models import (
    BillingPeriod, Invoice, InvoiceStatus, Subscription, SubscriptionStatus,
)
from app.payment_models import Payment

COUNT = 300
METHODS = ["cash", "card", "bank_transfer", "upi"]


def main():
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        customer_id = db.scalar(text("SELECT id FROM users ORDER BY id LIMIT 1"))
        if customer_id is None:
            print("No user found. Create a user first, then run this again.")
            return
        if db.scalar(select(Invoice.id).where(Invoice.invoice_number.like("SEED-%"))):
            print("Seed data already exists.")
            return
        now = datetime.now(timezone.utc)
        subs = []
        for i in range(40):
            s = Subscription(
                subscription_number=f"SEED-SUB-{i + 1:04d}",
                customer_id=customer_id,
                plan_name=random.choice(["Basic", "Pro", "Business"]),
                billing_period=BillingPeriod.monthly,
                start_date=now - timedelta(days=random.randint(30, 300)),
                status=SubscriptionStatus.active if i % 5 else SubscriptionStatus.closed,
            )
            db.add(s)
            subs.append(s)
        db.flush()

        for i in range(COUNT):
            issue = now - timedelta(days=random.randint(0, 120))
            total = random.choice([500.0, 1200.0, 2400.0, 5600.0, 9900.0])
            kind = random.choices(["paid", "partial", "unpaid"], weights=[50, 20, 30])[0]
            inv = Invoice(
                invoice_number=f"SEED-INV-{i + 1:05d}",
                customer_id=customer_id,
                subscription_id=random.choice(subs).id,
                cycle_key=f"seed-{i}",
                issue_date=issue,
                due_date=issue + timedelta(days=15),
                status=InvoiceStatus.paid if kind == "paid" else InvoiceStatus.confirmed,
                subtotal=total,
                total=total,
            )
            db.add(inv)
            db.flush()
            if kind != "unpaid":
                amount = total if kind == "paid" else round(total / 2, 2)
                db.add(Payment(
                    invoice_id=inv.id,
                    method=random.choice(METHODS),
                    amount=amount,
                    payment_date=min(now, issue + timedelta(days=random.randint(0, 10))),
                    note="Seed data",
                ))
        db.commit()
        print(f"Added {COUNT} invoices with payments.")


if __name__ == "__main__":
    main()