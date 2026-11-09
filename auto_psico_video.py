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
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# Imports para YouTube API y redes
from instagrapi import Client
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ARCHIVO_HISTORIAL = "historial_videos.txt"
LINK_AUDIBLE = "https://link.amazon/A091gjPQC"  # Tu enlace de 90 días

LIBROS_AFILIADOS = [
    {"titulo": "La Psicología del Lenguaje Corporal", "link": "https://link.amazon/B0gBvsEJI"},
    {"titulo": "Manual de Psicología de la Motivación", "link": "https://link.amazon/B0a48ro38"},
    {"titulo": "Psicología Oscura: Guía de Persuasión", "link": "https://link.amazon/B06iblozj"}
]

# ==============================================================================
# MEGA BASE DE DATOS DE 50 GUIONES (PEGAR AQUÍ TUS 50 GUIONES)
# ==============================================================================
PACK_GUIONES = {
    "1. Trucos contra manipuladores": {
        "cabecera": "3 TRUCOS DE PSICOLOGÍA OSCURA",
        "titulo_yt": "3 Trucos de Psicología Oscura para Dominar Cualquier Situación #Shorts",
        "escenas": [
            {"texto": "Si alguien te falta al respeto en público, aplica este truco inmediatamente."},
            {"texto": "Mírale a los ojos en silencio durante cuatro segundos. Destruirás su seguridad."},
            {"texto": "Pregúntale con voz calmada si se encuentra bien. Quedará en evidencia frente a todos."},
            {"texto": "Tienes los mejores audiolibros de persuasión gratis en la descripción."}
        ]
    },
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Pega aquí el resto de los 49 guiones que te preparé 
    # (Los 24 originales + los 26 nuevos). La estructura de 
    # escenas ahora solo necesita el "texto", los "prompts"
    # ya no hacen falta porque usamos siempre el mismo avatar.
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
}

def cargar_historial():
    if not os.path.exists(ARCHIVO_HISTORIAL):
        return []
    with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def guardar_historial(tema):
    with open(ARCHIVO_HISTORIAL, "a", encoding="utf-8") as f:
        f.write(f"{tema}\n")

async def generar_audio_y_tiempos(escenas, ruta_out):
    # Genera un audio maestro y guarda en qué segundo empieza cada frase para los subtítulos
    clips_audio = []
    tiempos_textos = []
    tiempo_actual = 0.0

    carpeta = "render_tmp"
    os.makedirs(carpeta, exist_ok=True)
    
    # VOZ FEMENINA JOVEN Y DULCE:
    voz = "es-ES-ElviraNeural"

    with open("temp_list.txt", "w") as f_list:
        for i, esc in enumerate(escenas):
            ruta_mp3 = os.path.join(carpeta, f"voz_{i}.mp3")
            comunicador = edge_tts.Communicate(esc["texto"], voz, rate="+5%")
            await comunicador.save(ruta_mp3)
            
            audio_clip = AudioFileClip(ruta_mp3)
            dur = audio_clip.duration
            
            # Guardamos la marca de tiempo (inicio, fin, texto)
            tiempos_textos.append((tiempo_actual, tiempo_actual + dur, esc["texto"]))
            tiempo_actual += dur + 0.2  # 0.2 seg de pausa entre frases
            
            ruta_wav = os.path.join(carpeta, f"voz_{i}.wav")
            audio_clip.write_audiofile(ruta_wav, logger=None)
            f_list.write(f"file '{ruta_wav}'\n")
            f_list.write(f"duration {dur}\n")
            f_list.write(f"file 'silence.wav'\n") # Mini silencio
            f_list.write(f"duration 0.2\n")
    
    # Crear archivo de silencio de 0.2s para pausas
    os.system("ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 0.2 -q:a 9 -acodec pcm_s16le render_tmp/silence.wav -y -hide_banner -loglevel error")
    
    # Unir todos los audios en uno solo
    os.system(f"ffmpeg -f concat -safe 0 -i temp_list.txt -c copy {ruta_out} -y -hide_banner -loglevel error")
    
    return tiempos_textos

