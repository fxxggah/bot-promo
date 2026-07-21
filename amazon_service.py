import os
import asyncio
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

class AmazonService:
    def __init__(self):
        print("🔌 Configurando serviço da Amazon (Modo Direto por Tag)...")
        self.tag_afiliado = "fxxggah-20"  # Sua StoreID de associado da Amazon
        self._lock = asyncio.Lock()

    async def expandir_link_curto(self, page, url_curta: str) -> str:
        print(f"🔗 Acessando o link curto da Amazon: {url_curta}")
        url_final = url_curta
        try:
            # Bloqueia imagens e fontes para carregar ultra rápido
            await page.route("**/*.{png,jpg,jpeg,gif,svg,css,font,woff}", lambda route: route.abort())
            await page.goto(url_curta, timeout=20000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            url_final = page.url
            print(f"✅ URL real do produto Amazon capturada: {url_final}")
        except Exception as e:
            print(f"⚠️ Erro ao navegar pelo link curto da Amazon: {e}")
            url_final = page.url
        return url_final

    def injetar_tag_na_url(self, url_original: str) -> str:
        """Adiciona ou substitui a tag de afiliado diretamente na URL do produto de forma limpa."""
        try:
            parsed_url = urlparse(url_original)
            query_params = dict(parse_qsl(parsed_url.query))
            
            # Define a sua tag de associado
            query_params['tag'] = self.tag_afiliado
            
            # Reconstrói a URL com a tag embutida
            nova_query = urlencode(query_params)
            url_modificada = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                nova_query,
                parsed_url.fragment
            ))
            return url_modificada
        except Exception as e:
            print(f"⚠️ Erro ao injetar tag na URL: {e}")
            return url_original

    async def gerar_link_afiliado(self, url_original: str) -> str:
        async with self._lock:
            print(f"🔄 Processando link da Amazon para: {url_original}")
            link_afiliado = None

            # Se for link curto (amzn.to), usamos o navegador levemente para descobrir a URL real do produto
            if "amzn.to" in url_original:
                async with async_playwright() as p:
                    page = None
                    try:
                        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                        contexts = browser.contexts
                        context = contexts[0] if contexts else await browser.new_context()
                        page = await context.new_page()

                        url_real = await self.expandir_link_curto(page, url_original)
                        link_afiliado = self.injetar_tag_na_url(url_real)

                    except Exception as e:
                        print(f"❌ Erro ao expandir link curto da Amazon no Playwright: {e}")
                        # Fallback se falhar o browser: apenas anexa a tag na marra no amzn.to
                        link_afiliado = self.injetar_tag_na_url(url_original)
                    finally:
                        if page:
                            try:
                                await page.close()
                            except:
                                pass
            else:
                # Se já for o link completo da Amazon, aplica a tag direto instantaneamente (sem abrir navegador!)
                link_afiliado = self.injetar_tag_na_url(url_original)

            print(f"✅ Link Amazon gerado final: {link_afiliado}")
            return link_afiliado