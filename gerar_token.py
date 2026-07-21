import os
import urllib.parse
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = "8863245897728139"
# Substitua com a Secret Key que está no seu painel do DevCenter
CLIENT_SECRET = input("Digite seu Client Secret (Secret Key) do ML: ").strip()
REDIRECT_URI = "https://httpbin.org/get"

# 1. Monta a URL perfeita
params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI
}
url_auth = f"https://auth.mercadolivre.com.br/authorization?{urllib.parse.urlencode(params)}"

print("\n" + "="*60)
print("1️⃣ COPIE A URL ABAIXO E ABRA NO SEU NAVEGADOR:")
print("="*60)
print(url_auth)
print("="*60 + "\n")

# 2. Pede o código TG
code_url = input("2️⃣ Depois de clicar em Autorizar, cole a URL INTEIRA da página onde você foi parar aqui:\n> ").strip()

# Extrai o código TG da URL
if "code=" in code_url:
    code = code_url.split("code=")[1].split("&")[0]
else:
    code = code_url

# 3. Faz a requisição HTTP para trocar o código pelo Refresh Token
url_token = "https://api.mercadolibre.com/oauth/token"
payload = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": code,
    "redirect_uri": REDIRECT_URI
}

res = requests.post(url_token, data=payload)

if res.status_code == 200:
    dados = res.json()
    print("\n✅ DEU CERTO! SEUS TOKENS FORAM GERADOS:")
    print(f"\nML_REFRESH_TOKEN={dados.get('refresh_token')}")
    print("\nGuarde esse Refresh Token no seu arquivo .env!")
else:
    print(f"\n❌ Erro ao gerar token ({res.status_code}): {res.text}")