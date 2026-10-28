import asyncio
import json
import os
import random
import subprocess
import sys
import textwrap
from pathlib import Path

from playwright.async_api import async_playwright

YOUTUBE_STATE = os.getenv("YOUTUBE_STATE", "")
TIKTOK_STATE = os.getenv("TIKTOK_STATE", "")
LINK_AFILIADO = os.getenv("LINK_AFILIADO", "")

HISTORIAL = Path("historial_videos.txt")
VIDEO_OUT = "video_final.mp4"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# ---------------------------------------------------------------
# GUIONES: sustituye por los tuyos
# ---------------------------------------------------------------
GUIONES = [
    {"titulo": "Por qué postergas las cosas",
     "texto": "Postergar no es pereza.\nEs tu cerebro evitando una emoción incómoda.\nEmpieza con 2 minutos y el resto fluye."},
    {"titulo": "El sesgo de confirmación",
     "texto": "Tu mente busca pruebas de lo que ya cree.\nPregúntate: ¿qué evidencia contradice mi idea?\nAsí piensas con más claridad."},
    {"titulo": "Por qué te comparas con otros",
     "texto": "Comparas tu detrás de cámaras\ncon el mejor momento de los demás.\nEs una trampa mental, no la realidad."},
    {"titulo": "El efecto Zeigarnik",
     "texto": "Tu cerebro recuerda más lo inacabado.\nPor eso las tareas pendientes no te dejan dormir.\nAnótalas y tu mente se calma."},
]


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------
# Historial y elección de guion
# ---------------------------------------------------------------
def elegir_guion():
    usados = set()
    if HISTORIAL.exists():
        usados = {l.strip() for l in HISTORIAL.read_text(encoding="utf-8").splitlines() if l.strip()}
    libres = [g for g in GUIONES if g["titulo"] not in usados]
    if not libres:
        log("♻️ Todos los guiones usados; reiniciando historial.")
        HISTORIAL.write_text("", encoding="utf-8")
        libres = GUIONES
    return random.choice(libres)


def marcar_usado(titulo):
    with HISTORIAL.open("a", encoding="utf-8") as f:
        f.write(titulo + "\n")


# ---------------------------------------------------------------
# Render del vídeo con ffmpeg (vertical 1080x1920, 20 s)
# ---------------------------------------------------------------
def renderizar_video(guion, salida=VIDEO_OUT, duracion=20):
    lineas = []
    for parrafo in guion["texto"].split("\n"):
        lineas.extend(textwrap.wrap(parrafo, width=26) or [""])
        lineas.append("")
    Path("texto_tmp.txt").write_text("\n".join(lineas), encoding="utf-8")

    fuente = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    filtro = (
        f"drawtext=fontfile={fuente}:textfile=texto_tmp.txt:fontcolor=white:"
        "fontsize=64:line_spacing=18:x=(w-text_w)/2:y=(h-text_h)/2:"
        "box=1:boxcolor=black@0.35:boxborderw=30"
    )
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=0x1b1f3b:s=1080x1920:d={duracion}:r=30",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", filtro,
        "-t", str(duracion),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-c:a", "aac", "-shortest",
        salida,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log(r.stderr[-2000:])
        raise RuntimeError("ffmpeg falló al renderizar el vídeo")
    log(f"🎬 Vídeo renderizado: {salida} ({Path(salida).stat().st_size/1024:.0f} KB)")
    return salida


# ---------------------------------------------------------------
# Utilidades de estado (cookies) — con normalización de sameSite
# ---------------------------------------------------------------
def _normalizar_cookie(c):
    """Convierte una cookie exportada por una extensión al formato de Playwright."""
    mapa_same_site = {
        "no_restriction": "None",
        "none": "None",
        "unspecified": "Lax",
        "lax": "Lax",
        "strict": "Strict",
    }
    ss = str(c.get("sameSite", "")).strip().lower()
    same_site = mapa_same_site.get(ss, "Lax")

    cookie = {
        "name": c["name"],
        "value": c["value"],
        "domain": c["domain"],
        "path": c.get("path", "/"),
        "httpOnly": bool(c.get("httpOnly", False)),
        "secure": bool(c.get("secure", False)),
        "sameSite": same_site,
    }

    # Playwright exige secure=True cuando sameSite=None
    if same_site == "None":
        cookie["secure"] = True

    exp = c.get("expirationDate", c.get("expires"))
    if isinstance(exp, (int, float)) and exp > 0:
        cookie["expires"] = float(exp)
    else:
        cookie["expires"] = -1  # cookie de sesión

    return cookie


def preparar_estado(raw, nombre_archivo):
    data = json.loads(raw)

    # Puede venir como lista de cookies o como storage_state completo
    if isinstance(data, list):
        data = {"cookies": data, "origins": []}

    data["cookies"] = [_normalizar_cookie(c) for c in data.get("cookies", [])]
    data.setdefault("origins", [])

    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return nombre_archivo


