import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

class AliExpressService:
    def __init__(self):
        print("🔌 Configurando serviço da AliExpress via Chrome Pessoal...")
        self._lock = asyncio.Lock()

    async def expandir_link_curto(self, page, url_curta: str) -> str:
        print(f"🔗 Acessando o link curto da AliExpress: {url_curta}")
        url_final = url_curta
        try:
            await page.goto(url_curta, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            url_final = page.url
            print(f"✅ URL real do produto AliExpress capturada: {url_final}")
        except Exception as e:
            print(f"⚠️ Erro ao navegar pelo link curto da AliExpress: {e}")
            url_final = page.url
        return url_final

    async def gerar_link_afiliado(self, url_original: str) -> str:
        async with self._lock:
            print(f"🔄 Automatizando link de afiliado AliExpress para: {url_original}")
            link_afiliado = None

            async with async_playwright() as p:
                page = None
                try:
                    browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                    contexts = browser.contexts
                    context = contexts[0] if contexts else await browser.new_context()
                    
                    page = await context.new_page()

                    # 1. Resolve links curtos (ex: a.aliexpress.com) se houverem
                    url_para_gerar = url_original
                    if "a.aliexpress.com" in url_original or "s.click.aliexpress.com" in url_original:
                        url_para_gerar = await self.expandir_link_curto(page, url_original)

                    # 2. Vai para o Portal de Afiliados da AliExpress (Gerador de Links)
                    url_painel = "https://portals.aliexpress.com/affiliate/center/tools/links/linkGenerator.htm"
                    print(f"🌐 Acessando o painel de Afiliados AliExpress: {url_painel}")
                    await page.goto(url_painel, timeout=60000)
                    await asyncio.sleep(3)

                    # Verifica se precisa de login
                    if "login" in page.url or "signin" in page.url or "passport" in page.url:
                        print("⚠️ Faça login na sua conta de Afiliados da AliExpress na aba do navegador...")
                        await asyncio.sleep(15)

                    print("🔍 Inserindo a URL do produto no painel da AliExpress...")
                    # Seletor padrão da caixa de inserção de link no Portal de Afiliados da AliExpress
                    input_selector = "input[placeholder*='Link'], input[placeholder*='link'], textarea[placeholder*='link'], .search-box input"
                    
                    await page.wait_for_selector(input_selector, state="visible", timeout=20000)

                    # Preenche o input utilizando injeção reativa limpa
                    await page.evaluate(f"""
                        const input = document.querySelector("{input_selector}");
                        if (input) {{
                            input.focus();
                            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                            nativeSetter.call(input, "{url_para_gerar}");
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    """)
                    await asyncio.sleep(1.5)

                    # Clica no botão de gerar/copiar link
                    print("🖱️ Acionando a geração do link...")
                    botao_gerar = page.locator("button:has-text('Generate'), button:has-text('Copiar'), button:has-text('Obter'), .generate-btn, button[type='button']")
                    if await botao_gerar.count() > 0:
                        # Clica no botão mais provável de geração
                        await botao_gerar.first.click()
                        await asyncio.sleep(3)

                    print("📋 Capturando o link gerado da AliExpress...")
                    # Extrai o link de afiliado gerado (geralmente links s.click.aliexpress.com ou afiliados)
                    link_afiliado = await page.evaluate("""
                        () => {
                            const inputs = Array.from(document.querySelectorAll('input[type="text"], textarea'));
                            for (let el of inputs) {
                                if (el.value && (el.value.includes('s.click.aliexpress.com') || el.value.includes('aff_fcid'))) {
                                    return el.value;
                                }
                            }
                            const links = Array.from(document.querySelectorAll('a'));
                            for (let a of links) {
                                if (a.href && (a.href.includes('s.click.aliexpress.com') || a.href.includes('aff_fcid'))) {
                                    return a.href;
                                }
                            }
                            return null;
                        }
                    """)

                    print(f"✅ Link AliExpress gerado final: {link_afiliado}")

                except Exception as e:
                    print(f"❌ Erro no Playwright para AliExpress: {e}")
                    link_afiliado = None
                finally:
                    if page:
                        try:
                            await page.close()
                        except:
                            pass

            return link_afiliado