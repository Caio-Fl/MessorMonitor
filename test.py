import asyncio
import websockets
import json
import time

URI = "wss://messor-api.onrender.com/websockets/echo"

async def ciclo():
    while True:
        try:
            print("🔌 Conectando...")
            async with websockets.connect(URI) as ws:
                print("✅ Conectado!")

                while True:
                    payload = {
                        "header": {
                            "topics": ["root/UAM1/SRV1/CH1"]
                        },
                        "value": time.time()
                    }

                    await ws.send(json.dumps(payload))
                    print("➡️ Enviado")

                    # seu servidor ainda não responde → pode dar timeout
                    try:
                        resp = await asyncio.wait_for(ws.recv(), timeout=3)
                        print("⬅️ Recebido:", resp)
                    except:
                        print("⚠️ Sem resposta (normal no seu caso)")

                    await asyncio.sleep(2)

        except Exception as e:
            print("❌ Erro:", e)
            print("🔁 Reconectando...\n")
            await asyncio.sleep(5)

asyncio.run(ciclo())