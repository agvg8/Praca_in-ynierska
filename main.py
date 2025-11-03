# main.py
# ---------------------------------------
# Serwer HTTP + WebSocket do komunikacji z ESP32 (MicroPython)
# ---------------------------------------
# - HTTP: serwuje index.html (na porcie 8080)
# - WebSocket: obsługuje połączenia z ESP32 i przeglądarką (port 8765)
# - Autoryzacja: ESP32 wysyła token 2390 → jeśli OK → serwer odsyła do strony status "authorized"
#
# Struktura:
#  * index.html  (frontend)
#  * menu.html   (po autoryzacji)
#
# Uruchom:
#   python3 main.py
#
# W przeglądarce: http://localhost:8080
# ---------------------------------------

import asyncio
import json
import websockets
import http.server
import socketserver
import threading
import os

AUTH_TOKEN = 2390
master_ws = None
browser_ws = None
master_authorized = False
PORT = int(os.environ.get("PORT", 8080))

# --- Serwer HTTP (statyczne pliki) ---
def start_http_server():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", 8080), handler) as httpd:
        print("Serwer HTTP działa na http://localhost:8080")
        httpd.serve_forever()

# --- Funkcja WebSocket ---
async def handler(websocket):
    print("Nowe połączenie TCP przyjęte!")
    global master_ws, browser_ws, master_authorized

    try:
        # pierwszy komunikat określa typ klienta
        msg = await websocket.recv()
        data = json.loads(msg)

        if data.get("role") == "master":
            if data.get("token") == AUTH_TOKEN:
                print("ESP32 zautoryzowane!")
                master_ws = websocket
                master_authorized = True
                if browser_ws:
                    await browser_ws.send(json.dumps({"status": "authorized"}))
            else:
                await websocket.send(json.dumps({"error": "invalid_token"}))
                await websocket.close()
                return

        elif data.get("role") == "browser":
            browser_ws = websocket
            print("Przeglądarka połączona.")
            # jeśli master już zautoryzowany, od razu powiadom
            if master_authorized:
                await browser_ws.send(json.dumps({"status": "authorized"}))
            else:
                await browser_ws.send(json.dumps({"status": "waiting"}))
        else:
            await websocket.send(json.dumps({"error": "unknown_role"}))
            await websocket.close()
            return

        # pętla odbioru komunikatów
        async for message in websocket:
            data = json.loads(message)

            # przeglądarka → polecenia do ESP32
            if data.get("type") == "slider" and master_ws:
                print("Otrzymano slider od przeglądarki:", data["sliders"])
                await master_ws.send(json.dumps(data))

                # ESP32 → status → przeglądarka
            elif data.get("type") == "status" and browser_ws:
                await browser_ws.send(json.dumps(data))

    except websockets.exceptions.ConnectionClosed:
        print("Połączenie zakończone.")
    finally:
        if websocket == master_ws:
            master_ws = None
            master_authorized = False
            if browser_ws:
                await browser_ws.send(json.dumps({"status": "disconnected"}))
        elif websocket == browser_ws:
            browser_ws = None

# --- Uruchomienie ---
if __name__ == "__main__":
    # Wątek HTTP
    threading.Thread(target=start_http_server, daemon=True).start()

    async def main():
        print("Serwer WebSocket na ws://0.0.0.0:8765")
        async with websockets.serve(handler, "0.0.0.0", int(os.environ.get("PORT", 8080))):
            await asyncio.Future()  # nieskończone oczekiwanie

    asyncio.run(main())



