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

                    # Substitua pela URL exata do painel onde você gera os links da KaBuM!
                    url_painel = "https://URL_DO_SEU_PAINEL_DE_AFILIADO_KABUM"
                    print(f"🌐 Acessando o painel da KaBuM!: {url_painel}")
                    await page.goto(url_painel, timeout=60000)
                    await asyncio.sleep(3)

                    # Verifica se precisa de login manual
                    if "login" in page.url:
                        print("⚠️ Faça login na conta de afiliado da KaBuM! na aba do navegador...")
                        await asyncio.sleep(15)

                    print("🔍 Inserindo a URL no campo gerador...")
                    # ATENÇÃO: Troque 'seletor_do_input' pelo CSS real da caixa de texto do painel
                    input_selector = "seletor_do_input" 
                    await page.wait_for_selector(input_selector, state="visible", timeout=20000)

                    # Injeta o link
                    await page.evaluate(f"""
                        const input = document.querySelector('{input_selector}');
                        input.focus();
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                        nativeInputValueSetter.call(input, '{url_original}');
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    """)
                    await asyncio.sleep(1.5)

                    print("🖱️ Clicando no botão de gerar link...")
                    # ATENÇÃO: Troque 'seletor_do_botao_gerar' pelo CSS real do botão
                    botao_gerar = page.locator("seletor_do_botao_gerar")
                    await botao_gerar.first.click()

                    print("⏳ Aguardando o painel gerar o link...")
                    await asyncio.sleep(3)

                    print("📋 Capturando o link gerado...")
                    # ATENÇÃO: Troque 'seletor_do_input_resultado' pelo CSS real de onde o link final aparece
                    resultado_selector = "seletor_do_input_resultado"
                    elemento_resultado = await page.locator(resultado_selector).first
                    link_afiliado = await elemento_resultado.get_attribute("value")

                    print(f"✅ Link KaBuM! gerado final: {link_afiliado}")

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