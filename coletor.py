import asyncio
import websockets
import json
import os
from datetime import datetime

PORT = int(os.environ.get("PORT", 9002))
BASE_DIR = "DataBank"

# Função para responder ao "Health Check" do Render
async def process_request(path, request_headers):
    # Se o Render enviar um HEAD ou GET comum (não-websocket), respondemos 200 OK
    if "Upgrade" not in request_headers:
        return websockets.http.HTTPStatus.OK, [], b"OK\n"
    return None

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
        print(f"[{datetime.now()}] Dados salvos com sucesso.")
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")

async def data_handler(websocket):
    print(f"Cliente conectado!")
    try:
        async for message in websocket:
            data = json.loads(message)
            save_raw_json(data)
    except Exception as e:
        print(f"Conexão encerrada.")

async def main():
    print(f"Iniciando Coletor Inteligente na porta {PORT}...")
    # O segredo está no 'process_request' para calar os erros do Render
    async with websockets.serve(
        data_handler, 
        "0.0.0.0", 
        PORT, 
        process_request=process_request,
        max_size=2**26
    ):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())