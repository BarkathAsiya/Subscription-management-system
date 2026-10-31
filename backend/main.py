from datetime import date
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
import models

app = FastAPI(
    title="Subscription Management System (SubSentry AI)",
    description="Product, Plan, Discount, and Tax Management API",
    version="1.0.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

# --- Product & Variant Schemas ---
class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    product_type: str = Field(min_length=1, max_length=100)
    sales_price: float = Field(ge=0)
    cost_price: float = Field(ge=0)
    notes: str = ""


class VariantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    additional_price: float = Field(ge=0)


class VariantUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    additional_price: Optional[float] = Field(default=None, ge=0)


class VariantResponse(BaseModel):
    id: int
    name: str
    additional_price: float
    final_price: float
    product_id: int

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: int
    name: str
    product_type: str
    sales_price: float
    cost_price: float
    notes: str
    variants: list[VariantResponse] = []

    class Config:
        from_attributes = True


# --- Subscription Plan Schemas ---
VALID_BILLING_PERIODS = ["daily", "weekly", "monthly", "yearly"]


class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    billing_period: str = Field(pattern="^(daily|weekly|monthly|yearly)$")
    price: float = Field(ge=0)
    product_id: int
    variant_id: Optional[int] = None
    min_quantity: int = Field(default=1, ge=1)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    allow_pause: bool = True
    allow_renewal: bool = True
    allow_early_close: bool = True
    auto_close_on_condition: bool = False
    is_active: bool = True

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date cannot be after end_date")
        return self


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    billing_period: Optional[str] = Field(default=None, pattern="^(daily|weekly|monthly|yearly)$")
    price: Optional[float] = Field(default=None, ge=0)
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    min_quantity: Optional[int] = Field(default=None, ge=1)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    allow_pause: Optional[bool] = None
    allow_renewal: Optional[bool] = None
    allow_early_close: Optional[bool] = None
    auto_close_on_condition: Optional[bool] = None
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date cannot be after end_date")
        return self


class PlanResponse(BaseModel):
    id: int
    name: str
    description: str
    billing_period: str
    price: float
    product_id: int
    variant_id: Optional[int] = None
    min_quantity: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    allow_pause: bool
    allow_renewal: bool
    allow_early_close: bool
    auto_close_on_condition: bool
    is_active: bool
    product_name: Optional[str] = None
    variant_name: Optional[str] = None

    class Config:
        from_attributes = True


# --- Discount Schemas ---
class DiscountCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    description: str = ""
    discount_type: str = Field(pattern="^(percentage|fixed)$")
    discount_value: float = Field(ge=0)
    min_purchase_amount: float = Field(default=0.0, ge=0)
    min_quantity: int = Field(default=1, ge=1)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    usage_limit: Optional[int] = Field(default=None, ge=1)
    applicable_to: str = Field(default="all", pattern="^(all|product|variant|plan)$")
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    plan_id: Optional[int] = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_discount(self):
        if self.discount_type == "percentage" and self.discount_value > 100.0:
            raise ValueError("Percentage discount cannot exceed 100%")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date")
        return self


class DiscountUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = None
    discount_type: Optional[str] = Field(default=None, pattern="^(percentage|fixed)$")
    discount_value: Optional[float] = Field(default=None, ge=0)
    min_purchase_amount: Optional[float] = Field(default=None, ge=0)
    min_quantity: Optional[int] = Field(default=None, ge=1)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    usage_limit: Optional[int] = Field(default=None, ge=1)
    applicable_to: Optional[str] = Field(default=None, pattern="^(all|product|variant|plan)$")
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    plan_id: Optional[int] = None
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def validate_discount(self):
        if self.discount_type == "percentage" and self.discount_value is not None and self.discount_value > 100.0:
            raise ValueError("Percentage discount cannot exceed 100%")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date")
        return self


class DiscountResponse(BaseModel):
    id: int
    code: str
    description: str
    discount_type: str
    discount_value: float
    min_purchase_amount: float
    min_quantity: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    usage_limit: Optional[int] = None
    times_used: int
    applicable_to: str
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    plan_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


class DiscountValidateRequest(BaseModel):
    code: str = Field(min_length=1)
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    plan_id: Optional[int] = None
    quantity: int = Field(default=1, ge=1)
    subtotal: float = Field(ge=0)


class DiscountValidateResponse(BaseModel):
    is_valid: bool
    code: str
    discount_type: Optional[str] = None
    discount_value: float = 0.0
    discount_amount: float = 0.0
    final_amount: float = 0.0
    reason: Optional[str] = None


# --- Tax Rule Schemas ---
class TaxCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    rate: float = Field(ge=0, le=100)
    applicable_scope: str = Field(default="all", pattern="^(all|product_type|product|plan)$")
    product_type: Optional[str] = None
    product_id: Optional[int] = None
    plan_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_tax_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date")
        return self


class TaxUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    rate: Optional[float] = Field(default=None, ge=0, le=100)
    applicable_scope: Optional[str] = Field(default=None, pattern="^(all|product_type|product|plan)$")
    product_type: Optional[str] = None
    product_id: Optional[int] = None
    plan_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def validate_tax_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date")
        return self


class TaxResponse(BaseModel):
    id: int
    name: str
    description: str
    rate: float
    applicable_scope: str
    product_type: Optional[str] = None
    product_id: Optional[int] = None
    plan_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class TaxCalculateRequest(BaseModel):
    amount: float = Field(ge=0)
    product_id: Optional[int] = None
    product_type: Optional[str] = None
    plan_id: Optional[int] = None


class TaxCalculateResponse(BaseModel):
    amount: float
    applicable_tax_rules: list[TaxResponse]
    combined_rate: float
    tax_amount: float
    total_with_tax: float


# ============================================================================
# API ROUTES
# ============================================================================

@app.get("/")
def home():
    return {
        "system": "Subscription Management System (SubSentry AI)",
        "status": "online",
        "modules": [
            "Products & Variants",
            "Subscription Plans",
            "Discounts & Rules",
            "Tax Rules",
        ],
    }


# ----------------------------------------------------------------------------
# MODULE A: PRODUCTS & VARIANTS
# ----------------------------------------------------------------------------

@app.post("/api/products", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/api/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).order_by(models.Product.id).all()


@app.get("/api/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/api/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    updated_product: ProductCreate,
    db: Session = Depends(get_db),
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in updated_product.model_dump().items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}


@app.post(
    "/api/products/{product_id}/variants",
    response_model=VariantResponse,
    status_code=201,
)
def add_variant(
    product_id: int,
    variant: VariantCreate,
    db: Session = Depends(get_db),
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    db_variant = models.ProductVariant(
        **variant.model_dump(),
        product_id=product_id,
    )
    db.add(db_variant)
    db.commit()
    db.refresh(db_variant)
    return db_variant


@app.get(
    "/api/products/{product_id}/variants",
    response_model=list[VariantResponse],
)
def get_product_variants(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.variants


@app.put(
    "/api/variants/{variant_id}",
    response_model=VariantResponse,
)
def update_variant(
    variant_id: int,
    updated_data: VariantUpdate,
    db: Session = Depends(get_db),
):
    variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == variant_id).first()
    if variant is None:
        raise HTTPException(status_code=404, detail="Variant not found")

    data = updated_data.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is not None:
            setattr(variant, field, value)

    db.commit()
    db.refresh(variant)
    return variant


@app.delete("/api/variants/{variant_id}")
def delete_variant(variant_id: int, db: Session = Depends(get_db)):
    variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == variant_id).first()
    if variant is None:
        raise HTTPException(status_code=404, detail="Variant not found")

    db.delete(variant)
    db.commit()
    return {"message": "Variant deleted successfully"}


# ----------------------------------------------------------------------------
# MODULE B: SUBSCRIPTION PLAN CONFIGURATION
# ----------------------------------------------------------------------------

def _enrich_plan_response(plan: models.SubscriptionPlan) -> dict:
    return {
        "id": plan.id,
        "name": plan.name,
        "description": plan.description,
        "billing_period": plan.billing_period,
        "price": plan.price,
        "product_id": plan.product_id,
        "variant_id": plan.variant_id,
        "min_quantity": plan.min_quantity,
        "start_date": plan.start_date,
        "end_date": plan.end_date,
        "allow_pause": plan.allow_pause,
        "allow_renewal": plan.allow_renewal,
        "allow_early_close": plan.allow_early_close,
        "auto_close_on_condition": plan.auto_close_on_condition,
        "is_active": plan.is_active,
        "product_name": plan.product.name if plan.product else None,
        "variant_name": plan.variant.name if plan.variant else None,
    }


@app.post("/api/plans", response_model=PlanResponse, status_code=201)
def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    # Validate product exists
    product = db.query(models.Product).filter(models.Product.id == plan.product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Associated product not found")

    # If variant specified, validate it belongs to this product
    if plan.variant_id is not None:
        variant = db.query(models.ProductVariant).filter(
            models.ProductVariant.id == plan.variant_id,
            models.ProductVariant.product_id == plan.product_id,
        ).first()
        if variant is None:
            raise HTTPException(status_code=400, detail="Variant not found or does not belong to specified product")

    db_plan = models.SubscriptionPlan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return _enrich_plan_response(db_plan)


@app.get("/api/plans", response_model=list[PlanResponse])
def get_plans(
    product_id: Optional[int] = None,
    billing_period: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.SubscriptionPlan)
    if product_id is not None:
        query = query.filter(models.SubscriptionPlan.product_id == product_id)
    if billing_period is not None:
        query = query.filter(models.SubscriptionPlan.billing_period == billing_period)
    if is_active is not None:
        query = query.filter(models.SubscriptionPlan.is_active == is_active)

    plans = query.order_by(models.SubscriptionPlan.id).all()
    return [_enrich_plan_response(p) for p in plans]


@app.get("/api/plans/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.id == plan_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    return _enrich_plan_response(plan)


@app.put("/api/plans/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: int, updated_plan: PlanUpdate, db: Session = Depends(get_db)):
    plan = db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.id == plan_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")

    data = updated_plan.model_dump(exclude_unset=True)

    target_product_id = data.get("product_id", plan.product_id)
    target_variant_id = data.get("variant_id", plan.variant_id)

    # Validate product if changing
    if "product_id" in data:
        product = db.query(models.Product).filter(models.Product.id == target_product_id).first()
        if product is None:
            raise HTTPException(status_code=404, detail="Associated product not found")

    # Validate variant if present
    if target_variant_id is not None:
        variant = db.query(models.ProductVariant).filter(
            models.ProductVariant.id == target_variant_id,
            models.ProductVariant.product_id == target_product_id,
        ).first()
        if variant is None:
            raise HTTPException(status_code=400, detail="Variant does not belong to specified product")

    for field, value in data.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return _enrich_plan_response(plan)


@app.patch("/api/plans/{plan_id}/status", response_model=PlanResponse)
def toggle_plan_status(plan_id: int, is_active: bool = Query(...), db: Session = Depends(get_db)):
    plan = db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.id == plan_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")

    plan.is_active = is_active
    db.commit()
    db.refresh(plan)
    return _enrich_plan_response(plan)


@app.delete("/api/plans/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.id == plan_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")

    db.delete(plan)
    db.commit()
    return {"message": "Subscription plan deleted successfully"}


# ----------------------------------------------------------------------------
# MODULE C: DISCOUNTS & DISCOUNT RULES
# ----------------------------------------------------------------------------

@app.post("/api/discounts", response_model=DiscountResponse, status_code=201)
def create_discount(discount: DiscountCreate, db: Session = Depends(get_db)):
    existing = db.query(models.DiscountRule).filter(models.DiscountRule.code.ilike(discount.code)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Discount code '{discount.code}' already exists")

    if discount.product_id:
        if not db.query(models.Product).filter(models.Product.id == discount.product_id).first():
            raise HTTPException(status_code=404, detail="Associated product not found")
    if discount.plan_id:
        if not db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.id == discount.plan_id).first():
            raise HTTPException(status_code=404, detail="Associated plan not found")

    db_discount = models.DiscountRule(**discount.model_dump())
    db_discount.code = db_discount.code.upper().strip()
    db.add(db_discount)
    db.commit()
    db.refresh(db_discount)
    return db_discount


@app.get("/api/discounts", response_model=list[DiscountResponse])
def get_discounts(is_active: Optional[bool] = None, db: Session = Depends(get_db)):
    query = db.query(models.DiscountRule)
    if is_active is not None:
        query = query.filter(models.DiscountRule.is_active == is_active)
    return query.order_by(models.DiscountRule.id).all()


@app.get("/api/discounts/{discount_id}", response_model=DiscountResponse)
def get_discount(discount_id: int, db: Session = Depends(get_db)):
    discount = db.query(models.DiscountRule).filter(models.DiscountRule.id == discount_id).first()
    if discount is None:
        raise HTTPException(status_code=404, detail="Discount not found")
    return discount


@app.put("/api/discounts/{discount_id}", response_model=DiscountResponse)
def update_discount(
    discount_id: int,
    updated_discount: DiscountUpdate,
    db: Session = Depends(get_db),
):
    discount = db.query(models.DiscountRule).filter(models.DiscountRule.id == discount_id).first()
    if discount is None:
        raise HTTPException(status_code=404, detail="Discount not found")

    data = updated_discount.model_dump(exclude_unset=True)
    if "code" in data and data["code"] is not None:
        code_upper = data["code"].upper().strip()
        existing = db.query(models.DiscountRule).filter(
            models.DiscountRule.code.ilike(code_upper),
            models.DiscountRule.id != discount_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Discount code '{data['code']}' already in use")
        data["code"] = code_upper

    for field, value in data.items():
        if value is not None:
            setattr(discount, field, value)

    db.commit()
    db.refresh(discount)
    return discount


@app.patch("/api/discounts/{discount_id}/status", response_model=DiscountResponse)
def toggle_discount_status(discount_id: int, is_active: bool = Query(...), db: Session = Depends(get_db)):
    discount = db.query(models.DiscountRule).filter(models.DiscountRule.id == discount_id).first()
    if discount is None:
        raise HTTPException(status_code=404, detail="Discount not found")

    discount.is_active = is_active
    db.commit()
    db.refresh(discount)
    return discount


@app.delete("/api/discounts/{discount_id}")
def delete_discount(discount_id: int, db: Session = Depends(get_db)):
    discount = db.query(models.DiscountRule).filter(models.DiscountRule.id == discount_id).first()
    if discount is None:
        raise HTTPException(status_code=404, detail="Discount not found")

    db.delete(discount)
    db.commit()
    return {"message": "Discount deleted successfully"}


@app.post("/api/discounts/validate", response_model=DiscountValidateResponse)
def validate_discount(req: DiscountValidateRequest, db: Session = Depends(get_db)):
    today_str = date.today().isoformat()
    discount = db.query(models.DiscountRule).filter(
        models.DiscountRule.code.ilike(req.code.strip())
    ).first()

    if not discount:
        return DiscountValidateResponse(
            is_valid=False,
            code=req.code,
            discount_amount=0.0,
            final_amount=req.subtotal,
            reason="Invalid discount code",
        )

    if not discount.is_active:
        return DiscountValidateResponse(
            is_valid=False,
            code=discount.code,
            reason="Discount is inactive",
            final_amount=req.subtotal,
        )

    # Date range validation
    if discount.start_date and today_str < discount.start_date:
        return DiscountValidateResponse(
            is_valid=False,
            code=discount.code,
            reason=f"Discount not valid until {discount.start_date}",
            final_amount=req.subtotal,
        )

    if discount.end_date and today_str > discount.end_date:
        return DiscountValidateResponse(
            is_valid=False,
            code=discount.code,
            reason=f"Discount expired on {discount.end_date}",
            final_amount=req.subtotal,
        )

    # Usage limits
    if discount.usage_limit is not None and discount.times_used >= discount.usage_limit:
        return DiscountValidateResponse(
            is_valid=False,
            code=discount.code,
            reason="Discount usage limit has been reached",
            final_amount=req.subtotal,
        )

    # Minimum purchase amount
    if req.subtotal < discount.min_purchase_amount:
        return DiscountValidateResponse(
            is_valid=False,
            code=discount.code,
            reason=f"Minimum purchase amount of ₹{discount.min_purchase_amount:,.2f} required",
            final_amount=req.subtotal,
        )

    # Minimum quantity
    if req.quantity < discount.min_quantity:
        return DiscountValidateResponse(
            is_valid=False,
            code=discount.code,
            reason=f"Minimum quantity of {discount.min_quantity} items required",
            final_amount=req.subtotal,
        )

    # Applicability check
    if discount.applicable_to == "product" and discount.product_id:
        if req.product_id != discount.product_id:
            return DiscountValidateResponse(
                is_valid=False,
                code=discount.code,
                reason="Discount does not apply to this product",
                final_amount=req.subtotal,
            )

    if discount.applicable_to == "variant" and discount.variant_id:
        if req.variant_id != discount.variant_id:
            return DiscountValidateResponse(
                is_valid=False,
                code=discount.code,
                reason="Discount does not apply to this variant",
                final_amount=req.subtotal,
            )

    if discount.applicable_to == "plan" and discount.plan_id:
        if req.plan_id != discount.plan_id:
            return DiscountValidateResponse(
                is_valid=False,
                code=discount.code,
                reason="Discount does not apply to this subscription plan",
                final_amount=req.subtotal,
            )

    # Calculate discount amount
    if discount.discount_type == "percentage":
        discount_amount = round(req.subtotal * (discount.discount_value / 100.0), 2)
    else:  # fixed
        discount_amount = min(req.subtotal, round(discount.discount_value, 2))

    final_amount = max(0.0, round(req.subtotal - discount_amount, 2))

    return DiscountValidateResponse(
        is_valid=True,
        code=discount.code,
        discount_type=discount.discount_type,
        discount_value=discount.discount_value,
        discount_amount=discount_amount,
        final_amount=final_amount,
        reason=None,
    )


# ----------------------------------------------------------------------------
# MODULE D: TAX RULES
# ----------------------------------------------------------------------------

@app.post("/api/taxes", response_model=TaxResponse, status_code=201)
def create_tax(tax: TaxCreate, db: Session = Depends(get_db)):
    if tax.product_id:
        if not db.query(models.Product).filter(models.Product.id == tax.product_id).first():
            raise HTTPException(status_code=404, detail="Associated product not found")
    if tax.plan_id:
        if not db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.id == tax.plan_id).first():
            raise HTTPException(status_code=404, detail="Associated plan not found")

    db_tax = models.TaxRule(**tax.model_dump())
    db.add(db_tax)
    db.commit()
    db.refresh(db_tax)
    return db_tax


@app.get("/api/taxes", response_model=list[TaxResponse])
def get_taxes(
    applicable_scope: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.TaxRule)
    if applicable_scope is not None:
        query = query.filter(models.TaxRule.applicable_scope == applicable_scope)
    if is_active is not None:
        query = query.filter(models.TaxRule.is_active == is_active)

    return query.order_by(models.TaxRule.id).all()


@app.get("/api/taxes/{tax_id}", response_model=TaxResponse)
def get_tax(tax_id: int, db: Session = Depends(get_db)):
    tax = db.query(models.TaxRule).filter(models.TaxRule.id == tax_id).first()
    if tax is None:
        raise HTTPException(status_code=404, detail="Tax rule not found")
    return tax


@app.put("/api/taxes/{tax_id}", response_model=TaxResponse)
def update_tax(
    tax_id: int,
    updated_tax: TaxUpdate,
    db: Session = Depends(get_db),
):
    tax = db.query(models.TaxRule).filter(models.TaxRule.id == tax_id).first()
    if tax is None:
        raise HTTPException(status_code=404, detail="Tax rule not found")

    data = updated_tax.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is not None:
            setattr(tax, field, value)

    db.commit()
    db.refresh(tax)
    return tax


@app.patch("/api/taxes/{tax_id}/status", response_model=TaxResponse)
def toggle_tax_status(tax_id: int, is_active: bool = Query(...), db: Session = Depends(get_db)):
    tax = db.query(models.TaxRule).filter(models.TaxRule.id == tax_id).first()
    if tax is None:
        raise HTTPException(status_code=404, detail="Tax rule not found")

    tax.is_active = is_active
    db.commit()
    db.refresh(tax)
    return tax


@app.delete("/api/taxes/{tax_id}")
def delete_tax(tax_id: int, db: Session = Depends(get_db)):
    tax = db.query(models.TaxRule).filter(models.TaxRule.id == tax_id).first()
    if tax is None:
        raise HTTPException(status_code=404, detail="Tax rule not found")

    db.delete(tax)
    db.commit()
    return {"message": "Tax rule deleted successfully"}


@app.post("/api/taxes/calculate", response_model=TaxCalculateResponse)
def calculate_tax(req: TaxCalculateRequest, db: Session = Depends(get_db)):
    today_str = date.today().isoformat()
    # Query all active tax rules
    all_active = db.query(models.TaxRule).filter(models.TaxRule.is_active == True).all()

    matching_rules: list[models.TaxRule] = []
    for rule in all_active:
        # Check date range
        if rule.start_date and today_str < rule.start_date:
            continue
        if rule.end_date and today_str > rule.end_date:
            continue

        # Check scope match
        if rule.applicable_scope == "all":
            matching_rules.append(rule)
        elif rule.applicable_scope == "product_type" and req.product_type:
            if rule.product_type and rule.product_type.lower() == req.product_type.lower():
                matching_rules.append(rule)
        elif rule.applicable_scope == "product" and req.product_id:
            if rule.product_id == req.product_id:
                matching_rules.append(rule)
        elif rule.applicable_scope == "plan" and req.plan_id:
            if rule.plan_id == req.plan_id:
                matching_rules.append(rule)

    combined_rate = sum(r.rate for r in matching_rules)
    tax_amount = round(req.amount * (combined_rate / 100.0), 2)
    total_with_tax = round(req.amount + tax_amount, 2)

    return TaxCalculateResponse(
        amount=req.amount,
        applicable_tax_rules=matching_rules,
        combined_rate=combined_rate,
        tax_amount=tax_amount,
        total_with_tax=total_with_tax,
    )
