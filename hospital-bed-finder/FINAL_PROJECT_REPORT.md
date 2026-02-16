# Final Project Report: Hospital Bed Finder

---

## 1. Introduction

### 1.1 Overview

**Hospital Bed Finder** is a web application that allows users to find hospitals near their current location and view the availability of general and ICU beds. It is designed to support quick decision-making during emergencies by combining geolocation, real-world hospital data from OpenStreetMap, and an admin-maintained bed inventory.

### 1.2 Objectives

- Enable users to discover hospitals within a chosen radius (10, 25, or 50 km) based on their current location.
- Display general and ICU bed availability for each hospital.
- Show hospital locations on an interactive map and sort results by distance.
- Provide an admin interface to update bed counts and search hospitals.
- Use free, open data (OSM) and a simple, maintainable tech stack.

### 1.3 Scope

The project covers:

- User-facing: location-based hospital search, map view, and bed/card display.
- Admin-facing: login, hospital list, bed updates, and search.
- Backend: Flask API, SQLite database, OSM/Overpass integration, and distance calculation.

The project is explicitly a **demo** and is not intended for production or real emergency use without additional security, data validation, and integration with official health systems.

---

## 2. System Analysis & Design

### 2.1 Problem Statement

In emergencies, patients and responders need to quickly identify nearby hospitals and know whether beds (especially ICU beds) are available. Manually searching and calling hospitals is slow and error-prone. A centralized, location-aware view of hospitals and bed counts can reduce delay and improve allocation of patients to facilities.

### 2.2 Proposed Solution

A lightweight web app that:

1. Asks the user for location permission and captures coordinates.
2. Fetches hospital nodes/ways/relations from OpenStreetMap within a given radius.
3. Stores and enriches hospital data (including admin-updated bed counts) in SQLite.
4. Presents hospitals sorted by distance with general/ICU beds and contact info.
5. Renders an interactive map with markers for each hospital.
6. Allows admins to log in and update bed counts and search hospitals.

### 2.3 Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| FR1 | User can allow location and trigger “Find Nearby Hospitals” | ✅ |
| FR2 | User can select search radius (10 / 25 / 50 km) | ✅ |
| FR3 | System fetches hospitals from OSM within radius and stores in DB | ✅ |
| FR4 | System calculates distance (Haversine) and filters by radius | ✅ |
| FR5 | User sees hospital cards with name, general beds, ICU beds, distance, contact | ✅ |
| FR6 | User sees map with markers when location is available | ✅ |
| FR7 | Admin can log in with username/password | ✅ |
| FR8 | Admin can view all hospitals and update general/ICU beds | ✅ |
| FR9 | Admin can search hospitals by name | ✅ |

### 2.4 Non-Functional Requirements

- **Usability:** Simple UI with clear controls and feedback (e.g. loader, “Allow location” message).
- **Performance:** Minimal dependencies; OSM fetch and distance calculation are fast for typical radii.
- **Maintainability:** Single Flask app, SQLite file, and standard front-end assets.
- **Security:** Admin area protected by session-based login (demo credentials: admin / admin123).

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | Python 3, Flask | Web server, routing, session, business logic |
| Database | SQLite | Persistent storage for hospitals and bed data |
| External API | Overpass API (OSM) | Fetch hospital nodes/ways/relations by area |
| Frontend | HTML5, CSS3, JavaScript | Structure, styling, geolocation, map |
| Map | Leaflet 1.9.4, OSM tiles | Interactive map and markers |
| Styling | Custom CSS (variables, grid, cards) | Responsive layout and UI |

---

## 4. System Design

### 4.1 Architecture

- **Client:** Browser requests `/`, gets HTML with hospital list and optional map; JavaScript calls `navigator.geolocation.getCurrentPosition`, then GET `/location?lat=&lon=&radius=` to set session and trigger OSM fetch; page reloads to show filtered, sorted results and map.
- **Server:** Flask serves templates, manages session (user coordinates, radius, admin flag), connects to SQLite, calls Overpass API, computes Haversine distance, and returns rendered pages or "OK" for `/location`.
- **Data flow:** OSM → Overpass API → Flask → SQLite (insert new hospitals only); on home load, Flask reads DB, filters by distance if session has lat/lon, sorts by distance, passes list to template.

### 4.2 Database Schema

**Table: `hospitals`**

| Column        | Type    | Description                    |
|---------------|---------|--------------------------------|
| id            | INTEGER | Primary key, auto-increment    |
| name          | TEXT    | Hospital name (from OSM or set)|
| general_beds  | INTEGER | General bed count (default 0)  |
| icu_beds      | INTEGER | ICU bed count (default 0)      |
| contact       | TEXT    | Contact info (default placeholder) |
| latitude      | REAL    | Latitude                       |
| longitude     | REAL    | Longitude                      |

