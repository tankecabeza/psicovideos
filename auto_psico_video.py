import os
import sys
import json
import wave
import time
import random
import asyncio
import urllib.parse
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
from playwright.async_api import async_playwright

# Parche Pillow para MoviePy
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

# ==============================================================================
# CONFIGURACIÓN DEL ROBOT
# ==============================================================================
YOUTUBE_STATE = os.getenv("YOUTUBE_STATE", "")
TIKTOK_STATE = os.getenv("TIKTOK_STATE", "")
LINK_AFILIADO = os.getenv("LINK_AFILIADO", "https://amzn.to/tu-enlace")
ARCHIVO_HISTORIAL = "historial_videos.txt"

PACK_GUIONES = {
    "1. Trucos contra manipuladores": {
        "cabecera": "3 TRUCOS DE PSICOLOGÍA OSCURA",
        "titulo_yt": "3 Trucos de Psicología Oscura para Dominar Cualquier Situación #Shorts",
        "libro_afiliado": "Las 48 Leyes del Poder",
        "escenas": [
            {"texto": "Si alguien te falta al respeto en público, haz esto inmediatamente.", "prompt": "mysterious man in dark room cinematic 8k"},
            {"texto": "Uno: mírale a los ojos en silencio durante cuatro segundos. Destruirás su seguridad.", "prompt": "intense eyes in shadow dark aesthetic 8k"},
            {"texto": "Dos: pregúntale con voz calmada si está bien. Quedará en evidencia frente a todos.", "prompt": "two shadowy figures talking dark room 8k"},
            {"texto": "Tienes el libro prohibido de persuasión en el primer comentario fijado.", "prompt": "leather gold book on dark desk candlelight"}
        ]
    },
    "2. Detectar mentiras": {
        "cabecera": "TÉCNICAS DEL FBI PARA MENTIRAS",
        "titulo_yt": "Cómo Saber si te Mienten en 5 Segundos según el FBI #psicologia",
        "libro_afiliado": "El Cuerpo Habla (Joe Navarro)",
        "escenas": [
            {"texto": "Así descubres a un mentiroso en menos de cinco segundos.", "prompt": "interrogation room dark lamp cinematic"},
            {"texto": "Si repite tu pregunta antes de responder, está ganando tiempo para inventar.", "prompt": "nervous man sweating shadow 8k"},
            {"texto": "Pídele que cuente la historia hacia atrás. Los mentirosos siempre se bloquean.", "prompt": "chess piece falling slow motion dark 8k"},
            {"texto": "Descubre el manual oficial del exagente del FBI en el comentario fijado.", "prompt": "classified dossier dark leather book desk"}
        ]
    },
    "3. El Efecto Escasez": {
        "cabecera": "LA LEY DEL DESAPEGO PSICOLÓGICO",
        "titulo_yt": "Por Qué Cuanto Más Das, Menos Te Valoran #psicologia #shorts",
        "libro_afiliado": "Influencia: La Psicología de la Persuasión",
        "escenas": [
            {"texto": "Deja de estar siempre disponible para todo el mundo.", "prompt": "lone man walking away foggy street night 8k"},
            {"texto": "El cerebro humano desprecia lo gratuito y se obsesiona con lo escaso.", "prompt": "gold pocket watch on dark velvet luxury"},
            {"texto": "Retira tu atención en silencio y verás cómo empiezan a buscarte.", "prompt": "silhouette confident man tall skyscraper window"},
            {"texto": "Aprende a dominar las leyes de la persuasión en el enlace del comentario fijado.", "prompt": "minimalist dark book golden light 8k"}
        ]
    }
}

# ==============================================================================
# LÓGICA DE PRODUCCIÓN AUDIOVISUAL
# ==============================================================================
def cargar_historial():
    if not os.path.exists(ARCHIVO_HISTORIAL):
        return []
    with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def guardar_historial(tema):
    with open(ARCHIVO_HISTORIAL, "a", encoding="utf-8") as f:
        f.write(f"{tema}\n")

