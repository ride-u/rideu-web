from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
from datetime import datetime
import os

app = FastAPI()

DB_PATH = "rideu.db"
FIXED_PIN = "1234"

gps_data = {
    "scooter": "SC01",
    "lat": 14.6349,
    "lon": -90.5069,
    "speed": 0,
    "last_update": "Sin datos reales todavía",
    "serial_status": "Esperando bridge GPS"
}

app.mount("/static", StaticFiles(directory="static"), name="static")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            carnet TEXT NOT NULL,
            zigi_code TEXT NOT NULL,
            plan TEXT NOT NULL,
            pin TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


@app.head("/")
def head_home():
    return


@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>RIDE U</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>

    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f3f4f6;
            color: #111827;
        }

        header {
            background: #111827;
            color: white;
            padding: 16px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
        }

        .container {
            max-width: 1200px;
            margin: auto;
            padding: 20px;
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 20px;
        }

        .card {
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 5px 18px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }

        .logo {
            width: 190px;
            display: block;
            margin: 0 auto 18px auto;
            border-radius: 10px;
        }

        .qr {
            width: 210px;
            display: block;
            margin: 10px auto;
            border-radius: 10px;
            border: 1px solid #e5e7eb;
        }

        h2 {
            margin-top: 0;
        }

        .conditions {
            background: #fff7ed;
            border-left: 5px solid #f97316;
            padding: 12px;
            border-radius: 10px;
            font-size: 14px;
            margin-bottom: 15px;
        }

        .conditions ul {
            padding-left: 18px;
            margin-bottom: 0;
        }

        label {
            display: block;
            margin-top: 12px;
            font-size: 14px;
            font-weight: bold;
        }

        input, select {
            width: 100%;
            padding: 12px;
            margin-top: 6px;
            box-sizing: border-box;
            border: 1px solid #d1d5db;
            border-radius: 10px;
            font-size: 16px;
        }

        button {
            width: 100%;
            margin-top: 18px;
            padding: 15px;
            background: #16a34a;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover {
            background: #15803d;
        }

        .pin-box {
            margin-top: 18px;
            background: #dcfce7;
            color: #065f46;
            text-align: center;
            border-radius: 14px;
            padding: 20px;
            font-size: 32px;
            font-weight: bold;
        }

        .pin-box small {
            display: block;
            font-size: 14px;
            margin-top: 8px;
        }

        #map {
            height: 430px;
            border-radius: 14px;
            margin-top: 10px;
        }

        .gps-info {
            background: #f9fafb;
            border-radius: 12px;
            padding: 12px;
            margin-top: 12px;
            font-size: 14px;
        }

        .gps-row {
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid #e5e7eb;
            padding: 7px 0;
            gap: 10px;
        }

        .gps-row:last-child {
            border-bottom: none;
        }

        .gps-row b {
            text-align: right;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }

        th, td {
            border-bottom: 1px solid #e5e7eb;
            padding: 9px;
            text-align: left;
        }

        th {
            background: #f9fafb;
        }

        @media (max-width: 850px) {
            .container {
                grid-template-columns: 1fr;
            }

            header {
                font-size: 21px;
            }

            table {
                font-size: 12px;
            }
        }
    </style>
</head>

<body>
    <header>RIDE U</header>

    <div class="container">

        <div>
            <div class="card">
                <img src="/static/logo.jpeg" class="logo">

                <h2>Generar acceso</h2>

                <div class="conditions">
                    <b>Condiciones de uso:</b>
                    <ul>
                        <li>Solo una persona a la vez.</li>
                        <li>Uso responsable dentro del área permitida.</li>
                        <li>Prioridad a peatones.</li>
                        <li>No usar bajo lluvia o condiciones inseguras.</li>
                        <li>El estudiante es responsable durante el uso del prototipo.</li>
                    </ul>
                </div>

                <label>Nombre del estudiante</label>
                <input id="studentName" placeholder="Ejemplo: Juan Pérez">

                <label>No. de carné</label>
                <input id="studentCarnet" placeholder="Ejemplo: 202412345">

                <label>Plan</label>
                <select id="plan">
                    <option value="Q3">Q3</option>
