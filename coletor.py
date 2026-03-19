import os
import json
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
import uvicorn

app = FastAPI()
BASE_DIR = "DataBank"

# 1. Resposta para o "Health Check" do Render (Cura o erro de HEAD/GET)
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
        
        with open(path, 'w') as f:
            json.dump(data, f)
        print(f"[{datetime.now()}] Dados salvos: {path}")
    except Exception as e:
        print(f"Erro ao salvar: {e}")

# 2. Rota WebSocket para o LabVIEW
# Aceita tanto a raiz "/" quanto "/websockets/echo"
@app.websocket("/")
@app.websocket("/websockets/echo")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print(f"Cliente LabVIEW conectado via WebSocket!")
    try:
        while True:
            # Recebe o JSON do LabVIEW
            data = await websocket.receive_json()
            save_raw_json(data)
    except WebSocketDisconnect:
        print("LabVIEW desconectado.")
    except Exception as e:
        print(f"Erro no WebSocket: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9002))
    # Roda o servidor Uvicorn (padrão para FastAPI)
    uvicorn.run(app, host="0.0.0.0", port=port)