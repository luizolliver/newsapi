from fastapi import FastAPI
from typing import List, Optional
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import re

app = FastAPI()

def extrair_3_noticias() -> List[dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")

        page.goto("https://www.cnnbrasil.com.br", timeout=60000)

        # Aceita cookies se necessário
        try:
            page.click("button:has-text('Aceitar')", timeout=5000)
        except:
            pass

        page.wait_for_selector("main a[href]", timeout=15000)
        links = page.query_selector_all("main a[href]")

        urls = []
        for link in links:
            href = link.get_attribute("href")
            if not href:
                continue
            full_url = urljoin("https://www.cnnbrasil.com.br", href)
            if (
                full_url.startswith("https://www.cnnbrasil.com.br")
                and full_url.count("/") >= 6
                and full_url not in urls
            ):
                urls.append(full_url)
            if len(urls) >= 3:
                break

        noticias = []

        for url in urls:
            page.goto(url, timeout=60000)

            try:
                page.wait_for_selector("article", timeout=15000)
            except:
                continue

            titulo = page.title()

            paragrafos = page.query_selector_all("article p")
            texto = "\n".join([p.inner_text() for p in paragrafos if p.inner_text().strip()])

            imagens = []
            palavras_bloqueadas = ["logo", "icone", "favicon", "marca", "placeholder"]
            for img in page.query_selector_all("article img"):
                src = img.get_attribute("src")
                if (
                    src
                    and src.startswith("http")
                    and not any(palavra in src.lower() for palavra in palavras_bloqueadas)
                ):
                    match = re.search(r"(.*\.(jpg|jpeg|png|webp|gif))", src, re.IGNORECASE)
                    if match:
                        imagem_limpa = match.group(1)
                        imagens.append(imagem_limpa)

            video_url = None
            iframe = page.query_selector("article iframe")
            if iframe:
                video_url = iframe.get_attribute("src")
            video_tag = page.query_selector("article video")
            if video_tag:
                video_url = video_tag.get_attribute("src")

            noticias.append({
                "url": url,
                "titulo": titulo,
                "texto": texto,
                "imagens": imagens,
                "video": video_url
            })

        browser.close()
        return noticias

@app.get("/noticias")
def get_noticias():
    return extrair_3_noticias()
