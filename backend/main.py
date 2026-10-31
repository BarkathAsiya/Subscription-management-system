from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
import models

app = FastAPI(
    title="Subscription Management System",
    description="Product Management API",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    product_type: str = Field(min_length=1, max_length=100)
    sales_price: float = Field(ge=0)
    cost_price: float = Field(ge=0)
    notes: str = ""


class VariantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    additional_price: float = Field(ge=0)


class VariantResponse(BaseModel):
    id: int
    name: str
    additional_price: float
    final_price: float

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: int
    name: str
    product_type: str
    sales_price: float
    cost_price: float
    notes: str
    variants: list[VariantResponse]

    class Config:
        from_attributes = True


@app.get("/")
def home():
    return {"message": "Subscription Management System API is running!"}


@app.post("/api/products", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(**product.model_dump())

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return db_product


@app.get("/api/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()


@app.get("/api/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@app.put("/api/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    updated_product: ProductCreate,
    db: Session = Depends(get_db),
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in updated_product.model_dump().items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

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
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

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
