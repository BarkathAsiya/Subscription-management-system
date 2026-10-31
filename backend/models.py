from sqlalchemy import Column, Integer, String, Float, ForeignKey
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
        cascade="all, delete-orphan"
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    additional_price = Column(Float, nullable=False)

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    product = relationship("Product", back_populates="variants")