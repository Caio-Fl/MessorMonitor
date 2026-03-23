import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()
BASE_DIR = "DataBank"

# =========================
# HEALTH CHECK (Render)
# =========================
@app.get("/")
@app.head("/")
async def health_check():
    return Response(content="OK", status_code=200)


# =========================
# SALVAMENTO (NDJSON)
# =========================
def save_raw_json(data):
    try:
        header = data.get('header', {})
        topics = header.get('topics', ["Geral/Desconhecido"])
        topic = topics[0]

        parts = [x for x in topic.split('/') if x]
        uam = parts[1] if len(parts) > 1 else "Geral"
        srv = parts[2] if len(parts) > 2 else "Servico"
        chn = "_".join(parts[3:]) if len(parts) > 3 else "Canal"

        folder = os.path.join(BASE_DIR, uam, srv)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{chn}.json")

        # append (NDJSON)
        with open(path, 'a') as f:
            f.write(json.dumps(data) + "\n")

        print(f"[{datetime.now()}] Dados salvos: {path}")

    except Exception as e:
        print(f"Erro ao salvar: {e}")


# =========================
# WEBSOCKET (LABVIEW)
# =========================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔌 Cliente LabVIEW conectado!")

    try:
        while True:
            data = await websocket.receive_json()

            # salva sem travar
            asyncio.create_task(asyncio.to_thread(save_raw_json, data))

            # ACK (ESSENCIAL pro LabVIEW)
            await websocket.send_json({
                "status": "received",
                "ts": datetime.now().isoformat()
            })

    except WebSocketDisconnect:
        print("❌ LabVIEW desconectado.")

    except Exception as e:
        print(f"Erro no WebSocket: {e}")


# =========================
# API - TODOS OS DADOS
# =========================
@app.get("/data")
def get_data(limit: int = 50):
    result = []   # ✅ agora é lista (formato correto)

    try:
        for root, dirs, files in os.walk(BASE_DIR):
            for file in files:
                if file.endswith(".json"):
                    path = os.path.join(root, file)

                    try:
                        with open(path, "r") as f:
                            lines = f.readlines()
                            last_lines = lines[-limit:]

                            for line in last_lines:
                                try:
                                    result.append(json.loads(line))  # ✅ evento direto
                                except:
                                    continue

                    except Exception as e:
                        print(f"Erro lendo {path}: {e}")

    except Exception as e:
        print(f"Erro geral: {e}")

    return JSONResponse(content=result)


# =========================
# API - POR CANAL
# =========================
@app.get("/data/{uam}/{srv}/{chn}")
def get_channel(uam: str, srv: str, chn: str, limit: int = 50):
    path = os.path.join(BASE_DIR, uam, srv, f"{chn}.json")

    if not os.path.exists(path):
        return JSONResponse(content={"error": "not found"}, status_code=404)

    try:
        with open(path, "r") as f:
            lines = f.readlines()
            last_lines = lines[-limit:]

            parsed = []
            for line in last_lines:
                try:
                    parsed.append(json.loads(line))
                except:
                    continue

        return JSONResponse(content=parsed)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# =========================
# API - LISTA DE CANAIS
# =========================
@app.get("/channels")
def list_channels():
    channels = []

    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".json"):
                rel = os.path.relpath(os.path.join(root, file), BASE_DIR)
                channels.append(rel.replace("\\", "/"))

    return {"channels": channels}


# =========================
# MAIN (Render)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render define isso
    uvicorn.run(app, host="0.0.0.0", port=port)