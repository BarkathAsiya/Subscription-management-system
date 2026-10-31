import sys
from datetime import date, timedelta
from pathlib import Path

# Configure utf-8 encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from sqlalchemy import text
import database
import models
from main import app

def run_all_tests():
    print("=" * 70)
    print("RUNNING FULL TEST SUITE FOR ASSIGNED MODULES (PERSON 2)")
    print("=" * 70)

    client = TestClient(app)

    # ------------------------------------------------------------------------
    # MODULE A: PRODUCTS & VARIANTS
    # ------------------------------------------------------------------------
    print("\n>>> [MODULE A] Testing Products & Variants...")

    # Verify existing Cotton Saree (id: 1)
    res = client.get("/api/products/1")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    p1 = res.json()
    assert p1["name"] == "Cotton Saree"
    print(f"  [OK] Product 1 exists: '{p1['name']}', Price: ₹{p1['sales_price']}")

    # Clean existing variants for product 1 for fresh testing
    with database.SessionLocal() as db:
        db.query(models.SubscriptionPlan).delete()
        db.query(models.ProductVariant).filter(models.ProductVariant.product_id == 1).delete()
        db.commit()

    # Add variant: Additional ₹200 -> Final ₹1,200
    res_var1 = client.post("/api/products/1/variants", json={"name": "Red Zari Border", "additional_price": 200.0})
    assert res_var1.status_code == 201
    v1_data = res_var1.json()
    assert v1_data["additional_price"] == 200.0
    assert v1_data["final_price"] == 1200.0
    var1_id = v1_data["id"]
    print(f"  [OK] Added variant {var1_id}: '{v1_data['name']}' (+₹200) -> Final: ₹{v1_data['final_price']}")

    # Add second variant: Additional ₹350 -> Final ₹1,350
    res_var2 = client.post("/api/products/1/variants", json={"name": "Gold Silk Border", "additional_price": 350.0})
    assert res_var2.status_code == 201
    v2_data = res_var2.json()
    assert v2_data["final_price"] == 1350.0
    var2_id = v2_data["id"]
    print(f"  [OK] Added second variant {var2_id}: '{v2_data['name']}' (+₹350) -> Final: ₹{v2_data['final_price']}")

    # Get product 1 and confirm both variants appear
    res_p1_vars = client.get("/api/products/1")
    assert res_p1_vars.status_code == 200
    assert len(res_p1_vars.json()["variants"]) == 2
    print(f"  [OK] Product 1 retrieval includes {len(res_p1_vars.json()['variants'])} variants with correct final prices")

    # Update variant
    res_up_var = client.put(f"/api/variants/{var2_id}", json={"additional_price": 400.0})
    assert res_up_var.status_code == 200
    assert res_up_var.json()["additional_price"] == 400.0
    assert res_up_var.json()["final_price"] == 1400.0
    print(f"  [OK] Updated variant {var2_id} price to ₹400 -> Final: ₹1400.0")

    # Create new product (e.g. Service product)
    new_prod_payload = {
        "name": "Saree Styling Consultation",
        "product_type": "Service",
        "sales_price": 500.0,
        "cost_price": 100.0,
        "notes": "1-on-1 virtual consultation session",
    }
    res_np = client.post("/api/products", json=new_prod_payload)
    assert res_np.status_code == 201
    service_prod_id = res_np.json()["id"]
    print(f"  [OK] Created new service product {service_prod_id}: '{res_np.json()['name']}'")

    # ------------------------------------------------------------------------
    # MODULE B: SUBSCRIPTION PLAN CONFIGURATION
    # ------------------------------------------------------------------------
    print("\n>>> [MODULE B] Testing Subscription Plan Configuration...")

    # Clean previous test plans
    with database.SessionLocal() as db:
        db.query(models.SubscriptionPlan).delete()
        db.commit()

    today_str = date.today().isoformat()
    future_str = (date.today() + timedelta(days=365)).isoformat()

    # Plan 1: Monthly Saree Box (Associated with Cotton Saree product 1 and variant 1)
    plan1_payload = {
        "name": "Monthly Saree Box",
        "description": "Receive curated handloom cotton sarees every month",
        "billing_period": "monthly",
        "price": 1150.0,
        "product_id": 1,
        "variant_id": var1_id,
        "min_quantity": 1,
        "start_date": today_str,
        "end_date": future_str,
        "allow_pause": True,
        "allow_renewal": True,
        "allow_early_close": True,
        "auto_close_on_condition": False,
        "is_active": True,
    }
    res_plan1 = client.post("/api/plans", json=plan1_payload)
    assert res_plan1.status_code == 201, f"Plan creation failed: {res_plan1.status_code} {res_plan1.text}"
    p1_resp = res_plan1.json()
    plan1_id = p1_resp["id"]
    assert p1_resp["product_name"] == "Cotton Saree"
    assert p1_resp["variant_name"] == "Red Zari Border"
    print(f"  [OK] Created Plan {plan1_id}: '{p1_resp['name']}' ({p1_resp['billing_period']}) - ₹{p1_resp['price']}")

    # Plan 2: Yearly VIP Saree Pass
    plan2_payload = {
        "name": "Yearly Styling & Handloom Pass",
        "description": "Full year styling support and seasonal sarees",
        "billing_period": "yearly",
        "price": 10000.0,
        "product_id": service_prod_id,
        "min_quantity": 1,
        "allow_pause": False,
        "allow_renewal": True,
        "allow_early_close": False,
        "auto_close_on_condition": True,
        "is_active": True,
    }
    res_plan2 = client.post("/api/plans", json=plan2_payload)
    assert res_plan2.status_code == 201
    plan2_id = res_plan2.json()["id"]
    print(f"  [OK] Created Plan {plan2_id}: '{res_plan2.json()['name']}' ({res_plan2.json()['billing_period']}) - ₹{res_plan2.json()['price']}")

    # List plans with filtering
    res_plans_all = client.get("/api/plans")
    assert res_plans_all.status_code == 200
    assert len(res_plans_all.json()) >= 2

    res_plans_monthly = client.get("/api/plans?billing_period=monthly")
    assert res_plans_monthly.status_code == 200
    assert any(p["id"] == plan1_id for p in res_plans_monthly.json())

    # Update plan
    res_up_plan = client.put(f"/api/plans/{plan1_id}", json={"price": 1199.0, "description": "Updated description"})
    assert res_up_plan.status_code == 200
    assert res_up_plan.json()["price"] == 1199.0
    print(f"  [OK] Updated Plan {plan1_id} price to ₹1,199.00")

    # Toggle plan status
    res_toggle_plan = client.patch(f"/api/plans/{plan1_id}/status?is_active=false")
    assert res_toggle_plan.status_code == 200
    assert res_toggle_plan.json()["is_active"] is False
    # Re-enable
    client.patch(f"/api/plans/{plan1_id}/status?is_active=true")
    print(f"  [OK] Plan status toggle verified (active/inactive)")

    # Validation: invalid billing period (e.g. "decade")
    bad_plan = {**plan1_payload, "billing_period": "decade"}
    res_bad_period = client.post("/api/plans", json=bad_plan)
    assert res_bad_period.status_code == 422
    print("  [OK] Rejected invalid billing period 'decade' (422)")

    # Validation: start_date > end_date
    bad_dates_plan = {**plan1_payload, "start_date": "2026-12-31", "end_date": "2026-01-01"}
    res_bad_dates = client.post("/api/plans", json=bad_dates_plan)
    assert res_bad_dates.status_code == 422
    print("  [OK] Rejected inverted dates start > end (422)")

    # ------------------------------------------------------------------------
    # MODULE C: DISCOUNTS & DISCOUNT RULES
    # ------------------------------------------------------------------------
    print("\n>>> [MODULE C] Testing Discount Management & Eligibility Rules...")

    with database.SessionLocal() as db:
        db.query(models.DiscountRule).delete()
        db.commit()

    # Discount 1: Percentage (20% off, min ₹500 purchase)
    d1_payload = {
        "code": "FESTIVE20",
        "description": "20% festive discount on orders above ₹500",
        "discount_type": "percentage",
        "discount_value": 20.0,
        "min_purchase_amount": 500.0,
        "min_quantity": 1,
        "start_date": today_str,
        "end_date": future_str,
        "usage_limit": 50,
        "applicable_to": "all",
        "is_active": True,
    }
    res_d1 = client.post("/api/discounts", json=d1_payload)
    assert res_d1.status_code == 201
    d1_id = res_d1.json()["id"]
    print(f"  [OK] Created percentage discount '{res_d1.json()['code']}' (20%)")

    # Discount 2: Fixed amount (₹150 off, min quantity 2)
    d2_payload = {
        "code": "SAVE150",
        "description": "₹150 flat discount on buying 2 or more items",
        "discount_type": "fixed",
        "discount_value": 150.0,
        "min_purchase_amount": 0.0,
        "min_quantity": 2,
        "start_date": today_str,
        "end_date": future_str,
        "applicable_to": "product",
        "product_id": 1,
        "is_active": True,
    }
    res_d2 = client.post("/api/discounts", json=d2_payload)
    assert res_d2.status_code == 201
    print(f"  [OK] Created fixed discount '{res_d2.json()['code']}' (₹150)")

    # Duplicate code rejection
    res_dup = client.post("/api/discounts", json=d1_payload)
    assert res_dup.status_code == 400
    print("  [OK] Prevented duplicate discount code creation (400)")

    # Validate percentage > 100% rejection
    res_invalid_pct = client.post("/api/discounts", json={**d1_payload, "code": "SUPER150", "discount_value": 150.0})
    assert res_invalid_pct.status_code == 422
    print("  [OK] Prevented percentage discount > 100% (422)")

    # Discount Calculation Endpoint (/api/discounts/validate)
    # Test valid 20% discount on ₹1,000 subtotal -> Discount ₹200, Final ₹800
    val_res1 = client.post("/api/discounts/validate", json={"code": "FESTIVE20", "subtotal": 1000.0, "quantity": 1})
    assert val_res1.status_code == 200
    r1 = val_res1.json()
    assert r1["is_valid"] is True
    assert r1["discount_amount"] == 200.0
    assert r1["final_amount"] == 800.0
    print(f"  [OK] Validated FESTIVE20 on ₹1,000: -₹{r1['discount_amount']} -> Final: ₹{r1['final_amount']}")

    # Test minimum purchase amount failure (₹400 < ₹500 min)
    val_res2 = client.post("/api/discounts/validate", json={"code": "FESTIVE20", "subtotal": 400.0, "quantity": 1})
    assert val_res2.status_code == 200
    r2 = val_res2.json()
    assert r2["is_valid"] is False
    assert "Minimum purchase amount" in r2["reason"]
    print(f"  [OK] Correctly blocked under-minimum purchase: reason='{r2['reason']}'")

    # Test minimum quantity failure on SAVE150 (qty: 1 < 2)
    val_res3 = client.post("/api/discounts/validate", json={"code": "SAVE150", "product_id": 1, "subtotal": 1000.0, "quantity": 1})
    assert val_res3.status_code == 200
    assert val_res3.json()["is_valid"] is False
    assert "Minimum quantity" in val_res3.json()["reason"]
    print(f"  [OK] Correctly blocked under-minimum quantity for SAVE150")

    # Test product applicability mismatch
    val_res4 = client.post("/api/discounts/validate", json={"code": "SAVE150", "product_id": 999, "subtotal": 2000.0, "quantity": 2})
    assert val_res4.status_code == 200
    assert val_res4.json()["is_valid"] is False
    assert "does not apply" in val_res4.json()["reason"]
    print(f"  [OK] Correctly blocked inapplicable product for SAVE150")

    # ------------------------------------------------------------------------
    # MODULE D: TAX RULES & CALCULATION
    # ------------------------------------------------------------------------
    print("\n>>> [MODULE D] Testing Tax Rules & Calculation...")

    with database.SessionLocal() as db:
        db.query(models.TaxRule).delete()
        db.commit()

    # Tax 1: GST Standard (18% for Services)
    tax1_payload = {
        "name": "GST Services (18%)",
        "description": "Standard 18% GST applicable to all service products",
        "rate": 18.0,
        "applicable_scope": "product_type",
        "product_type": "Service",
        "is_active": True,
    }
    res_t1 = client.post("/api/taxes", json=tax1_payload)
    assert res_t1.status_code == 201
    tax1_id = res_t1.json()["id"]
    print(f"  [OK] Created tax rule {tax1_id}: '{res_t1.json()['name']}' ({res_t1.json()['rate']}%)")

    # Tax 2: Textile GST (5% for Physical Handloom Products)
    tax2_payload = {
        "name": "Handloom Textile GST (5%)",
        "description": "Concessional 5% GST for physical handloom items",
        "rate": 5.0,
        "applicable_scope": "product_type",
        "product_type": "Physical",
        "is_active": True,
    }
    res_t2 = client.post("/api/taxes", json=tax2_payload)
    assert res_t2.status_code == 201
    print(f"  [OK] Created tax rule: '{res_t2.json()['name']}' ({res_t2.json()['rate']}%)")

    # Validation: Rate > 100% rejection
    res_bad_tax = client.post("/api/taxes", json={**tax1_payload, "name": "Super Tax", "rate": 105.0})
    assert res_bad_tax.status_code == 422
    print("  [OK] Prevented tax rate > 100% (422)")

    # Tax calculation for Service (18% on ₹1,000 -> ₹180 tax, total ₹1,180)
    calc1 = client.post("/api/taxes/calculate", json={"amount": 1000.0, "product_type": "Service"})
    assert calc1.status_code == 200
    c1 = calc1.json()
    assert c1["combined_rate"] == 18.0
    assert c1["tax_amount"] == 180.0
    assert c1["total_with_tax"] == 1180.0
    print(f"  [OK] Calculated tax for Service ₹1,000 at 18%: Tax=₹{c1['tax_amount']} -> Total: ₹{c1['total_with_tax']}")

    # Tax calculation for Physical Product (5% on ₹1,000 -> ₹50 tax, total ₹1,050)
    calc2 = client.post("/api/taxes/calculate", json={"amount": 1000.0, "product_type": "Physical", "product_id": 1})
    assert calc2.status_code == 200
    c2 = calc2.json()
    assert c2["combined_rate"] == 5.0
    assert c2["tax_amount"] == 50.0
    assert c2["total_with_tax"] == 1050.0
    print(f"  [OK] Calculated tax for Physical Handloom ₹1,000 at 5%: Tax=₹{c2['tax_amount']} -> Total: ₹{c2['total_with_tax']}")

    # ------------------------------------------------------------------------
    # DATABASE PERSISTENCE VERIFICATION
    # ------------------------------------------------------------------------
    print("\n>>> [DATABASE] Verifying PostgreSQL Direct Storage...")
    with database.engine.connect() as conn:
        p_count = conn.execute(text("SELECT count(*) FROM products")).scalar()
        v_count = conn.execute(text("SELECT count(*) FROM product_variants")).scalar()
        plan_count = conn.execute(text("SELECT count(*) FROM subscription_plans")).scalar()
        d_count = conn.execute(text("SELECT count(*) FROM discount_rules")).scalar()
        t_count = conn.execute(text("SELECT count(*) FROM tax_rules")).scalar()

        print(f"  PostgreSQL row counts:")
        print(f"    - products: {p_count}")
        print(f"    - product_variants: {v_count}")
        print(f"    - subscription_plans: {plan_count}")
        print(f"    - discount_rules: {d_count}")
        print(f"    - tax_rules: {t_count}")

        assert p_count >= 2
        assert v_count >= 2
        assert plan_count >= 2
        assert d_count >= 2
        assert t_count >= 2
    print("  [OK] All tables successfully populated and verified in PostgreSQL!")

    print("\n" + "=" * 70)
    print("ALL MODULE BACKEND TESTS PASSED (100% SUCCESSFUL)!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
