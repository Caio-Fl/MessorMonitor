import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
import uvicorn

app = FastAPI()
BASE_DIR = "DataBank"

# Health check (OK manter)
@app.get("/")
@app.head("/")
async def health_check():
    return Response(content="OK", status_code=200)

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

        # 👉 append (não sobrescreve)
        with open(path, 'a') as f:
            f.write(json.dumps(data) + "\n")

        print(f"[{datetime.now()}] Dados salvos: {path}")

    except Exception as e:
        print(f"Erro ao salvar: {e}")

# ✅ WebSocket LIMPO e dedicado
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Cliente LabVIEW conectado!")

    try:
        while True:
            data = await websocket.receive_json()

            # salva sem travar o WS
            asyncio.create_task(asyncio.to_thread(save_raw_json, data))

            # 👉 ACK (IMPORTANTE pro LabVIEW)
            await websocket.send_json({
                "status": "received",
                "ts": datetime.now().isoformat()
            })

    except WebSocketDisconnect:
        print("LabVIEW desconectado.")

    except Exception as e:
        print(f"Erro no WebSocket: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9002))
    uvicorn.run(app, host="0.0.0.0", port=port)