from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Subscription Management System",
    description="Product Management API",
    version="1.0.0",
)


class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    product_type: str = Field(min_length=1)
    sales_price: float = Field(ge=0)
    cost_price: float = Field(ge=0)
    notes: str = ""


class ProductVariant(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    additional_price: float = Field(ge=0)


products = {}
next_product_id = 1


@app.get("/")
def home():
    return {"message": "Subscription Management System API is running!"}


@app.post("/api/products", status_code=201)
def create_product(product: Product):
    global next_product_id

    product_id = next_product_id
    products[product_id] = {
        "id": product_id,
        **product.model_dump(),
        "variants": [],
    }

    next_product_id += 1

    return products[product_id]


@app.get("/api/products")
def get_products():
    return list(products.values())


@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    product = products.get(product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@app.put("/api/products/{product_id}")
def update_product(product_id: int, updated_product: Product):
    product = products.get(product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    product.update(updated_product.model_dump())

    return product


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int):
    product = products.pop(product_id, None)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Product deleted successfully"}


@app.post("/api/products/{product_id}/variants", status_code=201)
def add_variant(product_id: int, variant: ProductVariant):
    product = products.get(product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    variant_data = {
        "id": len(product["variants"]) + 1,
        **variant.model_dump(),
    }

    product["variants"].append(variant_data)

    return {
        **variant_data,
        "final_price": product["sales_price"] + variant_data["additional_price"],
    }