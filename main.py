import os
import re
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from ml_service import MercadoLivreService

# Carrega as variáveis do arquivo .env
load_dotenv()

# Variáveis do Telegram
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SEU_CANAL = os.getenv("SEU_CANAL")

# Trata múltiplos canais na variável CANAL_ORIGEM (separados por vírgula)
CANAL_ORIGEM_RAW = os.getenv("CANAL_ORIGEM", "")
CANAIS_ORIGEM = []

for item in CANAL_ORIGEM_RAW.split(","):
    canal = item.strip()
    if canal:
        # Tenta converter para inteiro se for ID numérico (ex: -100123456789)
        try:
            CANAIS_ORIGEM.append(int(canal))
        except ValueError:
            CANAIS_ORIGEM.append(canal)

# Inicializa o serviço do ML e o Cliente do Telegram
ml_service = MercadoLivreService()
client = TelegramClient("sessao_botpromo", API_ID, API_HASH)

# Regex para identificar links do Mercado Livre
REGEX_ML = r"(https?://(?:[a-zA-Z0-9-]+\.)?mercadolivre\.com\.br/[^\s]+|https?://mercadolivre\.com/[^\s]+|https?://[a-zA-Z0-9-]+\.mercadolibre\.com/[^\s]+)"

@client.on(events.NewMessage(chats=CANAIS_ORIGEM))
async def processar_mensagem(event):
    texto_original = event.message.text
    if not texto_original:
        return

    # Procura por links do Mercado Livre no texto da mensagem
    links_encontrados = re.findall(REGEX_ML, texto_original)

    if not links_encontrados:
        return

    print(f"\n📩 Nova oferta recebida! Encontrado(s) {len(links_encontrados)} link(s) do ML.")

    texto_final = texto_original

    # Garante que o access_token do ML esteja valido antes de processar
    try:
        ml_service.renovar_token()
    except Exception as e:
        print(f"⚠️ Erro ao renovar token do ML: {e}")
        return

    # Substitui cada link original pelo seu link encurtado/gerado de afiliado
    for link in links_encontrados:
        try:
            # Chama o metodo de conversao da sua classe MercadoLivreService
            link_afiliado = ml_service.gerar_link_afiliado(link)
            texto_final = texto_final.replace(link, link_afiliado)
            print(f"✅ Link convertido com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao converter o link {link}: {e}")

    # Reenvia a mensagem (com fotos/mídias se houver) para o seu canal
    try:
        if event.message.media:
            await client.send_file(
                SEU_CANAL,
                file=event.message.media,
                caption=texto_final
            )
        else:
            await client.send_message(SEU_CANAL, texto_final)

        print(f"🚀 Oferta enviada com sucesso para {SEU_CANAL}!")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem para o canal destino: {e}")

async def main():
    print("🤖 Iniciando o Bot Promo...")
    await client.start()
    print(f"⚡ Bot online e escutando os canais: {', '.join(str(c) for c in CANAIS_ORIGEM)}")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot encerrado pelo usuário com sucesso.")