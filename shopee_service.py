import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

class ShopeeService:
    def __init__(self):
        print("🔌 Configurando serviço da Shopee via Chrome Pessoal...")
        self._lock = asyncio.Lock()

    async def expandir_link_curto(self, page, url_curta: str) -> str:
        print(f"🔗 Acessando o link curto da Shopee: {url_curta}")
        url_final = url_curta
        try:
            await page.goto(url_curta, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            url_final = page.url
            
            # TRAVA DE SEGURANÇA: Verifica se a Shopee bloqueou com Captcha ou Tela de Login
            if "captcha" in url_final.lower() or "login" in url_final.lower() or "verify" in url_final.lower():
                print(f"⚠️ Bloqueio detectado (Captcha/Login) ao abrir link curto: {url_final}")
                return None
                
            print(f"✅ URL real do produto Shopee capturada: {url_final}")
        except Exception as e:
            print(f"⚠️ Erro ao navegar pelo link curto da Shopee: {e}")
            return None
            
        return url_final

    async def gerar_link_afiliado(self, url_original: str) -> str:
        async with self._lock:
            print(f"🔄 Automatizando link de afiliado Shopee para: {url_original}")
            link_afiliado = None

            async with async_playwright() as p:
                page = None
                try:
                    browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                    contexts = browser.contexts
                    context = contexts[0] if contexts else await browser.new_context()
                    
                    page = await context.new_page()

                    # 1. Resolve links curtos (shope.ee / s.shopee.com.br)
                    url_para_gerar = url_original
                    if "shope.ee" in url_original or "s.shopee.com.br" in url_original:
                        url_para_gerar = await self.expandir_link_curto(page, url_original)
                        
                        # Se o expansor retornou None (caiu no Captcha), aborta
                        if not url_para_gerar:
                            print("❌ Geração abortada: Link barrado pelo Captcha da Shopee.")
                            return None

                    # 2. Vai para a página exata de link personalizado da Shopee
                    url_painel = "https://affiliate.shopee.com.br/offer/custom_link"
                    print(f"🌐 Acessando a página de link personalizado: {url_painel}")
                    await page.goto(url_painel, timeout=60000)
                    await asyncio.sleep(3)

                    if "login" in page.url or "seller" in page.url:
                        print("⚠️ Faça login na conta de afiliado da Shopee na aba do navegador...")
                        await asyncio.sleep(15)

                    print("🔍 Inserindo a URL no textarea da Shopee...")
                    textarea_selector = "textarea.ant-input"
                    await page.wait_for_selector(textarea_selector, state="visible", timeout=20000)

                    # Injeta o link utilizando o setter nativo
                    await page.evaluate(f"""
                        const textarea = document.querySelector('{textarea_selector}');
                        textarea.focus();
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                        nativeInputValueSetter.call(textarea, '{url_para_gerar}');
                        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    """)
                    await asyncio.sleep(1.5)

                    print("🖱️ Clicando no botão 'Obter link'...")
                    botao_obter = page.locator("button[type='submit'].ant-btn-primary:has-text('Obter link')")
                    await page.wait_for_selector("button[type='submit'].ant-btn-primary", state="visible", timeout=10000)
                    await botao_obter.first.click()
                    print("✅ Botão 'Obter link' acionado com sucesso!")

                    print("⏳ Aguardando o painel gerar o link...")
                    await asyncio.sleep(3)

                    print("📋 Clicando no botão 'Copiar Link' e capturando...")
                    try:
                        botao_copiar = page.locator("button.ant-btn-primary:has-text('Copiar Link')")
                        if await botao_copiar.count() > 0:
                            await botao_copiar.first.click()
                            await asyncio.sleep(1)
                            link_afiliado = await page.evaluate("navigator.clipboard.readText()")
                    except Exception as clip_err:
                        print(f"⚠️ Erro ao capturar via clipboard do botão Copiar: {clip_err}")

                    # Fallback caso o clipboard falhe
                    if not link_afiliado or ("shope.ee" not in link_afiliado and "s.shopee.com.br" not in link_afiliado):
                        elementos = await page.locator("input[readonly], textarea[readonly]").all()
                        for el in elementos:
                            val = await el.get_attribute("value")
                            if val and ("shope.ee" in val or "s.shopee.com.br" in val) and val != url_para_gerar:
                                link_afiliado = val
                                break

                    print(f"✅ Link Shopee gerado final: {link_afiliado}")

                except Exception as e:
                    print(f"❌ Erro no Playwright para Shopee: {e}")
                    link_afiliado = None
                finally:
                    if page:
                        try:
                            await page.close()
                        except:
                            pass

            return link_afiliado