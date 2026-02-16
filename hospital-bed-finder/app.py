from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import math
import requests

app = Flask(__name__)
app.secret_key = "hospital_secret_key"


# ---------------- DATABASE CONNECTION ----------------
def get_db_connection():
    conn = sqlite3.connect("hospitals.db", timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- CREATE TABLE ----------------
def init_db():
    conn = get_db_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS hospitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        latitude REAL,
        longitude REAL,
        general_beds INTEGER DEFAULT 0,
        icu_beds INTEGER DEFAULT 0,
        contact TEXT DEFAULT 'Not Available'
    )
    """)
    conn.commit()
    conn.close()

init_db()


# ---------------- DISTANCE FUNCTION ----------------
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)


# ---------------- FETCH REAL HOSPITALS ----------------
def fetch_real_hospitals_osm(lat, lon, radius):
    conn = get_db_connection()

    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json];
    node["amenity"="hospital"](around:{radius*1000},{lat},{lon});
    out;
    """

    response = requests.post(overpass_url, data=query)

    if response.status_code != 200:
        return

    data = response.json()

    for element in data["elements"]:
        name = element["tags"].get("name", "Unnamed Hospital")
        h_lat = element["lat"]
        h_lon = element["lon"]

        exists = conn.execute(
            "SELECT * FROM hospitals WHERE name=?",
            (name,)
        ).fetchone()

        if not exists:
            conn.execute("""
                INSERT INTO hospitals (name, latitude, longitude)
                VALUES (?, ?, ?)
            """, (name, h_lat, h_lon))

    conn.commit()
    conn.close()


# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    conn = get_db_connection()
    hospitals = conn.execute("SELECT * FROM hospitals").fetchall()
    conn.close()

    lat = session.get("lat")
    lon = session.get("lon")
    radius = session.get("radius", 50)

    result = []

    if not lat or not lon:
        for h in hospitals:
            result.append({
                "id": h["id"],
                "name": h["name"],
                "general_beds": h["general_beds"],
                "icu_beds": h["icu_beds"],
                "contact": h["contact"],
                "latitude": h["latitude"],
                "longitude": h["longitude"],
                "distance": "Allow location"
            })
    else:
        for h in hospitals:
            if h["latitude"] and h["longitude"]:
                dist = calculate_distance(lat, lon, h["latitude"], h["longitude"])
                if dist <= radius:
                    result.append({
                        "id": h["id"],
                        "name": h["name"],
                        "general_beds": h["general_beds"],
                        "icu_beds": h["icu_beds"],
                        "contact": h["contact"],
                        "latitude": h["latitude"],
                        "longitude": h["longitude"],
                        "distance": dist
                    })

        result.sort(key=lambda x: x["distance"])

    return render_template("index.html", hospitals=result, radius=radius)


# ---------------- LOCATION SEARCH ----------------
@app.route("/location")
def location():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    radius = int(request.args.get("radius", 50))

    session["lat"] = lat
    session["lon"] = lon
    session["radius"] = radius

    fetch_real_hospitals_osm(lat, lon, radius)

    return "OK"


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin_logged"] = True
            return redirect("/admin")
        else:
            return "Invalid Login"

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin():

    if not session.get("admin_logged"):
        return redirect("/login")

    search = request.args.get("search", "")

    conn = get_db_connection()

    if search:
        hospitals = conn.execute(
            "SELECT * FROM hospitals WHERE name LIKE ? LIMIT 20",
            ('%' + search + '%',)
        ).fetchall()
    else:
        hospitals = conn.execute(
            "SELECT * FROM hospitals ORDER BY name LIMIT 20"
        ).fetchall()

    conn.close()

    return render_template("admin.html", hospitals=hospitals, search=search)


# ---------------- UPDATE BEDS ----------------
@app.route("/update_beds", methods=["POST"])
def update_beds():

    if not session.get("admin_logged"):
        return redirect("/login")

    hospital_id = request.form["id"]
    general = request.form["general_beds"]
    icu = request.form["icu_beds"]

    conn = get_db_connection()

    conn.execute(
        "UPDATE hospitals SET general_beds=?, icu_beds=? WHERE id=?",
        (general, icu, hospital_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
