import asyncio
import websockets
import json
import os
from datetime import datetime

# Porta injetada pelo Render
PORT = int(os.environ.get("PORT", 9002))
BASE_DIR = "DataBank"

# Função corrigida para a versão estável do websockets
async def process_request(request):
    """
    Responde às verificações de 'está vivo' (Health Checks) do Render.
    O Render envia requisições HTTP HEAD/GET para checar o servidor.
    """
    # Verifica se não é um pedido de Upgrade para WebSocket (como o do Render)
    if request.headers.get("Upgrade") != "websocket":
        return request.respond(websockets.http.HTTPStatus.OK, "OK\n")
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
        print(f"[{datetime.now()}] Dados salvos: {path}")
    except Exception as e:
        print(f"Erro ao salvar: {e}")

async def data_handler(websocket):
    print(f"Cliente conectado: {websocket.remote_address}")
    try:
        async for message in websocket:
            data = json.loads(message)
            save_raw_json(data)
    except Exception:
        print("Conexão encerrada pelo cliente.")

async def main():
    print(f"Iniciando Coletor Messor na porta {PORT}...")
    # O parâmetro process_request agora recebe o objeto request corretamente
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