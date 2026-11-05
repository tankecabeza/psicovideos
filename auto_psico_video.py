import os
import sys
import time
import wave
import random
import asyncio
import urllib.parse
import requests
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from moviepy import (
    ImageClip, AudioFileClip, CompositeAudioClip,
    CompositeVideoClip, concatenate_videoclips,
)
from instagrapi import Client

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

# ==============================================================================
# CONFIGURACIÓN Y ENLACES DE AFILIADO
# ==============================================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ARCHIVO_HISTORIAL = "historial_videos.txt"

LINK_AUDIBLE = "https://link.amazon/A019r3w21"

LIBROS_AFILIADOS = [
    {"titulo": "La Psicología del Lenguaje Corporal (6 Libros en 1)", "link": "https://link.amazon/B0gBvsEJI"},
    {"titulo": "Manual de Psicología de la Motivación", "link": "https://link.amazon/B0a48ro38"},
    {"titulo": "Psicología + Biblia = Sabiduría y Felicidad", "link": "https://link.amazon/B01Dbo2sd"},
    {"titulo": "Gran Guía Visual de la Psicología", "link": "https://link.amazon/B05oFn5m8"},
    {"titulo": "Psicología Oscura: Guía Esencial de Persuasión y PNL", "link": "https://link.amazon/B06iblozj"},
    {"titulo": "Psicología del Color: Sentimientos y Razón", "link": "https://link.amazon/B0fGUqwUw"},
    {"titulo": "Psico Cuentos: Inteligencia Emocional", "link": "https://link.amazon/B02pmWFFv"}
]

# ==============================================================================
# MEGA BASE DE DATOS DE GUIONES (Omitida visualmente aquí, mantén tu diccionario PACK_GUIONES intacto)
# ==============================================================================
PACK_GUIONES = {
    "1. Trucos contra manipuladores": {
        "cabecera": "3 TRUCOS DE PSICOLOGÍA OSCURA",
        "titulo_yt": "3 Trucos de Psicología Oscura para Dominar Cualquier Situación #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si alguien te falta al respeto en público, aplica este truco inmediatamente.", "prompt": "mysterious man in suit dark room dramatic lighting"},
            {"texto": "Uno: mírale a los ojos en silencio durante cuatro segundos. Destruirás su seguridad.", "prompt": "extreme closeup intense eyes in shadow dark moody"},
            {"texto": "Dos: pregúntale con voz calmada si se encuentra bien. Quedará en evidencia frente a todos.", "prompt": "two silhouettes arguing in dark office cinematic"},
            {"texto": "Tienes los mejores libros de persuasión y audiolibros gratis en la descripción.", "prompt": "ancient leather book with gold letters on dark desk"}
        ]
    },
    # (AÑADE EL RESTO DE TUS 24 GUIONES AQUÍ, NO LOS HE BORRADO, SOLO ACORTADO POR ESPACIO)
}

# ==============================================================================
# HISTORIAL
# ==============================================================================
def cargar_historial():
    if not os.path.exists(ARCHIVO_HISTORIAL):
        return []
    with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def guardar_historial(tema):
    with open(ARCHIVO_HISTORIAL, "a", encoding="utf-8") as f:
        f.write(f"{tema}\n")

# ==============================================================================
# GENERADOR PROCEDURAL Y DESCARGA IA (Igual que tu versión anterior)
# ==============================================================================
def generar_fondo_procedural_oscuro(ruta_img: str, seed: int):
    rng = np.random.default_rng(seed)
    W, H = 1080, 1920
    y, x = np.ogrid[:H, :W]
    cx = rng.integers(int(W * 0.25), int(W * 0.75))
    cy = rng.integers(int(H * 0.25), int(H * 0.65))
    dist = np.sqrt((x - cx) ** 2 + ((y - cy) * 0.65) ** 2)
    glow = np.clip(1.0 - dist / 950.0, 0, 1) ** 2.2
    paletas = [(75, 20, 35), (18, 52, 85), (70, 52, 18), (20, 65, 55), (55, 25, 75)]
    c = paletas[seed % len(paletas)]
    ruido = rng.normal(0, 4.5, (H, W))
    r = np.clip(8 + glow * c[0] + ruido, 0, 255).astype(np.uint8)
    g = np.clip(10 + glow * c[1] + ruido, 0, 255).astype(np.uint8)
    b = np.clip(16 + glow * c[2] + ruido, 0, 255).astype(np.uint8)
    img = Image.fromarray(np.dstack([r, g, b]))
    dr = ImageDraw.Draw(img)
    for _ in range(4):
        x0 = int(rng.integers(80, W - 80))
        dr.line([(x0, 0), (x0, H)], fill=(255, 255, 255), width=1)
    img.save(ruta_img, quality=92)

