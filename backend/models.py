from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    product_type = Column(String(100), nullable=False)
    sales_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    notes = Column(String, default="")

    variants = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVariant.id",
    )

    plans = relationship(
        "SubscriptionPlan",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="SubscriptionPlan.id",
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    additional_price = Column(Float, nullable=False)

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )

    product = relationship("Product", back_populates="variants")

    @property
    def final_price(self) -> float:
        if self.product:
            return round(self.product.sales_price + self.additional_price, 2)
        return round(self.additional_price, 2)


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String, default="")
    billing_period = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    price = Column(Float, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    min_quantity = Column(Integer, default=1, nullable=False)
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    allow_pause = Column(Boolean, default=True, nullable=False)
    allow_renewal = Column(Boolean, default=True, nullable=False)
    allow_early_close = Column(Boolean, default=True, nullable=False)
    auto_close_on_condition = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    product = relationship("Product", back_populates="plans")
    variant = relationship("ProductVariant")


class DiscountRule(Base):
    __tablename__ = "discount_rules"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String, default="")
    discount_type = Column(String(20), nullable=False)  # percentage, fixed
    discount_value = Column(Float, nullable=False)
    min_purchase_amount = Column(Float, default=0.0, nullable=False)
    min_quantity = Column(Integer, default=1, nullable=False)
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    usage_limit = Column(Integer, nullable=True)
    times_used = Column(Integer, default=0, nullable=False)
    applicable_to = Column(String(20), default="all", nullable=False)  # all, product, variant, plan
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    product = relationship("Product")
    variant = relationship("ProductVariant")
    plan = relationship("SubscriptionPlan")


class TaxRule(Base):
    __tablename__ = "tax_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String, default="")
    rate = Column(Float, nullable=False)  # Percentage, e.g. 5.0, 18.0
    applicable_scope = Column(String(20), default="all", nullable=False)  # all, product_type, product, plan
    product_type = Column(String(100), nullable=True)  # Physical, Service, etc.
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    product = relationship("Product")
    plan = relationship("SubscriptionPlan")
