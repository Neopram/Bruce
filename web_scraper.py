# web_scraper.py

"""
🕷️ Bruce – Web Scraper Cognitivo
Sistema de adquisición inteligente de datos externos para enriquecer análisis de mercado, alertas y aprendizaje simbiótico.
"""

import requests
import logging
from typing import Union, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger("Bruce.WebScraper")
logger.setLevel(logging.INFO)


class WebScraper:
    def __init__(self, mode: str = "mock"):
        self.mode = mode
        logger.info(f"[WebScraper] Inicializado en modo: {self.mode}")

    def fetch_data(self, source: str) -> Union[str, dict, list]:
        """
        🧠 Método principal para obtener datos desde una fuente especificada.
        """
        if self.mode == "mock":
            return f"[🧪 MOCK] Datos simulados desde: {source}"

        elif self.mode == "json":
            return self._fetch_json(source)

        elif self.mode == "html":
            return self._fetch_html(source)

        elif self.mode == "rss":
            return self._fetch_rss(source)

        else:
            logger.warning(f"[WebScraper] Modo desconocido: {self.mode}")
            return f"[❌ Modo inválido] {self.mode}"

    def _fetch_json(self, url: str) -> Union[dict, str]:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            logger.info(f"[JSON] Datos obtenidos de {url}")
            return response.json()
        except Exception as e:
            logger.error(f"[JSON] Error al obtener datos de {url}: {e}")
            return f"[❌ Error JSON] {e}"

    def _fetch_html(self, url: str, selector: Optional[str] = None) -> Union[str, list]:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            logger.info(f"[HTML] Página obtenida: {url}")
            if selector:
                elements = soup.select(selector)
                return [el.get_text(strip=True) for el in elements]
            return soup.title.string.strip() if soup.title else "Sin título encontrado"
        except Exception as e:
            logger.error(f"[HTML] Error al obtener HTML de {url}: {e}")
            return f"[❌ Error HTML] {e}"

    def _fetch_rss(self, url: str) -> Union[list, str]:
        try:
            import feedparser
            feed = feedparser.parse(url)
            logger.info(f"[RSS] Feed obtenido: {url}")
            return [entry.title for entry in feed.entries[:5]]
        except Exception as e:
            logger.error(f"[RSS] Error con el feed {url}: {e}")
            return f"[❌ Error RSS] {e}"


# Uso de prueba (local)
if __name__ == "__main__":
    scraper = WebScraper(mode="html")
    result = scraper.fetch_data("https://www.bbc.com")
    print(result)
