import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

class KabumService:
    def __init__(self):
        print("🔌 Configurando serviço da KaBuM! via Chrome Pessoal...")
        self._lock = asyncio.Lock()

    async def gerar_link_afiliado(self, url_original: str) -> str:
        async with self._lock:
            print(f"🔄 Automatizando link de afiliado KaBuM para: {url_original}")
            link_afiliado = None

            async with async_playwright() as p:
                page = None
                try:
                    browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                    contexts = browser.contexts
                    context = contexts[0] if contexts else await browser.new_context()
                    
                    page = await context.new_page()

                    # Substitua pela URL exata do painel da Awin
                    url_painel = "https://ui.awin.com/link-builder/br/awin/publisher/3002719"
                    print(f"🌐 Acessando o painel da Awin (KaBuM!): {url_painel}")
                    await page.goto(url_painel, timeout=60000)
                    await asyncio.sleep(3)

                    # Verifica se precisa de login manual
                    if "login" in page.url:
                        print("⚠️ Faça login na conta da Awin na aba do navegador...")
                        await asyncio.sleep(15)

                    print("🔍 Procurando o campo 'Destination URL' pelos seletores exatos...")
                    # Utiliza o atributo name="destinationUrl" fornecido por você (muito mais seguro)
                    campo_destino = page.locator('input[name="destinationUrl"]')
                    await campo_destino.wait_for(state="visible", timeout=20000)
                    
                    # Preenche o link original da oferta
                    await campo_destino.fill(url_original)
                    await asyncio.sleep(1)

                    print("🖱️ Clicando no botão 'Generate link'...")
                    # Localiza o botão laranja exatamente pelo nome que está escrito nele
                    botao_gerar = page.get_by_role("button", name="Generate link")
                    await botao_gerar.click()

                    print("⏳ Aguardando o painel gerar o link na seção 'Seu Deeplink'...")
                    await asyncio.sleep(3) # Tempo para a Awin processar

                    print("📋 Capturando o link gerado...")
                    # Na Awin, o link gerado costuma aparecer em um input ou caixa de texto que permite cópia
                    # Vamos tentar pegar o valor do primeiro input que aparece na tela após clicar em gerar
                    
                    link_afiliado = None
                    inputs = await page.locator("input[type='text']").all()
                    if inputs:
                        # Pega o valor do último input de texto da página (geralmente é o resultado da Awin)
                        link_afiliado = await inputs[-1].get_attribute("value")
                    
                    # Fallback de segurança: se o método acima falhar, tenta pegar do clipboard se houver botão de copiar
                    if not link_afiliado or link_afiliado == url_original:
                        try:
                            botao_copiar = page.locator("button:has-text('Copiar'), button:has-text('Copy')")
                            if await botao_copiar.count() > 0:
                                await botao_copiar.first.click()
                                await asyncio.sleep(1)
                                link_afiliado = await page.evaluate("navigator.clipboard.readText()")
                        except Exception:
                            pass

                    print(f"✅ Link KaBuM! (Awin) gerado final: {link_afiliado}")

                except Exception as e:
                    print(f"❌ Erro no Playwright para KaBuM!: {e}")
                    link_afiliado = None
                finally:
                    if page:
                        try:
                            await page.close()
                        except:
                            pass

            return link_afiliado