### 4.3 Module Overview

- **DB:** `get_db_connection()`, `init_db()` — connection and table creation.
- **Distance:** `calculate_distance(lat1, lon1, lat2, lon2)` — Haversine formula (radius 6371 km).
- **OSM:** `fetch_real_hospitals_osm(lat, lon, radius_km)` — Overpass query for `amenity=hospital`, insert new hospitals by name.
- **Routes:** `/` (home), `/location` (set session + OSM fetch), `/login`, `/admin` (list/update/search). *(Note: `/logout` is linked in admin UI but not implemented in the provided `app.py`; adding a simple logout route that clears the admin session is recommended.)*

---

## 5. Implementation Details

### 5.1 Key Algorithms

**Haversine distance**

- Input: two (lat, lon) pairs.
- Output: distance in km.
- Used to filter hospitals within the user-selected radius and to sort results by distance.

**OSM Overpass query**

- Query type: `node`, `way`, `relation` with `amenity=hospital` and `around:{radius_m},{lat},{lon}`.
- Response: JSON with elements; for each element, name from tags, coordinates from `lat`/`lon` or `center`.
- Insert into `hospitals` only if name does not already exist (avoids duplicates).

### 5.2 User Flow

1. User opens `/` → sees hero, radius dropdown, “Find Nearby Hospitals” button, and any existing hospital cards (distance shown as “Allow location” until location is set).
2. User clicks “Find Nearby Hospitals” → browser asks for location → on success, GET `/location?lat=&lon=&radius=` → server stores in session and calls OSM → response "OK" → page reloads.
3. On reload, server has session lat/lon/radius → filters hospitals by distance, sorts by distance → template shows cards with numeric distance and a map with markers.
4. Admin: goes to `/login` → enters credentials → redirected to `/admin` → can search and update general/ICU beds per hospital.

### 5.3 Security Considerations (Demo)

- Admin password is hardcoded (admin/admin123); suitable only for demo.
- Session secret is fixed; production should use environment variable and HTTPS.
- No CSRF protection on admin forms; production should add tokens.
- `/logout` is referenced in admin template but route is missing in the provided code; should be implemented to clear session.

---

## 6. Testing & Validation

- **Manual testing:** Location allow/deny, radius change, OSM fetch, map display, card data, admin login, bed update, search.
- **Edge cases:** No location permission (message and no map), empty hospital list (e.g. no OSM data in radius), first-time DB creation via `init_db()`.

---

## 7. Results & Discussion

- The application successfully integrates geolocation, OSM data, and admin-maintained bed counts.
- Users get a clear list of nearby hospitals with distance and bed availability and a map for visual reference.
- Admins can keep bed counts updated and find hospitals by name.
- Limitations: OSM data quality and completeness vary by region; bed counts are manual; no real-time integration with hospital systems; demo-level security and no `/logout` implementation in the provided snippet.

---

## 8. Conclusion

The **Hospital Bed Finder** project meets its stated goals: it provides a working demo for finding nearby hospitals by location, displays general and ICU bed information, shows results on a map, and offers an admin panel for maintaining bed data. The use of Flask, SQLite, and OpenStreetMap keeps the system simple and suitable for extension (e.g. proper auth, CSRF, `/logout`, and optional APIs for real-time bed data). The project is suitable as a portfolio or academic project and as a base for a more robust emergency bed-finding system.

---

## 9. References & Appendix

### 9.1 References

- Flask: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
- OpenStreetMap / Overpass API: [https://wiki.openstreetmap.org/wiki/Overpass_API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- Leaflet: [https://leafletjs.com/](https://leafletjs.com/)
- Haversine formula: standard formula for great-circle distance between two points on a sphere.

### 9.2 Project Structure

```
hospital-bed-finder/
├── app.py              # Flask app, routes, DB, OSM, distance logic
├── hospitals.db        # SQLite database (created at first run)
├── ABSTRACT.md         # Abstract of the project
├── FINAL_PROJECT_REPORT.md  # This report
├── static/
│   ├── style.css       # Global styles
│   └── manifest.json   # PWA manifest (if used)
└── templates/
    ├── index.html      # Home: controls, map, hospital cards
    ├── login.html      # Admin login form
    └── admin.html      # Admin: search, hospital list, bed update forms
```

### 9.3 How to Run

1. Install Python 3 and dependencies (e.g. `flask`, `requests`).
2. From project root: `python app.py`.
3. Open browser to `http://127.0.0.1:5000/`.
4. Use “Find Nearby Hospitals” (allow location), then view results and map.
5. Admin: go to `/login`, use admin / admin123, then update beds or search from `/admin`.

---

*End of Report*