¿
                </select>

                <label>Código / comprobante Zigi</label>
                <input id="zigiCode" placeholder="Ejemplo: ZIGI-123456">

                <button onclick="generatePin()">Ya pagué con Zigi. Generar PIN</button>

                <div class="pin-box">
                    PIN: <span id="pinText">----</span>
                    <small>Presiona # para ENTER en el teclado del scooter</small>
                </div>
            </div>

            <div class="card">
                <h2>QR de acceso</h2>
                <p>Escanea este QR para realizar el pago.</p>
                <img src="/static/qr.jpeg" class="qr">
            </div>
        </div>

        <div>
            <div class="card">
                <h2>Mapa GPS del scooter</h2>
                <div id="map"></div>

                <div class="gps-info">
                    <div class="gps-row"><span>Scooter</span><b id="gpsScooter">SC01</b></div>
                    <div class="gps-row"><span>Latitud</span><b id="gpsLat">---</b></div>
                    <div class="gps-row"><span>Longitud</span><b id="gpsLon">---</b></div>
                    <div class="gps-row"><span>Velocidad</span><b id="gpsSpeed">---</b></div>
                    <div class="gps-row"><span>Última actualización</span><b id="gpsUpdate">---</b></div>
                    <div class="gps-row"><span>Estado GPS</span><b id="gpsSerial">---</b></div>
                </div>
            </div>

            <div class="card">
                <h2>Estudiantes registrados</h2>

                <table>
                    <thead>
                        <tr>
                            <th>Nombre</th>
                            <th>Carné</th>
                            <th>Plan</th>
                            <th>Zigi</th>
                            <th>PIN</th>
                            <th>Fecha</th>
                        </tr>
                    </thead>
                    <tbody id="studentsTable"></tbody>
                </table>
            </div>
        </div>

    </div>

    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

    <script>
        const defaultLat = 14.6349;
        const defaultLon = -90.5069;

        const map = L.map('map').setView([defaultLat, defaultLon], 16);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: 'OpenStreetMap'
        }).addTo(map);

        const marker = L.marker([defaultLat, defaultLon])
            .addTo(map)
            .bindPopup("Scooter RIDE U - BASE1")
            .openPopup();

        async function updateGPS() {
            try {
                const res = await fetch("/gps");
                const data = await res.json();

                const lat = Number(data.lat);
                const lon = Number(data.lon);

                marker.setLatLng([lat, lon]);
                map.panTo([lat, lon]);

                document.getElementById("gpsScooter").innerText = data.scooter;
                document.getElementById("gpsLat").innerText = lat.toFixed(6);
                document.getElementById("gpsLon").innerText = lon.toFixed(6);
                document.getElementById("gpsSpeed").innerText = data.speed + " km/h";
                document.getElementById("gpsUpdate").innerText = data.last_update;
                document.getElementById("gpsSerial").innerText = data.serial_status;

            } catch(e) {
                console.log("GPS error:", e);
            }
        }

        async function generatePin() {
            const payload = {
                name: document.getElementById("studentName").value.trim(),
                carnet: document.getElementById("studentCarnet").value.trim(),
                plan: document.getElementById("plan").value,
                zigi_code: document.getElementById("zigiCode").value.trim()
            };

            if (!payload.name || !payload.carnet || !payload.zigi_code) {
                alert("Completa nombre, carné y comprobante Zigi.");
                return;
            }

            const res = await fetch("/generate-pin", {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (!data.ok) {
                alert(data.error);
                return;
            }

            document.getElementById("pinText").innerText = data.pin + "#";

            document.getElementById("studentName").value = "";
            document.getElementById("studentCarnet").value = "";
            document.getElementById("zigiCode").value = "";

            loadStudents();
        }

        async function loadStudents() {
            const res = await fetch("/students");
            const students = await res.json();

            document.getElementById("studentsTable").innerHTML = students.map(s => `
                <tr>
                    <td>${s.name}</td>
                    <td>${s.carnet}</td>
                    <td>${s.plan}</td>
                    <td>${s.zigi_code}</td>
                    <td>${s.pin}#</td>
                    <td>${s.created_at}</td>
                </tr>
            `).join("");
        }

        updateGPS();
        setInterval(updateGPS, 2000);
        loadStudents();
    </script>

</body>
</html>
    """


@app.get("/gps")
def gps():
    return gps_data


@app.post("/update-gps")
async def update_gps(request: Request):
    global gps_data

    try:
        data = await request.json()

        gps_data["scooter"] = data.get("scooter", "SC01")
        gps_data["lat"] = float(data.get("lat", 0))
        gps_data["lon"] = float(data.get("lon", 0))
        gps_data["speed"] = float(data.get("speed", 0))
        gps_data["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        gps_data["serial_status"] = "GPS ONLINE"

        return {"ok": True, "gps": gps_data}

    except Exception as e:
        return JSONResponse({
            "ok": False,
            "error": str(e)
        }, status_code=400)


@app.post("/generate-pin")
async def generate_pin(request: Request):
    data = await request.json()

    name = data.get("name", "").strip()
    carnet = data.get("carnet", "").strip()
    zigi_code = data.get("zigi_code", "").strip()
    plan = data.get("plan", "").strip()

    if not name or not carnet or not zigi_code:
        return JSONResponse({
            "ok": False,
            "error": "Faltan datos"
        })

    pin = FIXED_PIN
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO students (name, carnet, zigi_code, plan, pin, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, carnet, zigi_code, plan, pin, created_at))

    conn.commit()
    conn.close()

    return {"ok": True, "pin": pin}


@app.get("/students")
def students():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT name, carnet, zigi_code, plan, pin, created_at
        FROM students
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "name": r[0],
            "carnet": r[1],
            "zigi_code": r[2],
            "plan": r[3],
            "pin": r[4],
            "created_at": r[5]
        }
        for r in rows
    ]


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)