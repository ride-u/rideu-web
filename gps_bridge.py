import serial
import requests
import time

SERIAL_PORT = "/dev/cu.usbmodem101"
BAUDRATE = 115200

SERVER_URL = "https://rideu-web-1.onrender.com/update-gps"


def main():
    print("===================================")
    print(" RIDE U - GPS BRIDGE")
    print("===================================")
    print(f"[BRIDGE] Serial: {SERIAL_PORT}")
    print(f"[BRIDGE] Render: {SERVER_URL}")

    while True:
        try:
            print(f"[SERIAL] Conectando a {SERIAL_PORT}...")
            ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
            print("[SERIAL] Conectado")

            while True:
                line = ser.readline().decode(errors="ignore").strip()

                if not line:
                    continue

                print("[SERIAL RX]", line)

                # Formato esperado:
                # SC01,GPS,14.634915,-90.506882,0.0
                parts = line.split(",")

                if len(parts) < 5:
                    print("[SKIP] Formato incompleto")
                    continue

                scooter_id = parts[0].strip()
                msg_type = parts[1].strip()

                if msg_type != "GPS":
                    print("[SKIP] No es GPS")
                    continue

                payload = {
                    "scooter": scooter_id,
                    "lat": float(parts[2]),
                    "lon": float(parts[3]),
                    "speed": float(parts[4])
                }

                response = requests.post(SERVER_URL, json=payload, timeout=5)

                if response.status_code == 200:
                    print("[UPLOAD OK]", payload)
                else:
                    print("[UPLOAD ERROR]", response.status_code, response.text)

        except serial.SerialException as e:
            print("[SERIAL ERROR]", e)
            print("[INFO] Revisa que el Arduino esté conectado y que el COM sea correcto.")
            time.sleep(3)

        except requests.RequestException as e:
            print("[INTERNET ERROR]", e)
            time.sleep(3)

        except Exception as e:
            print("[ERROR]", e)
            time.sleep(3)


if __name__ == "__main__":
    main()