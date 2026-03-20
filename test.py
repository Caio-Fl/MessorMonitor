import asyncio
import websockets
import time

URI = "wss://messor-api.onrender.com/ws"  # ajuste se necessário

async def websocket_cycle():
    while True:  # loop infinito de reconexão
        try:
            print("🔌 Tentando conectar...")
            async with websockets.connect(URI) as ws:
                print("✅ Conectado!")

                while True:
                    # mensagem de teste (ajuste se precisar JSON)
                    msg = {"type": "ping", "timestamp": time.time()}
                    
                    await ws.send(str(msg))
                    print("➡️ Enviado:", msg)

                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=10)
                        print("⬅️ Recebido:", response)
                    except asyncio.TimeoutError:
                        print("⚠️ Timeout sem resposta")

                    await asyncio.sleep(5)  # intervalo do ciclo

        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
            print("🔁 Reconectando em 5s...\n")
            await asyncio.sleep(5)

asyncio.run(websocket_cycle())