# ---------------------------------------------------------------
# YouTube Studio
# ---------------------------------------------------------------
async def subir_youtube(page, video_path, titulo, descripcion):
    await page.goto("https://studio.youtube.com", wait_until="domcontentloaded")
    await page.wait_for_timeout(5000)
    if "accounts.google.com" in page.url:
        raise RuntimeError("Cookies de YouTube caducadas o rechazadas (redirige a login)")

    await page.click("#create-icon", timeout=30000)
    await page.click("#text-item-0", timeout=30000)
    await page.wait_for_selector("input[type='file']", state="attached", timeout=30000)
    await page.set_input_files("input[type='file']", video_path)

    await page.wait_for_selector("#title-textarea #textbox", timeout=60000)
    caja_titulo = page.locator("#title-textarea #textbox")
    await caja_titulo.click()
    await page.keyboard.press("Control+A")
    await page.keyboard.type(titulo[:100])

    caja_desc = page.locator("#description-textarea #textbox")
    await caja_desc.click()
    await page.keyboard.type(descripcion)

    await page.locator("[name='VIDEO_MADE_FOR_KIDS_NOT_MADE_FOR_KIDS']").click()

    for _ in range(3):
        await page.click("#next-button")
        await page.wait_for_timeout(1500)

    await page.locator("[name='PUBLIC']").click()

    # Esperar a que termine la subida antes de publicar
    for _ in range(60):
        estado = await page.locator("ytcp-video-upload-progress").inner_text()
        if any(s in estado for s in (
            "Subida completa", "Upload complete", "Procesando",
            "Processing", "Comprobaciones", "Checks",
        )):
            break
        await page.wait_for_timeout(3000)

    await page.click("#done-button", timeout=30000)
    await page.wait_for_timeout(8000)
    log("✅ YouTube: publicado")


# ---------------------------------------------------------------
# TikTok Studio
# ---------------------------------------------------------------
async def subir_tiktok(page, video_path, titulo):
    await page.goto("https://www.tiktok.com/tiktokstudio/upload?from=webapp",
                    wait_until="domcontentloaded")
    await page.wait_for_timeout(6000)
    if "login" in page.url:
        raise RuntimeError("Cookies de TikTok caducadas (redirige a login)")

    # El uploader puede estar en un iframe o en la página principal
    contexto = page
    for fr in page.frames:
        if "upload" in fr.url and await fr.locator("input[type='file']").count():
            contexto = fr
            break

    await contexto.locator("input[type='file']").first.set_input_files(video_path)

    editor = contexto.locator("div[contenteditable='true']").first
    await editor.wait_for(timeout=90000)
    await editor.click()
    await page.keyboard.press("Control+A")
    await page.keyboard.type(titulo)

    # Esperar a que el botón de publicar esté activo
    boton = contexto.locator("button:has-text('Publicar'), button:has-text('Post')").last
    for _ in range(60):
        if await boton.is_enabled():
            break
        await page.wait_for_timeout(3000)
    await boton.click()
    await page.wait_for_timeout(10000)

    # Confirmación opcional ("Publicar ahora")
    extra = page.locator("button:has-text('Publicar ahora'), button:has-text('Post now')")
    if await extra.count():
        await extra.first.click()
        await page.wait_for_timeout(8000)
    log("✅ TikTok: publicado")


# ---------------------------------------------------------------
# Despachador
# ---------------------------------------------------------------
async def despachador_redes(video_path, titulo_yt, link):
    descripcion_yt = (f"Descubre cómo funciona tu mente.\n"
                      f"El libro recomendado (gratis el primer mes) aquí: {link}\n"
                      f"#psicologia #desarrollopersonal #shorts")
    titulo_tk = f"{titulo_yt} #psicologia #desarrollopersonal"
    exitos, errores = [], []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )

        redes = [
            ("youtube", YOUTUBE_STATE, "yt_state_tmp.json",
             lambda pg: subir_youtube(pg, video_path, titulo_yt, descripcion_yt)),
            ("tiktok", TIKTOK_STATE, "tk_state_tmp.json",
             lambda pg: subir_tiktok(pg, video_path, titulo_tk)),
        ]

        for nombre, estado, tmp, funcion in redes:
            if not estado or len(estado.strip()) <= 5:
                log(f"ℹ️ {nombre.upper()}_STATE vacío; salto {nombre}.")
                errores.append(f"{nombre}: secreto vacío")
                continue
            ctx = None
            try:
                preparar_estado(estado, tmp)
                ctx = await browser.new_context(
                    storage_state=tmp, user_agent=UA, locale="es-ES",
                    viewport={"width": 1366, "height": 900},
                )
                page = await ctx.new_page()
                try:
                    await funcion(page)
                    exitos.append(nombre)
                except Exception as e:
                    log(f"❌ Error subiendo a {nombre}: {e}")
                    errores.append(f"{nombre}: {e}")
                    try:
                        await page.screenshot(path=f"error_{nombre}.png", full_page=True)
                    except Exception:
                        pass
            except Exception as e:
                log(f"❌ Error preparando {nombre}: {e}")
                errores.append(f"{nombre}: {e}")
            finally:
                if ctx:
                    await ctx.close()
                if os.path.exists(tmp):
                    os.remove(tmp)

        await browser.close()

    return exitos, errores


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
async def main():
    log("🚀 Iniciando bot PsicoVideos")
    guion = elegir_guion()
    log(f"📝 Guion elegido: {guion['titulo']}")

    video = renderizar_video(guion)
    exitos, errores = await despachador_redes(video, guion["titulo"], LINK_AFILIADO)

    log(f"Publicado en: {exitos or 'ninguna red'}")
    if errores:
        log("Errores: " + " | ".join(errores))

    if not exitos:
        log("💥 No se publicó en ninguna red.")
        sys.exit(1)

    marcar_usado(guion["titulo"])  # solo se marca si al menos una red funcionó


if __name__ == "__main__":
    asyncio.run(main())