def descargar_fondo_ia(prompt: str, ruta_img: str, seed: int):
    prm = urllib.parse.quote(f"{prompt}, vertical 9:16, dark moody cinematography, hyperrealistic, dramatic shadows, no text")
    urls_intento = [
        f"https://image.pollinations.ai/prompt/{prm}?width=576&height=1024&seed={seed}&nologo=true",
        f"https://pollinations.ai/p/{prm}?width=576&height=1024&seed={seed + 11}&nologo=true"
    ]
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ]
    for intento, url in enumerate(urls_intento, 1):
        try:
            time.sleep(3.5 * intento)
            headers = {"User-Agent": user_agents[0], "Accept": "image/*"}
            r = requests.get(url, headers=headers, timeout=45)
            if r.status_code == 200 and len(r.content) > 8000:
                with open(ruta_img, "wb") as f:
                    f.write(r.content)
                im = Image.open(ruta_img).convert("RGB").resize((1080, 1920), Image.LANCZOS)
                im.save(ruta_img, quality=95)
                return
        except:
            pass
    generar_fondo_procedural_oscuro(ruta_img, seed)

# ==============================================================================
# AUDIO, SUBTÍTULOS Y PRODUCCIÓN VÍDEO (API 2.x restaurada)
# ==============================================================================
def crear_musica_fondo(filepath: str, duracion: float, sr: int = 44100):
    t = np.linspace(0, duracion, int(sr * duracion), False)
    sub = np.sin(2 * np.pi * 55.0 * t) * 0.50
    mid = np.sin(2 * np.pi * 82.41 * t) * 0.25
    high = np.sin(2 * np.pi * 110.0 * t) * 0.15
    pulso = 0.65 + 0.35 * np.sin(2 * np.pi * 0.25 * t)
    audio_pcm = (np.clip((sub + mid + high) * pulso * 0.26, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_pcm.tobytes())

async def sintetizar_voz(texto: str, voz: str, ruta_mp3: str):
    comunicador = edge_tts.Communicate(texto, voz, rate="+12%")
    await comunicador.save(ruta_mp3)

def quemar_textos(ruta_in, cabecera, texto, num_escena, total_escenas, ruta_out):
    img = Image.open(ruta_in).convert("RGBA").resize((1080, 1920), Image.LANCZOS)
    capa = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    dr_capa = ImageDraw.Draw(capa)
    dr_capa.rectangle([(0, 0), (1080, 230)], fill=(0, 0, 0, 165))
    dr_capa.rectangle([(0, 1100), (1080, 1720)], fill=(0, 0, 0, 140))
    img = Image.alpha_composite(img, capa).convert("RGB")
    draw = ImageDraw.Draw(img)
    # Ajusta la ruta de la fuente según tu entorno si falla, esto funciona en Ubuntu/GitHub
    try:
        f_cab = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
        f_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 68)
    except:
        f_cab = ImageFont.load_default()
        f_sub = ImageFont.load_default()

    bbox_c = draw.textbbox((0, 0), cabecera, font=f_cab)
    draw.text(((1080 - (bbox_c[2] - bbox_c[0])) / 2, 95), cabecera, font=f_cab, fill="#FFFFFF", stroke_width=4, stroke_fill="#000000")

    palabras = texto.upper().split()
    lineas, actual = [], []
    for p in palabras:
        if len(" ".join(actual + [p])) > 18:
            lineas.append(" ".join(actual))
            actual = [p]
        else:
            actual.append(p)
    if actual: lineas.append(" ".join(actual))

    y = 1185
    mitad = max(1, len(lineas) // 2)
    for idx, lin in enumerate(lineas):
        es_ultima = num_escena == total_escenas - 1
        color = "#00FF88" if (es_ultima and idx >= mitad) else ("#FFE600" if es_ultima or idx >= mitad else "#FFFFFF")
        bbox = draw.textbbox((0, 0), lin, font=f_sub)
        draw.text(((1080 - (bbox[2] - bbox[0])) / 2, y), lin, font=f_sub, fill=color, stroke_width=6, stroke_fill="#000000")
        y += (bbox[3] - bbox[1]) + 24
    img.save(ruta_out, quality=95)

def producir_video(clave, datos):
    print(f"🎬 Produciendo: {clave}", flush=True)
    carpeta = "render_tmp"
    os.makedirs(carpeta, exist_ok=True)
    clips = []

    for i, esc in enumerate(datos["escenas"]):
        r_mp3 = os.path.join(carpeta, f"voz_{i}.mp3")
        r_raw = os.path.join(carpeta, f"raw_{i}.jpg")
        r_sub = os.path.join(carpeta, f"escena_{i}.jpg")

        asyncio.run(sintetizar_voz(esc["texto"], "es-ES-AlvaroNeural", r_mp3))
        audio = AudioFileClip(r_mp3)
        dur = audio.duration + 0.3

        descargar_fondo_ia(esc["prompt"], r_raw, random.randint(100, 99999))
        quemar_textos(r_raw, datos["cabecera"], esc["texto"], i, len(datos["escenas"]), r_sub)

        # Sintaxis original de MoviePy 2.x restaurada
        base = ImageClip(r_sub).with_duration(dur)
        zoom = base.resized(lambda t: 1.0 + 0.032 * t).with_position(("center", "center"))
        escena = CompositeVideoClip([zoom], size=(1080, 1920)).with_duration(dur).with_audio(audio)
        clips.append(escena)

    final = concatenate_videoclips(clips, method="compose")
    r_bgm = os.path.join(carpeta, "bgm.wav")
    crear_musica_fondo(r_bgm, final.duration)
    
    # Sintaxis original de MoviePy 2.x restaurada
    bgm = AudioFileClip(r_bgm).with_volume_scaled(0.18).with_duration(final.duration)

    mezcla = CompositeAudioClip([final.audio, bgm])
    mp4_out = os.path.join(carpeta, "VIDEO_FINAL.mp4")
    
    final.with_audio(mezcla).write_videofile(
        mp4_out, fps=24, codec="libx264", audio_codec="aac",
        preset="ultrafast", logger=None
    )
    return mp4_out

# ==============================================================================
# ENVÍO A TELEGRAM (CON #PUBLI AÑADIDO)
# ==============================================================================
def enviar_pack_telegram(video_path, titulo_yt, libro_elegido):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Faltan credenciales de Telegram. Omitiendo.")
        return False

    titulo_yt_limpio = titulo_yt[:100].strip()

    descripcion_yt = (
        f"¿Quieres dominar tu mente y entender el comportamiento humano?\n\n"
        f"🎧 Prueba Audible 30 días GRATIS (Audiolibros ilimitados): {LINK_AUDIBLE}\n\n"
        f"📚 Libro recomendado de hoy: {libro_elegido['titulo']}\n"
        f"👉 Consíguelo aquí: {libro_elegido['link']}\n\n"
        f"#publi #psicologia #psicologiaoscura #lenguajecorporal #persuasion #manipulacion"
    )

    descripcion_tiktok = (
        f"{titulo_yt_limpio} 🧠 Libro recomendado y prueba GRATIS de Audible en el enlace de mi perfil 🔗 "
        f"#publi #psicologia #psicologiaoscura #lenguajecorporal #manipulacion #curiosidades"
    )

    url_video = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        with open(video_path, "rb") as vid:
            r1 = requests.post(
                url_video,
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": f"🎬 <b>VÍDEO LISTO:</b> {titulo_yt_limpio}",
                    "parse_mode": "HTML",
                    "supports_streaming": "true"
                },
                files={"video": vid},
                timeout=180,
            )
        if r1.status_code != 200:
            print(f"❌ Error subiendo vídeo a Telegram: {r1.text}")
            return False

        texto_copiable = (
            f"📋 <b>TOCA CADA CAJA PARA COPIARLA AL PORTAPAPELES:</b>\n\n"
            f"1️⃣ <b>TÍTULO YOUTUBE SHORTS:</b>\n<code>{titulo_yt_limpio}</code>\n\n"
            f"2️⃣ <b>DESCRIPCIÓN YOUTUBE:</b>\n<code>{descripcion_yt}</code>\n\n"
            f"3️⃣ <b>DESCRIPCIÓN TIKTOK:</b>\n<code>{descripcion_tiktok}</code>"
        )
        requests.post(
            url_msg,
            data={"chat_id": TELEGRAM_CHAT_ID, "text": texto_copiable, "parse_mode": "HTML"},
            timeout=30,
        )
        print("✅ ¡Vídeo y textos enviados a Telegram!")
        return True
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")
        return False

