from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import base64
from email.message import EmailMessage
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv

# 1. Lê o arquivo .env no início do arquivo
load_dotenv()

def raspar_noticias():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://g1.globo.com/")
        page.wait_for_selector("h2 a")
        html_renderizado = page.content()
        browser.close()

        
        soup = BeautifulSoup(html_renderizado, 'html.parser')
        noticias = soup.select('h2 a')

        corpo_email = []
        for noticia in noticias:
            texto = noticia.text.strip()
            link = noticia.get('href')
            if texto and link:
                corpo_email.append(f"Título: {texto}\nLink: {link}\n")

        return "\n".join(corpo_email)


# Escopo necessário para enviar mensagens
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def enviar_email(conteudo):
    creds = None
    token_path = os.getenv('TOKEN_FILE', 'token.json')
    credentials_path = os.getenv('CREDENTIALS_FILE', 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    try:
            service = build('gmail', 'v1', credentials=creds)

            message = EmailMessage()
            message.set_content(conteudo)
            message['Subject'] = 'Notícias do dia - G1'
            message['To'] = 'ingridrayane1998@gmail.com'
            message['From'] = 'ingridrayane1998@gmail.com'

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'raw': encoded_message}

            send_message = service.users().messages().send(
                userId='me', body=create_message
            ).execute()
            
            print(f'E-mail enviado com sucesso! ID: {send_message["id"]}')

    except HttpError as error:
            print(f'Ocorreu um erro no envio: {error}')


if __name__ == '__main__':
    print("Coletando notícias...")
    texto_noticias = raspar_noticias()
    
    if texto_noticias:
        print("Enviando e-mail...")
        enviar_email(texto_noticias)
    else:
        print("Nenhuma notícia encontrada.")