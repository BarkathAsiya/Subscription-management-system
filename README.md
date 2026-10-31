# Subscription-management-system

Subscription management system for Brightloop Software: manage products, plans and subscriptions, auto-generate invoices, track payments, apply discounts and taxes, and view revenue reports, with role-based access for admin, staff and customers.

## SubSentry AI — Phase 1 (Brightloop Software)

Phase 1 implements the identity and access-control foundation required by the Brightloop Software Subscription Management System brief.

## Included
- Customer self-registration with unique email validation.
- Password policy: more than 8 characters, at least one uppercase, one lowercase, and one special character.
- Admin, Staff, and Customer roles.
- Only an Admin can create Staff accounts.
- JWT-based login and protected API routes.
- Argon2 password hashing.
- Forgot-password and reset-password flow using a one-time, expiring token.
- Customer profile endpoint scoped to the authenticated customer.
- Responsive dark React dashboard with login, registration, forgot/reset password, and role-aware landing pages.
- SQLite works out of the box; PostgreSQL can be enabled through `DATABASE_URL`.

## Project structure

```text
subsentry-ai-phase1/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   └── admin.py
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── deps.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   └── mailer.py
│   ├── scripts/
│   │   └── create_admin.py
│   ├── .env.example
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── ProtectedRoute.jsx
    │   ├── pages/
    │   │   ├── AuthPages.jsx
    │   │   └── Dashboard.jsx
    │   ├── api.js
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── styles.css
    ├── .env.example
    ├── index.html
    └── package.json
```

## 1. Requirements
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (optional for local demo; SQLite is the default)
- SMTP credentials for real password-reset email delivery (optional in local development)

## 2. Start the backend

Open a terminal in `backend/`.

### Windows PowerShell
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`. For a quick local run, leave `DATABASE_URL` as SQLite. Set a long random `SECRET_KEY`.

```powershell
uvicorn app.main:app --reload
```

Backend: http://127.0.0.1:8000  
API docs: http://127.0.0.1:8000/docs

### Create the first Admin
In a second terminal, still inside `backend/` and with the virtual environment active:

```powershell
python -m scripts.create_admin
```

Enter the admin email and a password that satisfies the password policy. Admin creation is a one-time bootstrap operation; public registration cannot create Admin or Staff users.

## 3. Start the frontend

Open another terminal in `frontend/`:

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Open the local URL printed by Vite (normally http://localhost:5173).

## 4. Configure PostgreSQL (optional)

Create a database, then set in `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/subsentry
```

Restart the backend. SQLAlchemy creates the Phase 1 tables automatically for this starter. For a production deployment, add Alembic migrations before changing schemas.

## 5. Configure password-reset email

Set these values in `backend/.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com
FRONTEND_URL=http://localhost:5173
```

Use an email provider's app password or SMTP credential, not your normal mailbox password.

If SMTP is not configured, the API still returns a generic success response for forgot-password requests, and the reset URL is printed to the backend console **only when `DEBUG_RESET_LINKS=true`**. This is for local testing only. Do not enable it in production.

## 6. Demo flow
1. Create the first Admin using the bootstrap command.
2. Log in as Admin.
3. Use **Create staff account** to create an internal Staff user.
4. Log out and register a Customer through the public registration page.
5. Log in as Staff and verify the Staff role is shown.
6. Log in as Customer and verify the customer portal only shows that customer's profile.
7. Test forgot-password. With SMTP configured, the user receives a reset email. Without SMTP, set `DEBUG_RESET_LINKS=true` locally and copy the printed link from the backend terminal.

## 7. API summary

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | Public | Register a Customer |
| POST | `/api/auth/login` | Public | Login |
| GET | `/api/auth/me` | Authenticated | Current account |
| POST | `/api/auth/forgot-password` | Public | Request reset email |
| POST | `/api/auth/reset-password` | Public | Set new password with token |
| GET | `/api/customer/me` | Customer | Own customer profile |
| POST | `/api/admin/staff` | Admin | Create Staff account |
| GET | `/api/admin/users` | Admin | List accounts |
| GET | `/health` | Public | Health check |

## Important security notes
- Public registration always creates the `customer` role; role values from the browser are ignored.
- Staff creation is protected by a server-side Admin role check.
- Password reset tokens are random, stored only as SHA-256 hashes, expire, and are single-use.
- Forgot-password responses do not reveal whether an email exists.
- Passwords are never returned by the API.
- This is a hackathon-ready Phase 1 foundation, not a complete production security review. Before production, add rate limiting, email verification, audit logs, CSRF strategy if using cookies, database migrations, HTTPS, monitoring, and a managed secrets store.

---

# Phase 3 — Subscriptions and Invoices (Person 3)

This phase extends the Phase 1 authentication foundation with quotation, subscription and invoice operations.

## What is included
- Quotation creation with customer, validity, product lines, quantity, unit price, tax and line discount snapshots.
- Quotation conversion into a draft subscription.
- Subscription records with unique subscription numbers, plan/billing period, start/expiry dates, payment terms and line items.
- Server-enforced lifecycle: `draft → quotation → confirmed → active → closed` (quotation can return to draft; confirmed/active can close).
- Automatic invoice generation for active subscriptions whose `next_billing_date` is due.
- Idempotency: each subscription billing cycle has a unique `cycle_key`, protected by a database unique constraint. Re-running the billing endpoint will not create a second invoice for the same cycle.
- Invoice snapshots with calculated subtotal, discounts, taxes and total.
- Invoice lifecycle: `draft → confirmed → paid`, or cancel before paid.
- Invoice email delivery using the existing SMTP configuration, and a browser print layout in the frontend.
- Customer reads are scoped to the authenticated customer; Admin/Staff can manage records.
- Pagination parameters and indexes on frequently queried customer/status/date columns.
- Frontend route: `/subscriptions`.

## Run the updated project
Use the same Phase 1 steps above. Stop and restart the backend after adding these files so SQLAlchemy creates the new tables. Start the frontend again and open **Open subscriptions & invoices** from the dashboard.

## Person 3 API endpoints
All paths are under the backend base URL `http://127.0.0.1:8000`.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/billing/customers` | Admin/Staff | Customer choices for subscription creation |
| POST | `/api/quotations` | Admin/Staff | Create a quotation |
| GET | `/api/quotations?page=1&page_size=20` | Authenticated | List quotations (customers see only theirs) |
| POST | `/api/quotations/{id}/convert` | Admin/Staff | Convert a valid quotation to a draft subscription |
| POST | `/api/subscriptions` | Admin/Staff | Create a draft subscription directly |
| GET | `/api/subscriptions?page=1&page_size=20` | Authenticated | List subscriptions (customers see only theirs) |
| PATCH | `/api/subscriptions/{id}/status` | Admin/Staff | Move through the allowed subscription lifecycle |
| POST | `/api/billing/run` | Admin/Staff | Process all due active subscriptions and create invoices |
| GET | `/api/invoices?page=1&page_size=20` | Authenticated | List invoices (customers see only theirs) |
| GET | `/api/invoices/{id}` | Authenticated | Get one invoice with ownership check |
| PATCH | `/api/invoices/{id}/status` | Admin/Staff | Confirm, mark paid, or cancel an invoice |
| POST | `/api/invoices/{id}/send` | Admin/Staff | Email invoice using SMTP |