# ==============================================================================
# ENVÍO A INSTAGRAM (CON INYECCIÓN DE SESIÓN)
# ==============================================================================
def publicar_instagram_reel(video_path, titulo_yt, libro_elegido):
    INSTA_USER = os.getenv("INSTA_USER")
    INSTA_PASS = os.getenv("INSTA_PASS")
    INSTA_SESSION = os.getenv("INSTA_SESSION")
    
    if not all([INSTA_USER, INSTA_PASS, INSTA_SESSION]):
        print("⚠️ Faltan credenciales o sesión de Instagram en los Secrets. Omitiendo subida.")
        return False

    titulo_limpio = titulo_yt[:100].strip()
    descripcion_ig = (
        f"{titulo_limpio}\n\n"
        f"🎧 Prueba Audible 30 días GRATIS (link en mi bio)\n"
        f"📚 Libro de hoy: {libro_elegido['titulo']}\n\n"
        f"#publi #psicologia #psicologiaoscura #lenguajecorporal #persuasion #manipulacion"
    )

    print("📱 Conectando a Instagram mediante sesión inyectada...")
    try:
        cl = Client()
        cl.delay_range = [2, 6] # Simula tiempos de espera humanos
        cl.set_settings(json.loads(INSTA_SESSION))
        cl.login(INSTA_USER, INSTA_PASS)
        
        print("🚀 Subiendo Reel a Instagram...")
        cl.clip_upload(
            video_path,
            descripcion_ig,
            extra_data={
                "custom_accessibility_caption": "Vídeo animado de psicología.",
                "like_and_view_counts_disabled": 0,
                "disable_comments": 0,
            }
        )
        print("✅ ¡Reel publicado con éxito en Instagram!")
        return True
    except Exception as e:
        print(f"❌ Error subiendo a Instagram: {e}")
        return False

