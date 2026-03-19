import asyncio
import websockets
import json

async def diagnostic_handler(websocket):
    # Pega a URI de forma segura para qualquer versão
    uri = getattr(websocket, 'path', None) or getattr(websocket.request, 'path', 'unknown')
    print(f"\n[CONEXÃO] Messor bateu na porta! URI: {uri}")
    print(f"[CLIENTE] IP/Porta: {websocket.remote_address}")

    try:
        # Tenta enviar um "OK" para o Messor (alguns clientes precisam disso)
        await websocket.send(json.dumps({"status": "ready"}))
        print("[SERVER] Enviei sinal de 'Ready' para o Messor.")

        print("[AGUARDANDO] Esperando frames de dados...")
        async for message in websocket:
            # Se chegar aqui, o maskpayload foi resolvido e o dado está na mão
            print(f"\n[SUCESSO] Recebi um pacote de {len(message)} bytes!")
            
            # Tenta mostrar o início do JSON
            try:
                data = json.loads(message)
                topicos = data.get('header', {}).get('topics', [])
                print(f"[CONTEÚDO] Tópico: {topicos}")
                print(f"[DADO] Primeiros 100 caracteres: {str(message)[:100]}...")
            except:
                print(f"[AVISO] O dado não parece ser um JSON válido, mas o frame chegou.")

    except Exception as e:
        print(f"[ERRO] A conexão caiu: {e}")

async def main():
    print("=== TESTE DE RECEBIMENTO MESSOR (PORTA 9002) ===")
    print("Aguardando conexão do Messor...")
    
    async with websockets.serve(
        diagnostic_handler, 
        "0.0.0.0", 
        9002, 
        max_size=2**26 # 64MB
    ):
        await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTeste encerrado pelo usuário.")