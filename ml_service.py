import os
import requests
from dotenv import load_dotenv

load_dotenv()

class MercadoLivreService:
    def __init__(self):
        self.client_id = os.getenv("ML_CLIENT_ID")
        self.client_secret = os.getenv("ML_CLIENT_SECRET")
        self.refresh_token = os.getenv("ML_REFRESH_TOKEN")
        self.access_token = None

    def renovar_token(self):
        url = "https://api.mercadolibre.com/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(url, data=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            # Se a API devolver um novo refresh_token, atualizamos o estado da aplicação
            if data.get("refresh_token"):
                self.refresh_token = data.get("refresh_token")
            print("🔑 Access Token atualizado com sucesso!")
            return self.access_token
        else:
            raise Exception(f"Erro ao renovar token: {response.text}")