def crear_musica_fondo(filepath: str, duracion: float, sr: int = 44100):
    t = np.linspace(0, duracion, int(sr * duracion), False)
    sub = np.sin(2 * np.pi * 55.0 * t) * 0.50
    mid = np.sin(2 * np.pi * 82.41 * t) * 0.25
    high = np.sin(2 * np.pi * 110.0 * t) * 0.15
    pulso = 0.65 + 0.35 * np.sin(2 * np.pi * 0.25 * t)
    audio_pcm = (np.clip((sub + mid + high) * pulso * 0.28, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_pcm.tobytes())

async def sintetizar_voz(texto: str, voz: str, ruta_mp3: str):
    comunicador = edge_tts.Communicate(texto, voz, rate="+10%")
    await comunicador.save(ruta_mp3)

def descargar_fondo_ia(prompt: str, ruta_img: str, seed: int):
    prm = urllib.parse.quote(f"{prompt}, vertical 9:16, dark moody cinematography, no text")
    url = f"https://image.pollinations.ai/prompt/{prm}?width=1080&height=1920&seed={seed}&nologo=true"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(ruta_img, "wb") as f:
            f.write(r.content)
    except Exception:
        Image.new("RGB", (1080, 1920), (14, 18, 28)).save(ruta_img)

def quemar_textos(ruta_in, cabecera, texto, num_escena, total_escenas, ruta_out):
    img = Image.open(ruta_in).convert("RGBA").resize((1080, 1920), Image.LANCZOS)
    capa = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    dr_capa = ImageDraw.Draw(capa)
    dr_capa.rectangle([(0, 0), (1080, 230)], fill=(0, 0, 0, 150))
    dr_capa.rectangle([(0, 1120), (1080, 1680)], fill=(0, 0, 0, 125))
    img = Image.alpha_composite(img, capa).convert("RGB")
    draw = ImageDraw.Draw(img)

    f_cab = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
    f_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)

    bbox_c = draw.textbbox((0, 0), cabecera, font=f_cab)
    draw.text(((1080 - (bbox_c[2]-bbox_c[0])) / 2, 95), cabecera, font=f_cab, fill="#FFFFFF", stroke_width=4, stroke_fill="#000000")

    palabras = texto.upper().split()
    lineas, actual = [], []
    for p in palabras:
        actual.append(p)
        if len(" ".join(actual)) > 17:
            if len(actual) > 1: actual.pop()
            lineas.append(" ".join(actual))
            actual = [p] if len(actual) > 1 else []
    if actual: lineas.append(" ".join(actual))

    y = 1210
    mitad = max(1, len(lineas) // 2)
    for idx, lin in enumerate(lineas):
        color = "#00FF88" if num_escena == total_escenas - 1 and idx >= mitad else ("#FFE600" if (num_escena == total_escenas - 1 or idx >= mitad) else "#FFFFFF")
        bbox = draw.textbbox((0, 0), lin, font=f_sub)
        draw.text(((1080 - (bbox[2]-bbox[0])) / 2, y), lin, font=f_sub, fill=color, stroke_width=6, stroke_fill="#000000")
        y += (bbox[3]-bbox[1]) + 26
    img.save(ruta_out, quality=95)

def producir_video(clave, datos):
    print(f"🎬 Iniciando producción: {clave}")
    carpeta = "render_tmp"
    os.makedirs(carpeta, exist_ok=True)
    clips = []
    
    for i, esc in enumerate(datos["escenas"]):
        r_mp3 = os.path.join(carpeta, f"voz_{i}.mp3")
        r_raw = os.path.join(carpeta, f"raw_{i}.jpg")
        r_sub = os.path.join(carpeta, f"escena_{i}.jpg")
        
        asyncio.run(sintetizar_voz(esc["texto"], "es-ES-AlvaroNeural", r_mp3))
        audio = AudioFileClip(r_mp3)
        descargar_fondo_ia(esc["prompt"], r_raw, 300 + i*19)
        quemar_textos(r_raw, datos["cabecera"], esc["texto"], i, len(datos["escenas"]), r_sub)
        
        clips.append(ImageClip(r_sub).set_duration(audio.duration + 0.3).resize(lambda t: 1.0 + 0.028*t).set_position(("center", "center")).set_audio(audio))

    final = concatenate_videoclips(clips, method="compose")
    r_bgm = os.path.join(carpeta, "bgm.wav")
    crear_musica_fondo(r_bgm, final.duration)
    bgm = AudioFileClip(r_bgm).volumex(0.18)
    
    mp4_out = os.path.join(carpeta, "VIDEO_FINAL.mp4")
    final.set_audio(CompositeAudioClip([final.audio, bgm])).write_videofile(
        mp4_out, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None
    )
    return mp4_out

# ==============================================================================
# DISTRIBUIDOR PLAYWRIGHT (YOUTUBE Y TIKTOK)
# ==============================================================================
async def subir_youtube(page, video_path, titulo, descripcion):
    print("🌐 Iniciando subida a YouTube Shorts...")
    await page.goto("https://studio.youtube.com/")
    await page.wait_for_timeout(3000)
    
    if "signin" in page.url:
        print("::error::Sesión de YouTube caducada.")
        return False

    await page.locator("#upload-icon").click()
    await page.locator("input[type='file']").set_input_files(video_path)
    await page.wait_for_timeout(5000)
    
    # Rellenar Título y Descripción
    cajas = page.locator("#textbox")
    await cajas.nth(0).fill(titulo)
    await page.wait_for_timeout(1000)
    await cajas.nth(1).fill(descripcion)
    
    # Marcar "No es para niños"
    await page.locator("tp-yt-paper-radio-button[name='NOT_MADE_FOR_KIDS']").click()
    
    # Pulsar Siguiente 3 veces
    for _ in range(3):
        await page.locator("#next-button").click()
        await page.wait_for_timeout(2000)
        
    # Marcar Público
    await page.locator("tp-yt-paper-radio-button[name='PUBLIC']").click()
    await page.wait_for_timeout(1000)
    
    # Publicar
    await page.locator("#done-button").click()
    
    try:
        await page.get_by_text(re.compile(r"Se ha publicado|Video published")).wait_for(timeout=30000)
        print("✅ ¡YouTube Short Publicado!")
        return True
    except Exception:
        print("::warning::No se detectó confirmación de YouTube, pero pudo haberse subido.")
        return True

async def subir_tiktok(page, video_path, titulo):
    print("🌐 Iniciando subida a TikTok...")
    await page.goto("https://www.tiktok.com/creator-center/upload")
    await page.wait_for_timeout(5000)
    
    if "login" in page.url:
        print("::error::Sesión de TikTok caducada.")
        return False
        
    # Inyectar archivo
    await page.locator("input[type='file'][accept*='video']").set_input_files(video_path)
    print("⏳ Subiendo vídeo a los servidores de TikTok (esperando 15s)...")
    await page.wait_for_timeout(15000)
    
    # Editor de texto de TikTok
    editor = page.locator(".public-DraftEditor-content")
    if await editor.count() > 0:
        await editor.fill(titulo)
    
    # Publicar
    boton_post = page.locator("button:has-text('Publicar'), button:has-text('Post')").last
    await boton_post.click()
    
    try:
        await page.get_by_text(re.compile(r"publicado|uploaded")).wait_for(timeout=20000)
        print("✅ ¡TikTok Publicado!")
        return True
    except Exception:
        print("::warning::No se detectó confirmación de TikTok, pero pudo haberse subido.")
        return True

async def despachador_redes(video_path, titulo_yt, link):
    descripcion_yt = f"Descubre cómo funciona tu mente.\nEl libro recomendado (gratis el primer mes) aquí: {link}\n#psicologia #desarrollopersonal #shorts"
    titulo_tk = f"{titulo_yt} #psicologia #desarrollopersonal"
    
    y_state = json.loads(YOUTUBE_STATE) if YOUTUBE_STATE else None
    t_state = json.loads(TIKTOK_STATE) if TIKTOK_STATE else None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Flujo YouTube
        if y_state:
            ctx_yt = await browser.new_context(storage_state=y_state, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            await subir_youtube(await ctx_yt.new_page(), video_path, titulo_yt, descripcion_yt)
            await ctx_yt.close()
            
        # Flujo TikTok
        if t_state:
            ctx_tk = await browser.new_context(storage_state=t_state, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            await subir_tiktok(await ctx_tk.new_page(), video_path, titulo_tk)
            await ctx_tk.close()
            
        await browser.close()

# ==============================================================================
# EJECUCIÓN PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    historial = cargar_historial()
    pendientes = [k for k in PACK_GUIONES.keys() if k not in historial]
    
    if not pendientes:
        print("ℹ️ Todos los guiones ya se han publicado. Reseteando historial para volver a empezar.")
        open(ARCHIVO_HISTORIAL, 'w').close()
        pendientes = list(PACK_GUIONES.keys())
        
    clave_elegida = random.choice(pendientes)
    datos = PACK_GUIONES[clave_elegida]
    
    ruta_mp4 = producir_video(clave_elegida, datos)
    
    print("🚀 Arrancando motores de publicación...")
    asyncio.run(despachador_redes(ruta_mp4, datos["titulo_yt"], LINK_AFILIADO))
    
    guardar_historial(clave_elegida)
    print("🎉 Proceso finalizado con éxito.")
