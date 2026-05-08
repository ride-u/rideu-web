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

body{
    margin:0;
    font-family:Arial;
    background:#f3f4f6;
}

header{
    background:#111827;
    color:white;
    padding:16px;
    text-align:center;
    font-size:24px;
    font-weight:bold;
}

.container{
    max-width:1200px;
    margin:auto;
    padding:20px;
    display:grid;
    grid-template-columns:380px 1fr;
    gap:20px;
}

.card{
    background:white;
    border-radius:16px;
    padding:20px;
    box-shadow:0 5px 18px rgba(0,0,0,0.08);
    margin-bottom:20px;
}

.logo{
    width:190px;
    display:block;
    margin:auto;
}

.qr{
    width:220px;
    display:block;
    margin:auto;
}

label{
    display:block;
    margin-top:12px;
    font-weight:bold;
}

input,select{
    width:100%;
    padding:12px;
    margin-top:6px;
    border-radius:10px;
    border:1px solid #d1d5db;
    box-sizing:border-box;
}

button{
    width:100%;
    margin-top:18px;
    padding:15px;
    background:#16a34a;
    color:white;
    border:none;
    border-radius:10px;
    font-size:16px;
    font-weight:bold;
}

.pin-box{
    margin-top:18px;
    background:#dcfce7;
    padding:20px;
    border-radius:14px;
    text-align:center;
    font-size:32px;
    font-weight:bold;
}

#map{
    height:430px;
    border-radius:14px;
}

.gps-info{
    margin-top:10px;
    background:#f9fafb;
    padding:12px;
    border-radius:12px;
}

.gps-row{
    display:flex;
    justify-content:space-between;
    padding:7px 0;
    border-bottom:1px solid #e5e7eb;
}

table{
    width:100%;
    border-collapse:collapse;
}

th,td{
    border-bottom:1px solid #e5e7eb;
    padding:8px;
    text-align:left;
}

@media(max-width:850px){
    .container{
        grid-template-columns:1fr;
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

<label>Nombre estudiante</label>
<input id="studentName">

<label>No. Carné</label>
<input id="studentCarnet">

<label>Plan</label>
<select id="plan">
<option value="Q5">Q5</option>
<option value="Q10">Q10</option>
<option value="Q15">Q15</option>
<option value="Q20">Q20</option>
</select>

<label>Comprobante Zigi</label>
<input id="zigiCode">

<button onclick="generatePin()">
Ya pagué con Zigi. Generar PIN
</button>

<div class="pin-box">
PIN: <span id="pinText">----</span>
</div>

</div>

<div class="card">
<h2>QR</h2>
<img src="/static/qr.jpeg" class="qr">
</div>

</div>

<div>

<div class="card">

<h2>Mapa GPS</h2>

<div id="map"></div>

<div class="gps-info">

<div class="gps-row">
<span>Scooter</span>
<b id="gpsScooter">SC01</b>
</div>

<div class="gps-row">
<span>Latitud</span>
<b id="gpsLat">---</b>
</div>

<div class="gps-row">
<span>Longitud</span>
<b id="gpsLon">---</b>
</div>

<div class="gps-row">
<span>Velocidad</span>
<b id="gpsSpeed">---</b>
</div>

<div class="gps-row">
<span>Estado</span>
<b id="gpsStatus">Esperando...</b>
</div>

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

const map = L.map('map').setView([14.6349,-90.5069],16);

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
{
maxZoom:19
}
).addTo(map);

const marker = L.marker([14.6349,-90.5069])
.addTo(map);

async function updateGPS(){

    try{

        const res = await fetch("/gps");
        const data = await res.json();

        const lat = Number(data.lat);
        const lon = Number(data.lon);

        marker.setLatLng([lat,lon]);

        map.panTo([lat,lon]);

        document.getElementById("gpsScooter").innerText = data.scooter;
        document.getElementById("gpsLat").innerText = lat.toFixed(6);
        document.getElementById("gpsLon").innerText = lon.toFixed(6);
        document.getElementById("gpsSpeed").innerText = data.speed + " km/h";
        document.getElementById("gpsStatus").innerText = data.serial_status;

    }catch(e){
        console.log(e);
    }
}

async function generatePin(){

    const payload = {
        name: document.getElementById("studentName").value,
        carnet: document.getElementById("studentCarnet").value,
        plan: document.getElementById("plan").value,
        zigi_code: document.getElementById("zigiCode").value
    };

    const res = await fetch("/generate-pin",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify(payload)
    });

    const data = await res.json();

    document.getElementById("pinText").innerText = data.pin + "#";

    loadStudents();
}

async function loadStudents(){

    const res = await fetch("/students");
    const data = await res.json();

    document.getElementById("studentsTable").innerHTML =
    data.map(s=>`
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
loadStudents();

setInterval(updateGPS,2000);

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

    data = await request.json()

    gps_data["scooter"] = data.get("scooter", "SC01")
    gps_data["lat"] = float(data.get("lat", 0))
    gps_data["lon"] = float(data.get("lon", 0))
    gps_data["speed"] = float(data.get("speed", 0))
    gps_data["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    gps_data["serial_status"] = "GPS ONLINE"

    return {"ok": True}


@app.post("/generate-pin")
async def generate_pin(request: Request):

    data = await request.json()

    name = data.get("name","")
    carnet = data.get("carnet","")
    zigi_code = data.get("zigi_code","")
    plan = data.get("plan","")

    pin = FIXED_PIN

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO students
        (name,carnet,zigi_code,plan,pin,created_at)
        VALUES (?,?,?,?,?,?)
    """,(name,carnet,zigi_code,plan,pin,created_at))

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "pin": pin
    }


@app.get("/students")
def students():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT name,carnet,zigi_code,plan,pin,created_at
        FROM students
        ORDER BY id DESC
    """)

    rows = cur.fetchall()

    conn.close()

    return [
        {
            "name":r[0],
            "carnet":r[1],
            "zigi_code":r[2],
            "plan":r[3],
            "pin":r[4],
            "created_at":r[5]
        }
        for r in rows
    ]


if __name__ == "__main__":

    import uvicorn

    port = int(os.environ.get("PORT",8000))

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port
    )