def dibujar_subtitulos(frame, t, tiempos_textos, cabecera):
    # Dibuja la barra superior, la cabecera y el texto correspondiente al segundo 't'
    img = Image.fromarray(frame).convert("RGBA")
    capa = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    dr_capa = ImageDraw.Draw(capa)
    
    # Fondo oscurecido arriba y abajo para que el texto lea bien
    dr_capa.rectangle([(0, 0), (1080, 230)], fill=(0, 0, 0, 160))
    dr_capa.rectangle([(0, 1200), (1080, 1720)], fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img, capa).convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        f_cab = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
        f_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        f_cab = ImageFont.load_default()
        f_sub = ImageFont.load_default()

    # Cabecera superior
    bbox_c = draw.textbbox((0, 0), cabecera, font=f_cab)
    draw.text(((1080 - (bbox_c[2] - bbox_c[0])) / 2, 95), cabecera, font=f_cab, fill="#FFE600", stroke_width=4, stroke_fill="#000000")

    # Buscar el texto que toca en este segundo
    texto_actual = ""
    for inicio, fin, txt in tiempos_textos:
        if inicio <= t <= (fin + 0.2):
            texto_actual = txt
            break

    # Pintar Subtítulos
    if texto_actual:
        palabras = texto_actual.upper().split()
        lineas, actual = [], []
        for p in palabras:
            if len(" ".join(actual + [p])) > 19:
                lineas.append(" ".join(actual))
                actual = [p]
            else:
                actual.append(p)
        if actual: lineas.append(" ".join(actual))

        y = 1250
        for idx, lin in enumerate(lineas):
            color = "#00FF88" if idx == len(lineas)-1 else "#FFFFFF"
            bbox = draw.textbbox((0, 0), lin, font=f_sub)
            draw.text(((1080 - (bbox[2] - bbox[0])) / 2, y), lin, font=f_sub, fill=color, stroke_width=5, stroke_fill="#000000")
            y += (bbox[3] - bbox[1]) + 20

    return np.array(img)

def producir_video_avatar(clave, datos):
    print(f"🎬 Iniciando producción AVATAR: {clave}", flush=True)
    os.makedirs("render_tmp", exist_ok=True)
    audio_maestro = "render_tmp/audio_maestro.wav"

    # 1. Generar audio maestro y calcular tiempos
    tiempos_textos = asyncio.run(generar_audio_y_tiempos(datos["escenas"], audio_maestro))

    # 2. Ejecutar la IA local (Wav2Lip)
    print("🤖 Iniciando renderizado de Inteligencia Artificial (Esto tardará unos 10-15 mins)...")
    ruta_avatar_ia = "render_tmp/avatar_hablando.mp4"
    comando_ia = (
        "cd Wav2Lip && python inference.py "
        "--checkpoint_path checkpoints/wav2lip_gan.pth "
        "--face ../avatar.jpg "
        f"--audio ../{audio_maestro} "
        f"--outfile ../{ruta_avatar_ia} "
        "--nosmooth"
    )
    os.system(comando_ia)

    # 3. Quemar subtítulos encima del vídeo generado por la IA
    print("✍️ Quemando subtítulos sincronizados...")
    video_ia = VideoFileClip(ruta_avatar_ia)
    
    # Escalamos a 1080x1920 (Wav2Lip saca una resolución más pequeña)
    video_redimensionado = video_ia.resize(height=1920).crop(x_center=video_ia.w/2, width=1080)
    
    # Aplicamos nuestra función de dibujar textos cuadro por cuadro
    video_final = video_redimensionado.fl(lambda gf, t: dibujar_subtitulos(gf(t), t, tiempos_textos, datos["cabecera"]))

    mp4_out = "render_tmp/VIDEO_FINAL_AVATAR.mp4"
    video_final.write_videofile(
        mp4_out, fps=24, codec="libx264", audio_codec="aac",
        preset="veryfast", ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None
    )
    return mp4_out


# Funciones de redes sociales (Mantenemos las tuyas intactas)
def publicar_youtube_short(video_path, titulo_yt, libro_elegido):
    # ... Tu código de youtube ...
    return True

def publicar_instagram_reel(video_path, titulo_yt, libro_elegido):
    # ... Tu código de instagram ...
    return True

def enviar_pack_telegram(video_path, titulo_yt, libro_elegido):
    # ... Tu código de Telegram ...
    return True

if __name__ == "__main__":
    if not os.path.exists("avatar.jpg"):
        print("❌ ERROR FATAL: No se ha encontrado la imagen 'avatar.jpg' en el repositorio.")
        sys.exit(1)

    historial = cargar_historial()
    pendientes = [k for k in PACK_GUIONES if k not in historial]

    if not pendientes:
        print("🔄 Se completaron los 50 guiones. Reiniciando ciclo.")
        open(ARCHIVO_HISTORIAL, "w").close()
        pendientes = list(PACK_GUIONES.keys())

    clave_elegida = random.choice(pendientes)
    datos = PACK_GUIONES[clave_elegida]
    libro_al_azar = random.choice(LIBROS_AFILIADOS)

    ruta_mp4 = producir_video_avatar(clave_elegida, datos)
    
    # 1. Telegram
    exito_telegram = enviar_pack_telegram(ruta_mp4, datos["titulo_yt"], libro_al_azar)
    # 2. Instagram
    exito_ig = publicar_instagram_reel(ruta_mp4, datos["titulo_yt"], libro_al_azar)
    # 3. YouTube
    exito_yt = publicar_youtube_short(ruta_mp4, datos["titulo_yt"], libro_al_azar)
    
    if exito_telegram or exito_ig or exito_yt:
        guardar_historial(clave_elegida)
        print("🎉 Proceso de avatar completado con éxito.")
    else:
        print("⚠️ Hubo un fallo en la distribución.")
