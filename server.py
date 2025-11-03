'''import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Przechowujemy aktywne połączenia
robot_ws = None
client_ws = None

# Serwujemy pliki statyczne (strona HTML)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.websocket("/ws/robot")
async def robot_endpoint(websocket: WebSocket):
    global robot_ws
    await websocket.accept()
    robot_ws = websocket
    print("Robot connected")
    try:
        while True:
            # Robot może też wysyłać status (opcjonalnie)
            data = await websocket.receive_text()
            print("Robot says:", data)
    except WebSocketDisconnect:
        print("Robot disconnected")
        robot_ws = None

@app.websocket("/ws/client")
async def client_endpoint(websocket: WebSocket):
    global client_ws, robot_ws
    await websocket.accept()
    client_ws = websocket
    print("Client connected")
    try:
        while True:
            cmd = await websocket.receive_text()
            print("Client command:", cmd)
            # Przekazujemy komendę do robota, jeśli jest połączony
            if robot_ws is not None:
                await robot_ws.send_text(cmd)
    except WebSocketDisconnect:
        print("Client disconnected")
        client_ws = None

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
