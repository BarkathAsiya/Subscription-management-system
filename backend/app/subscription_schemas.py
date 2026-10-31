from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from .subscription_models import BillingPeriod, SubscriptionStatus, InvoiceStatus

class LineIn(BaseModel):
    product_id: int | None = None
    product_name: str = Field(min_length=1, max_length=160)
    quantity: int = Field(ge=1, le=100000)
    unit_price: float = Field(ge=0)
    tax_percent: float = Field(default=0, ge=0, le=100)
    discount_type: Literal['fixed', 'percent'] | None = None
    discount_value: float = Field(default=0, ge=0)

class QuotationCreate(BaseModel):
    customer_id: int
    title: str = Field(default='Subscription quotation', max_length=160)
    valid_until: datetime | None = None
    notes: str | None = None
    items: list[LineIn] = Field(min_length=1)

class SubscriptionCreate(BaseModel):
    customer_id: int
    quotation_id: int | None = None
    plan_id: int | None = None
    plan_name: str = Field(default='Custom plan', max_length=160)
    billing_period: BillingPeriod = BillingPeriod.monthly
    start_date: datetime
    expiry_date: datetime | None = None
    payment_terms: str | None = None
    notes: str | None = None
    auto_renew: bool = True
    items: list[LineIn] = Field(min_length=1)

class StatusUpdate(BaseModel):
    status: SubscriptionStatus

class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus

class InvoiceSendRequest(BaseModel):
    recipient_email: str | None = None

class ORMOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class QuotationConvert(BaseModel):
    plan_name: str = Field(default="Custom plan", max_length=160)
    billing_period: BillingPeriod = BillingPeriod.monthly
    start_date: datetime
    expiry_date: datetime | None = None
    payment_terms: str | None = None
    auto_renew: bool = True
