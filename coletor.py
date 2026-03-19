import asyncio
import websockets
import json
import os
from datetime import datetime

# Porta dinâmica do Render
PORT = int(os.environ.get("PORT", 9002))
BASE_DIR = "DataBank"

async def process_request(*args):
    """
    Captura as verificações de saúde (Health Checks) do Render.
    Retorna uma resposta HTTP 200 OK sem depender de métodos do objeto Request.
    """
    # Nas versões novas, o request é o segundo argumento se o primeiro for a conexão
    request = args[1] if len(args) > 1 else args[0]
    
    # Se não for um pedido de WebSocket (Upgrade), responde HTTP 200
    if request.headers.get("Upgrade") != "websocket":
        # Retornamos (Status, Headers, Body)
        return (websockets.http.HTTPStatus.OK, [], b"OK\n")
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
        print(f"[{datetime.now()}] Dados persistidos em: {path}")
    except Exception as e:
        print(f"Erro ao salvar: {e}")

async def data_handler(websocket):
    print(f"Nova conexão estabelecida!")
    try:
        async for message in websocket:
            data = json.loads(message)
            save_raw_json(data)
    except Exception:
        pass

async def main():
    print(f"Servidor Coletor Messor ativo na porta {PORT}...")
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