# ==============================================================================
# EJECUCIÓN PRINCIPAL CON CONTROL DE FALLOS
# ==============================================================================
if __name__ == "__main__":
    historial = cargar_historial()
    pendientes = [k for k in PACK_GUIONES if k not in historial]

    if not pendientes:
        print("ℹ️ Historial completado (24 vídeos). Reiniciando ciclo.")
        open(ARCHIVO_HISTORIAL, "w").close()
        pendientes = list(PACK_GUIONES.keys())

    clave_elegida = random.choice(pendientes)
    datos = PACK_GUIONES[clave_elegida]
    libro_al_azar = random.choice(LIBROS_AFILIADOS)

    ruta_mp4 = producir_video(clave_elegida, datos)
    
    # 1. Enviar primero a Telegram (Garantiza que lo recibes siempre)
    exito_telegram = enviar_pack_telegram(ruta_mp4, datos["titulo_yt"], libro_al_azar)
    
    # 2. Publicar en Instagram usando la sesión guardada
    exito_ig = publicar_instagram_reel(ruta_mp4, datos["titulo_yt"], libro_al_azar)
    
    # Solo guarda en el historial si AL MENOS una plataforma lo recibió bien. 
    # Así, si Instagram falla por algo, la próxima vez generará otro distinto, 
    # o si fallan ambas, reintentará este mismo mañana.
    if exito_telegram or exito_ig:
        guardar_historial(clave_elegida)
        print("🎉 Proceso completado con éxito.")
    else:
        print("⚠️ Hubo un fallo general en la distribución. No se marca como publicado.")
