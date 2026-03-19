import asyncio
import websockets
import json
import os

# O Render injeta a porta automaticamente aqui
PORT = int(os.environ.get("PORT", 9002))
BASE_DIR = "DataBank"

def save_raw_json(data):
    header = data.get('header', {})
    topics = header.get('topics', ["Geral/Desconhecido"])
    topic = topics[0]
    
    # Organiza as pastas igual ao seu main_dashboard
    parts = [x for x in topic.split('/') if x]
    uam = parts[1] if len(parts) > 1 else "Geral"
    srv = parts[2] if len(parts) > 2 else "Servico"
    chn = "_".join(parts[3:]) if len(parts) > 3 else "Canal"
    
    folder = os.path.join(BASE_DIR, uam, srv)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{chn}.json")
    
    with open(path, 'w') as f:
        json.dump(data, f)
    print(f"[{datetime.now()}] Dados salvos em: {path}")

async def data_handler(websocket):
    print(f"Cliente LabVIEW conectado!")
    try:
        async for message in websocket:
            data = json.loads(message)
            save_raw_json(data)
    except Exception as e:
        print(f"Conexão encerrada ou erro: {e}")

async def main():
    print(f"Servidor Coletor Messor iniciado na porta {PORT}")
    async with websockets.serve(data_handler, "0.0.0.0", PORT, max_size=2**26):
        await asyncio.Future() # Mantém rodando

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(main())