import sys
from pathlib import Path

# Configure utf-8 encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from sqlalchemy import text
import database
import models
from main import app

def run_tests():
    print("=" * 60)
    print("STARTING PRODUCT VARIANT VERIFICATION AND TEST SUITE")
    print("=" * 60)

    # Clean up any leftover test variants first
    with database.SessionLocal() as db:
        db.query(models.SubscriptionPlan).delete()
        db.query(models.ProductVariant).delete()
        db.commit()

        # Confirm base product 1 exists
        prod1 = db.query(models.Product).filter(models.Product.id == 1).first()
        assert prod1 is not None, "Product 1 (Cotton Saree) must exist in DB"
        print(f"Base Product Verified: ID={prod1.id}, Name='{prod1.name}', Sales Price={prod1.sales_price}")

    client = TestClient(app)

    # -------------------------------------------------------------
    # Task 1 & 3: Test adding a product variant & verify final_price
    # -------------------------------------------------------------
    print("\n--- [TEST 1] Add Product Variant (Base: 1000, Add: 200, Expected: 1200) ---")
    payload1 = {"name": "Red Zari Border", "additional_price": 200.0}
    res1 = client.post("/api/products/1/variants", json=payload1)
    print(f"Response Status: {res1.status_code}")
    print(f"Response Body: {res1.json()}")
    assert res1.status_code == 201, f"Expected 201, got {res1.status_code}"
    data1 = res1.json()
    assert data1["name"] == "Red Zari Border"
    assert data1["additional_price"] == 200.0
    assert data1["final_price"] == 1200.0, f"Expected 1200.0, got {data1['final_price']}"
    variant1_id = data1["id"]
    print("[PASS] Test 1 passed: Variant created with correct final_price=1200.0")

    # Add a second variant
    print("\n--- [TEST 2] Add Second Variant (Base: 1000, Add: 350, Expected: 1350) ---")
    payload2 = {"name": "Green Zari Border", "additional_price": 350.0}
    res2 = client.post("/api/products/1/variants", json=payload2)
    print(f"Response Status: {res2.status_code}")
    print(f"Response Body: {res2.json()}")
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["final_price"] == 1350.0
    variant2_id = data2["id"]
    print("[PASS] Test 2 passed: Second variant created with final_price=1350.0")

    # -------------------------------------------------------------
    # Task 2 & 7: Test retrieving product and verifying variants appear
    # -------------------------------------------------------------
    print("\n--- [TEST 3] Retrieve Product by ID (GET /api/products/1) ---")
    res_get = client.get("/api/products/1")
    print(f"Response Status: {res_get.status_code}")
    print(f"Response Body: {res_get.json()}")
    assert res_get.status_code == 200
    prod_data = res_get.json()
    assert len(prod_data["variants"]) == 2, f"Expected 2 variants, got {len(prod_data['variants'])}"
    
    # Check variant 1 in product response
    v1 = next(v for v in prod_data["variants"] if v["id"] == variant1_id)
    assert v1["name"] == "Red Zari Border"
    assert v1["additional_price"] == 200.0
    assert v1["final_price"] == 1200.0, f"Expected final_price 1200.0, got {v1.get('final_price')}"

    # Check variant 2 in product response
    v2 = next(v for v in prod_data["variants"] if v["id"] == variant2_id)
    assert v2["name"] == "Green Zari Border"
    assert v2["additional_price"] == 350.0
    assert v2["final_price"] == 1350.0, f"Expected final_price 1350.0, got {v2.get('final_price')}"
    print("[PASS] Test 3 passed: Both variants appear in product response with correct final_price")

    print("\n--- [TEST 4] Retrieve All Products (GET /api/products) ---")
    res_list = client.get("/api/products")
    assert res_list.status_code == 200
    products_list = res_list.json()
    p1_in_list = next(p for p in products_list if p["id"] == 1)
    assert len(p1_in_list["variants"]) == 2
    assert p1_in_list["variants"][0]["final_price"] in (1200.0, 1350.0)
    print("[PASS] Test 4 passed: All products endpoint returns variants with final_price")

    # -------------------------------------------------------------
    # Task 4: Verify persistence in PostgreSQL
    # -------------------------------------------------------------
    print("\n--- [TEST 5] Verify PostgreSQL Database Persistence via Direct SQL Query ---")
    with database.engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name, additional_price, product_id FROM product_variants ORDER BY id")).fetchall()
        print("Raw database rows in product_variants table:")
        for r in rows:
            print(f"  Row: id={r[0]}, name='{r[1]}', additional_price={r[2]}, product_id={r[3]}")
        assert len(rows) == 2, f"Expected 2 rows in DB, got {len(rows)}"
        assert rows[0][1] == "Red Zari Border"
        assert rows[0][2] == 200.0
        assert rows[0][3] == 1
    print("[PASS] Test 5 passed: PostgreSQL directly confirmed to hold variant records")

    # Simulate server restart / fresh client & new database session
    print("\n--- [TEST 6] Simulate Server Restart / Fresh Application Instance ---")
    fresh_client = TestClient(app)
    res_restart = fresh_client.get("/api/products/1")
    assert res_restart.status_code == 200
    restart_data = res_restart.json()
    assert len(restart_data["variants"]) == 2
    assert restart_data["variants"][0]["final_price"] in (1200.0, 1350.0)
    print("[PASS] Test 6 passed: Data remains intact after fresh server instance initialization")

    # -------------------------------------------------------------
    # Task 5: Error responses for nonexistent product and invalid input
    # -------------------------------------------------------------
    print("\n--- [TEST 7] Error Handling: Nonexistent Product ---")
    res_404 = client.post("/api/products/9999/variants", json={"name": "Gold", "additional_price": 500.0})
    print(f"Nonexistent product response: {res_404.status_code} -> {res_404.json()}")
    assert res_404.status_code == 404
    assert res_404.json()["detail"] == "Product not found"
    print("[PASS] Test 7 passed: 404 returned for nonexistent product")

    print("\n--- [TEST 8] Error Handling: Invalid Inputs ---")
    
    # 8a: Empty name
    res_empty_name = client.post("/api/products/1/variants", json={"name": "", "additional_price": 100.0})
    print(f"Empty name response: {res_empty_name.status_code}")
    assert res_empty_name.status_code == 422
    print("[PASS] 8a: 422 for empty name")

    # 8b: Missing name
    res_missing_name = client.post("/api/products/1/variants", json={"additional_price": 100.0})
    print(f"Missing name response: {res_missing_name.status_code}")
    assert res_missing_name.status_code == 422
    print("[PASS] 8b: 422 for missing name")

    # 8c: Negative additional_price
    res_negative_price = client.post("/api/products/1/variants", json={"name": "Discount Border", "additional_price": -50.0})
    print(f"Negative price response: {res_negative_price.status_code}")
    assert res_negative_price.status_code == 422
    print("[PASS] 8c: 422 for negative additional_price")

    # 8d: Non-numeric additional_price
    res_non_num_price = client.post("/api/products/1/variants", json={"name": "Special", "additional_price": "five hundred"})
    print(f"Non-numeric price response: {res_non_num_price.status_code}")
    assert res_non_num_price.status_code == 422
    print("[PASS] 8d: 422 for non-numeric additional_price")

    # 8e: Non-integer product_id in URL
    res_invalid_id = client.post("/api/products/invalid_id/variants", json={"name": "Special", "additional_price": 100.0})
    print(f"Invalid URL product ID response: {res_invalid_id.status_code}")
    assert res_invalid_id.status_code == 422
    print("[PASS] 8e: 422 for non-integer product_id in URL")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