Interactive API documentation: `http://127.0.0.1:8000/docs`.

## Suggested hackathon demo
1. Register a customer using the Phase 1 signup page.
2. Log in as Admin or Staff and open **Subscriptions & invoices**.
3. Create a draft subscription for that customer. Choose a start date in the past for a quick demo.
4. Move it through `quotation`, `confirmed`, and `active` using the status dropdown.
5. Click **Run billing now**. An invoice should appear in the Invoices tab.
6. Click **Run billing now** again. It should not create a duplicate invoice for that billing cycle.
7. Confirm the invoice, print it, and mark it paid (or cancel it while unpaid).
8. Log in as the customer to verify only that customer's subscriptions and invoices are visible.

## Important integration contract for the team
- Person 1 owns `users`. This module references `users.id` for `customer_id`; it does not create a second customer table.
- Person 2 owns product, plan, tax-rule and discount master data. This phase stores `product_id` and `plan_id` as optional references and stores product/price/tax/discount snapshots on each quotation/subscription/invoice line. That preserves historical invoice amounts if catalog prices later change. When Person 2's models and API are ready, connect their IDs and validate that each selected product/plan exists and is available. Do not create duplicate product/plan master tables in Person 3's module.
- Person 4 owns payments and finance reporting. The `invoices.id`, `invoice_number`, `customer_id`, `total`, `due_date` and `status` fields are the integration points. In production, marking an invoice Paid should be driven by a confirmed payment record from Person 4, not by a manual status button. The manual action is present only to make the isolated demo testable.
- Current tax and discount values are passed as line-level snapshots by the caller. Person 2 should supply the validated tax and discount values/rules when integrated.

## Billing behavior and production notes
- The billing endpoint is intentionally callable by Admin/Staff for a hackathon demonstration. In production, call the same billing service from a scheduled background worker (e.g. daily scheduler), not from a public browser button.
- The invoice cycle key is the due date on the subscription. The unique database constraint is the final duplicate-prevention guard.
- This implementation creates the invoice in Draft state. An authorized staff member confirms it after review.
- SMTP must be configured in `backend/.env` for the Send Invoice action. Without SMTP, the API returns a clear configuration error.
- SQLAlchemy `create_all` is retained from Phase 1 for this prototype. Before production, use Alembic migrations and test the unique-constraint behavior against the chosen PostgreSQL deployment.
- The current frontend subscription form is a lightweight demo form. Quotation creation/conversion APIs are available in Swagger and can be added to the UI in the next UI pass.
