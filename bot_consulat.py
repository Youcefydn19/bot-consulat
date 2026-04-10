"""
Bot RDV Consulat d'Espagne - Oran
Conçu pour GitHub Actions (exécution unique, pas de boucle)
"""

import asyncio
import os
import requests
from datetime import datetime
from playwright.async_api import async_playwright

# Config depuis les secrets GitHub
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID        = os.environ["CHAT_ID"]
URL_CONSULAT   = "https://www.citaconsular.es/es/hosteds/widgetdefault/2da8fb6f4ac7361929959598a1e5b1e45"

def envoyer_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }, timeout=10)
        print("✅ Telegram envoyé" if r.status_code == 200 else f"❌ Erreur : {r.text}")
    except Exception as e:
        print(f"❌ Telegram inaccessible : {e}")

async def verifier() -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(30000)
        try:
            print("🌐 Chargement du site...")
            await page.goto(URL_CONSULAT, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            print("🖱️ Clic sur Continuar...")
            for selecteur in [
                "button:has-text('Continuar')",
                "a:has-text('Continuar')",
                "button:has-text('Continue')",
                "input[type='submit']",
            ]:
                try:
                    elem = page.locator(selecteur).first
                    if await elem.is_visible():
                        await elem.click()
                        print(f"✅ Cliqué")
                        break
                except:
                    continue

            await page.wait_for_timeout(4000)
            await page.wait_for_load_state("networkidle")

            contenu = (await page.inner_text("body")).lower()
            print(f"📄 {len(contenu)} caractères lus")

            for mot in ["no hay citas disponibles", "no existen citas", "no disponible", "sin citas", "agotado"]:
                if mot in contenu:
                    return {"statut": "indisponible", "details": mot}

            for mot in ["seleccione", "seleccionar fecha", "fecha disponible", "hora disponible", "calendario", "elige un d"]:
                if mot in contenu:
                    return {"statut": "disponible", "details": mot}

            return {"statut": "inconnu", "details": contenu[:300]}

        except Exception as e:
            return {"statut": "erreur", "details": str(e)}
        finally:
            await browser.close()

async def main():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"\n🔍 Vérification — {now}\n")

    resultat = await verifier()
    statut = resultat["statut"]
    print(f"📊 Statut : {statut}")

    if statut == "disponible":
        envoyer_telegram(
            f"🚨🚨 <b>RDV DISPONIBLE !</b> 🚨🚨\n\n"
            f"Des créneaux sont disponibles au Consulat d'Espagne à Oran !\n\n"
            f"👉 <a href='{URL_CONSULAT}'>Réserver maintenant !</a>\n\n"
            f"⚡ Fais vite, ça part très vite !\n"
            f"🕐 {now}"
        )
    elif statut == "inconnu":
        envoyer_telegram(
            f"⚠️ <b>Page modifiée !</b>\n"
            f"Vérifie manuellement :\n"
            f"👉 <a href='{URL_CONSULAT}'>Ouvrir le site</a>\n"
            f"🕐 {now}"
        )
    elif statut == "erreur":
        print(f"⚠️ Erreur : {resultat['details']}")
    else:
        print("🔴 Pas de RDV disponible.")

if __name__ == "__main__":
    asyncio.run(main())
