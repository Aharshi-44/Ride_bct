<div align="Left">

<div style="display:flex;align-items:center;justify-content:center;gap:14px;">
  <img src="static/img/Final_logo.png" alt="Project logo" width="56" height="56" />
  <h1 style="margin:0;font-size:2rem;">Quick-Go</h1>
</div>

### Smart ride booking for demos & coursework

**Riders** book with live fares and a wait-for-driver modal. **Drivers** go online, accept or reject requests, and manage trips — server-rendered Django, custom CSS, and JSON APIs where it matters.

<br>

[![Django](https://img.shields.io/badge/Django-4.2%2B-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MariaDB](https://img.shields.io/badge/Database-MySQL%20%2F%20MariaDB-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mariadb.org/)

<br>

[Why Quick-Go](#why-Quick-Go) · [Features](#features) · [Quick start](#quick-start) · [Tech stack](#tech-stack) · [Architecture](#architecture) · [Configuration](#configuration) · [Fare](#fare-calculation) · [URLs](#http-routes) · [Layout](#project-layout) · [License](#license)

<br>

---

<br>

</div>

> **Demo scope** — Payments are **simulated** (`templates/rides/payment.html`). There is no real payment gateway. Intended for learning, portfolios, and prototypes.

<br>

## Why Quick-Go?

| | |
|:---|:---|
| **Transparent pricing** | `fare = base + (km × rate) + (minutes × rate)` — constants in `rides/services.py`. |
| **India search** | `locations` app calls public Nominatim (`countrycodes=in`, `format=json`) with `requests`. |
| **Routing** | OSRM for distance/ETA when reachable; public Project OSRM fallback; haversine-style estimate if all fail (unless disabled). |
| **Driver pool** | Pending rides are shared; **accept** uses `select_for_update` + conditional `update`; **reject** uses `RideRejection` per driver. |
| **Cancellations** | `Ride.Status.CANCELLED`; rider can cancel **pending** (`rider_cancel`); driver can cancel **accepted/ongoing** (`cancel`). |

<br>

## Features

<details>
<summary><strong>Riders</strong> (<code>accounts</code> + <code>rides</code>)</summary>

- Register / login — `User` with `is_driver`; `LOGIN_REDIRECT_URL` → dashboard (`config/settings.py`).
- **Book** (`/rides/book/`) — pickup/drop from `/api/location/search/?q=`; hidden lat/lng fields; `book_action`: `preview` vs `confirm`.
- **Confirm** via `fetch` + `X-Requested-With: XMLHttpRequest` → JSON `{ ok, ride_id }`; otherwise redirect `?wait=<id>` for no-JS.
- **Wait modal** (`static/js/book_wait_modal.js`) — polls `GET /rides/<id>/status/api/`; **Cancel request** → `POST /rides/<id>/rider-cancel/` while pending.
- After **accepted** — green **Continue to payment** → `/rides/<id>/payment/` only if status is **`accepted`** (`rides/views.payment_placeholder`).
- **Status** (`/rides/<id>/status/`) — `static/js/ride_status.js` polls every 3s; cancelled state + messaging.

</details>

<details>
<summary><strong>Drivers</strong></summary>

- `DriverProfile`: vehicle, `is_available`, optional `current_area`.
- **Toggle availability** — `POST /rides/driver/toggle-availability/`.
- **Incoming** — pending rides without driver, excluding this driver’s rejections (`accounts/views.dashboard` + `rides.services.simulated_pickup_distance_km` for display).
- **Accept / Reject** — `POST /rides/<id>/accept/`, `.../reject/`.
- **Cancel trip** — `POST /rides/<id>/cancel/` when assigned and accepted or ongoing.

</details>

<details>
<summary><strong>System &amp; data</strong></summary>

- **DB:** MySQL/MariaDB via `ENGINE = config.db_backends.mysql` — custom `DatabaseFeatures` for **MariaDB 10.4** under Django 6+ (relaxes version check + `INSERT … RETURNING` behavior). Default DB name `ride_booking_db` (`config/settings.py`).
- **Auth model:** `AUTH_USER_MODEL = accounts.User`.
- **Time zone:** `Asia/Kolkata`.
- **Lifecycle simulation:** `maybe_advance_ride_status` in `rides/services.py` advances accepted → ongoing → completed from elapsed time (not applied to `pending` or `cancelled`).

</details>

<br>

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate         # macOS / Linux

pip install -r requirements.txt

# Create DB (match NAME/USER/PASSWORD in config/settings.py if needed):
# CREATE DATABASE ride_booking_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

copy .env.example .env             # Windows — see Configuration
# cp .env.example .env

python manage.py migrate
python manage.py runserver
```

Open **http://127.0.0.1:8000/** — register a **passenger** and a **driver** to exercise both sides.

<br>

## Tech stack

| Layer | Details |
|--------|---------|
| Framework | **Django** ≥ 4.2 (`requirements.txt`); project uses **Django 6**-compatible DB backend notes in `config/db_backends/mysql/`. |
| Database | **MySQL / MariaDB** — default `ride_booking_db`, user `root`, empty password in settings (change for your machine). |
| HTTP | **`requests`** — Nominatim in `locations/services.py`; **`urllib`** — OSRM in `rides/services.py`. |
| Frontend | Templates + **`static/css/app.css`**, **`static/js/app.js`** (theme, toasts), **`ride_status.js`**, **`book_wait_modal.js`**. Fonts: Inter (see `templates/base.html`). |
| Admin | `/admin/` — `accounts/admin.py`, `rides/admin.py`. |

<br>

## Architecture

```text
┌─────────────┐     SSR + forms      ┌──────────────┐
│   Browser   │ ◄──────────────────► │ Django apps  │
└──────┬──────┘                      │ accounts     │
       │                             │ rides        │
       │  GET/POST JSON              │ locations    │
       └─────────────────────────────►└──────┬───────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
              MySQL/MariaDB          Nominatim (search)      OSRM (route)
              (ride, user,           via requests             via urllib
               rejection…)           India-scoped             + fallbacks
```

**Ride statuses:** `pending` → `accepted` → `ongoing` → `completed`, or **`cancelled`**.

<br>

## Configuration

`.env` is loaded manually in `config/settings.py` (no `django-environ` dependency). Copy **`.env.example`**.

**Currently in `.env.example` (used):**

| Variable | Purpose |
|----------|---------|
| `DJANGO_DEBUG` | `"1"` → `DEBUG=True` (default in code if unset). |
| `OSM_HTTP_USER_AGENT` | Passed into `settings.OSM_HTTP_USER_AGENT` — used by **`rides/services.py`** for OSRM HTTP calls. |
| `OSM_OSRM_BASE_URL` | Primary OSRM base URL for fare / route metrics. |

**Also defined in `settings.py` but not in slim `.env.example`:**

| Variable | Default (if unset) |
|----------|-------------------|
| `OSM_NOMINATIM_BASE_URL` | `http://localhost:8080` — stored on `settings`; **not** used by `locations` search (that module uses a **fixed** public Nominatim URL in `locations/services.py`). |

**Read directly in `rides/services.py` from `os.environ` (optional):**

| Variable | Effect |
|----------|--------|
| `OSM_DISABLE_PUBLIC_OSRM_FALLBACK` | `1` → do not try public Project OSRM after primary OSRM fails. |
| `OSM_PUBLIC_OSRM_BASE_URL` | Override default `https://router.project-osrm.org`. |
| `OSM_DISABLE_ROUTE_FALLBACK` | `1` → no haversine-style estimate when OSRM fails (stricter). |

**`locations` User-Agent:** `getattr(settings, "LOCATIONS_NOMINATIM_USER_AGENT", "rideshare-app")` — add this name in `settings.py` if you want it configurable; otherwise default **`rideshare-app`**.

Self-hosted OSRM/Nominatim: **[API.md](API.md)**. Production: respect [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/).

<br>

## Fare calculation

Implemented in **`rides/services.py`** (`BASE_FARE`, `PER_KM_RATE`, `PER_MIN_RATE`):

```text
fare = base_fare + (distance_km × per_km_rate) + (billable_minutes × per_min_rate)
```

Billable minutes = whole minutes, **rounded up** from route `duration_seconds`. Defaults: **₹50** base, **₹10**/km, **₹2**/min.

<br>

## HTTP routes

| Path | Description |
|------|-------------|
| `/` | Home (`accounts.views.home`). |
| `/admin/` | Django admin. |
| `/accounts/login/`, `/logout/`, `/register/`, `/register/driver/`, `/dashboard/` | Auth & dashboards. |
| `/rides/book/` | Booking form + wait modal. |
| `/rides/<id>/payment/` | Demo payment (**rider**, ride must be **`accepted`**). |
| `/rides/<id>/status/`, `/rides/<id>/status/api/` | Status page + JSON poll. |
| `/rides/<id>/accept/`, `/reject/`, `/cancel/`, `/rider-cancel/` | Driver/rider actions (POST). |
| `/rides/driver/toggle-availability/` | Driver online toggle (POST). |
| `/api/location/search/?q=` | Nominatim-backed search (login required). |

<br>

## Project layout

```text
├── accounts/                 # Custom User, DriverProfile, auth, dashboards
├── config/
│   ├── settings.py           # .env loader, DB, OSM settings, AUTH_USER_MODEL
│   ├── urls.py
│   └── db_backends/mysql/    # MariaDB 10.4 compatibility
├── locations/
│   ├── services.py           # get_location_from_nominatim, caching
│   └── views.py              # GET .../search/ → JSON
├── rides/                    # Ride, RideRejection, booking, status, fare, routing
├── templates/                # base.html, home, dashboards, accounts/*, rides/*
├── static/
│   ├── css/app.css
│   └── js/                   # app.js, ride_status.js, book_wait_modal.js
├── manage.py
├── requirements.txt
├── .env.example
├── API.md
├── LICENSE
└── README.md
```

**Optional asset:** `templates/home.html` references `{% static 'img/route-preview.png' %}`. Add `static/img/route-preview.png` or remove the `<img>` to avoid a broken image in the hero.

<br>

## Security & production

- **Do not commit** `.env`. Replace the hardcoded **`SECRET_KEY`** in `settings.py` for any public deployment (use environment variable).
- Set **`DJANGO_DEBUG=0`**, expand **`ALLOWED_HOSTS`**, enable HTTPS and secure cookie settings.
- Rate-limit external geocoding/routing in production.

<br>

## Troubleshooting

| Issue | What to check |
|-------|-----------------|
| DB errors | MySQL/MariaDB running; database exists; `NAME` / `USER` / `PASSWORD` / `HOST` in `settings.py`. |
| MariaDB 10.4 + Django 6 | Keep `ENGINE = "config.db_backends.mysql"` as configured. |
| No search results | Network; Nominatim reachable; `requests` installed; query length ≥ 3. |
| Fare / routing failures | `OSM_OSRM_BASE_URL` reachable; or allow public OSRM + coordinate fallback (see env vars above). |
| `mysqlclient` on Windows | Use a wheel or build tools; switching drivers needs code changes. |

<br>

## License

This project is licensed under the **MIT License** — see **[LICENSE](LICENSE)** for the full text.

<br>

## Acknowledgements

**[Django](https://www.djangoproject.com/)** · **[OpenStreetMap](https://www.openstreetmap.org/)** · **Nominatim** · **OSRM** · © OpenStreetMap contributors.

---

<div align="center">

**Quick-Go** — *Ride booking, demo-ready.*

</div>
