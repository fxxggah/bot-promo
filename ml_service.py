import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

class MercadoLivreService:
    def __init__(self):
        print("🔌 Configurando serviço do Mercado Livre via Chrome Pessoal...")
        self._lock = asyncio.Lock()

    def renovar_token(self):
        print("🔑 Verificando sessão...")
        return True

    async def expandir_link_curto(self, page, url_curta: str) -> str:
        print(f"🔗 Acessando o link curto: {url_curta}")
        url_final = url_curta
        try:
            await page.goto(url_curta, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            print("🔍 Procurando o botão 'Ir para produto'...")
            botao_ir_produto = "a.poly-component__link--action-link"
            
            if await page.locator(botao_ir_produto).count() > 0:
                print("🖱️ Clicando em 'Ir para produto'...")
                await page.click(botao_ir_produto)
                await page.wait_for_load_state("domcontentloaded", timeout=15000)
                await asyncio.sleep(3)
            
            url_final = page.url
            print(f"✅ URL real do produto capturada: {url_final}")
        except Exception as e:
            print(f"⚠️ Erro ao navegar pelo link curto (mantendo original): {e}")
            url_final = page.url
        
        return url_final

    async def gerar_link_afiliado(self, url_original: str) -> str:
        async with self._lock:
            print(f"🔄 Automatizando a geração de link para: {url_original}")
            link_afiliado = None

            async with async_playwright() as p:
                page = None
                try:
                    browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                    contexts = browser.contexts
                    context = contexts[0] if contexts else await browser.new_context()
                    
                    page = await context.new_page()

                    # PASSO 1: Resolve o link curto
                    url_para_gerar = url_original
                    if "meli.la" in url_original:
                        url_para_gerar = await self.expandir_link_curto(page, url_original)

                    # PASSO 2: Vai para o painel de afiliados
                    url_painel_afiliados = "https://www.mercadolivre.com.br/afiliados/linkbuilder#hub"
                    print(f"🌐 Acessando o painel de afiliados: {url_painel_afiliados}")
                    await page.goto(url_painel_afiliados, timeout=60000)
                    await asyncio.sleep(3)

                    if "login" in page.url or "authorization" in page.url or "sso" in page.url:
                        print("⚠️ Faça login na aba do navegador se necessário...")
                        await asyncio.sleep(15)

                    print("🔍 Inserindo a URL no campo #url-0 via DOM reativo...")
                    input_selector = "#url-0"
                    await page.wait_for_selector(input_selector, state="visible", timeout=20000)

                    # Injeta o valor utilizando o setter nativo do React e dispara os eventos
                    await page.evaluate(f"""
                        const textarea = document.querySelector('{input_selector}');
                        textarea.focus();
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                        nativeInputValueSetter.call(textarea, '{url_para_gerar}');
                        
                        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    """)
                    await asyncio.sleep(1.5)

                    print("🖱️ Verificando e clicando no botão 'Gerar'...")
                    botao_gerar_selector = "button.links-form__button"
                    
                    try:
                        await page.wait_for_function(
                            "selector => !document.querySelector(selector).hasAttribute('disabled')",
                            arg=botao_gerar_selector,
                            timeout=6000
                        )
                    except:
                        print("⚠️ Forçando remoção do atributo disabled do botão...")
                        await page.evaluate(f"document.querySelector('{botao_gerar_selector}').removeAttribute('disabled');")

                    await page.click(botao_gerar_selector)
                    print("✅ Botão 'Gerar' acionado com sucesso!")

                    # Aguarda o painel processar e gerar o link final na tela
                    print("⏳ Aguardando o painel gerar o link...")
                    await asyncio.sleep(5)

                    print("📋 Capturando o link gerado pelo campo ou botão de cópia...")
                    
                    # Tenta ler diretamente de qualquer input/textarea readonly que contenha a estrutura de afiliado do ML
                    for _ in range(3):
                        textareas = await page.locator("textarea, input[readonly]").all()
                        for el in textareas:
                            val = await el.get_attribute("value")
                            if val and ("mercadolivre.com" in val or "meli.la" in val) and val != url_para_gerar and val != url_original:
                                link_afiliado = val
                                break
                        if link_afiliado:
                            break
                        await asyncio.sleep(1)

                    # Se não achou varrendo os inputs, tenta clicar no botão "Copiar" exato que você mandou e ler da área de transferência
                    if not link_afiliado:
                        try:
                            print("🖱️ Tentando clicar no botão 'Copiar' via seletor específico...")
                            botao_copiar = page.locator("span.andes-button__content[data-andes-button-content='true']:has-text('Copiar')")
                            if await botao_copiar.count() > 0:
                                await botao_copiar.first.click()
                                await asyncio.sleep(1)
                                link_afiliado = await page.evaluate("navigator.clipboard.readText()")
                        except Exception as clip_err:
                            print(f"⚠️ Não foi possível ler via clipboard: {clip_err}")

                    print(f"✅ Link gerado final: {link_afiliado}")

                except Exception as e:
                    print(f"❌ Erro ao gerar link no Playwright: {e}")
                    link_afiliado = None
                finally:
                    if page:
                        try:
                            await page.close()
                        except:
                            pass

            return link_afiliado