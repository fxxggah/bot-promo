import os
import re
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
from telethon import TelegramClient, events
from ml_service import MercadoLivreService
from shopee_service import ShopeeService
from amazon_service import AmazonService
from aliexpress_service import AliExpressService
from kabum_service import KabumService

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
        try:
            CANAIS_ORIGEM.append(int(canal))
        except ValueError:
            CANAIS_ORIGEM.append(canal)

# Inicializa os serviços e o Cliente do Telegram
ml_service = MercadoLivreService()
shopee_service = ShopeeService()
amazon_service = AmazonService()
aliexpress_service = AliExpressService()
kabum_service = KabumService()
client = TelegramClient("sessao_botpromo", API_ID, API_HASH)

# Regex unificada abrangendo Mercado Livre, Shopee, Amazon e AliExpress
REGEX_PROMO = r"(https?://(?:[a-zA-Z0-9-]+\.)?mercadolivre\.com\.br/[^\s]+|https?://mercadolivre\.com/[^\s]+|https?://[a-zA-Z0-9-]+\.mercadolibre\.com/[^\s]+|https?://meli\.la/[^\s]+|https?://(?:[a-zA-Z0-9-]+\.)?shope\.ee/[^\s]+|https?://s\.shopee\.com\.br/[^\s]+|https?://amzn\.to/[^\s]+|https?://(?:[a-zA-Z0-9-]+\.)?amazon\.com\.br/[^\s]+|https?://(?:[a-zA-Z0-9-]+\.)?aliexpress\.com/[^\s]+|https?://a\.aliexpress\.com/[^\s]+|https?://s\.click\.aliexpress\.com/[^\s]+|https?://(?:[a-zA-Z0-9-]+\.)?kabum\.com\.br/[^\s]+)"

# Registra o momento exato em que o bot ligou para ignorar mensagens retroativas
TEMPO_INICIO = datetime.now(timezone.utc)

@client.on(events.NewMessage(chats=CANAIS_ORIGEM, incoming=True))
async def processar_mensagem(event):
    # Ignora mensagens anteriores à inicialização do bot
    if event.message.date < TEMPO_INICIO:
        return

    # Pega o texto ou a legenda da mensagem (caso venha com foto)
    texto_original = event.message.text or event.message.caption
    if not texto_original:
        return

    # Procura por links suportados
    links_encontrados = re.findall(REGEX_PROMO, texto_original)

    if not links_encontrados:
        return

    print(f"\n📩 Nova oferta recebida de {event.chat_id}! Encontrado(s) {len(links_encontrados)} link(s) compatíveis.")

    texto_final = texto_original
    
    # Variável de controle para barrar postagem caso algum link quebre
    links_convertidos_com_sucesso = True

    # Substitui cada link original pelo seu respectivo link de afiliado
    for link in links_encontrados:
        try:
            link_afiliado = None
            
            # Identifica a plataforma e aciona o serviço correspondente
            if "mercadolivre" in link or "meli.la" in link:
                ml_service.renovar_token()
                link_afiliado = await ml_service.gerar_link_afiliado(link)
            elif "shope.ee" in link or "s.shopee.com.br" in link:
                link_afiliado = await shopee_service.gerar_link_afiliado(link)
            elif "amzn.to" in link or "amazon.com.br" in link:
                link_afiliado = await amazon_service.gerar_link_afiliado(link)
            elif "aliexpress.com" in link or "a.aliexpress.com" in link or "s.click.aliexpress.com" in link:
                link_afiliado = await aliexpress_service.gerar_link_afiliado(link)
            elif "kabum.com.br" in link:
                link_afiliado = await kabum_service.gerar_link_afiliado(link)

            if link_afiliado:
                texto_final = texto_final.replace(link, link_afiliado)
                print(f"✅ Link convertido com sucesso!")
            else:
                print(f"⚠️ A conversão retornou vazio para o link: {link}")
                links_convertidos_com_sucesso = False
                break  # Cancela o processo dos demais links desta mensagem
                
        except Exception as e:
            print(f"❌ Erro ao converter o link {link}: {e}")
            links_convertidos_com_sucesso = False
            break

    # TRAVA PRINCIPAL: Se deu BO em qualquer link (app store, captcha), aborta o envio pro canal
    if not links_convertidos_com_sucesso:
        print("🚫 Postagem cancelada: O link falhou na conversão (bloqueio por Captcha, Google Play, etc). O bot não fará esta postagem.")
        return

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
    print("🤖 Iniciando o Bot Promo (Mercado Livre + Shopee + Amazon + AliExpress + Kabum)...")
    await client.start()
    print(f"⚡ Bot online e escutando os {len(CANAIS_ORIGEM)} canais de origem.")
    print("⏳ Aguardando novas postagens em tempo real...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot encerrado pelo usuário com sucesso.")