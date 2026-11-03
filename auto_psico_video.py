import os
import sys
import wave
import random
import asyncio
import urllib.parse
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from moviepy import (
    ImageClip, AudioFileClip, CompositeAudioClip,
    CompositeVideoClip, concatenate_videoclips,
)

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ARCHIVO_HISTORIAL = "historial_videos.txt"

# --- ENLACES DE AFILIADO ---
LINK_AUDIBLE = "https://link.amazon/A019r3w21"

LIBROS_AFILIADOS = [
    {"titulo": "LA PSICOLOGÍA DEL LENGUAJE CORPORAL (6 Libros en 1)", "link": "https://link.amazon/B0gBvsEJI"},
    {"titulo": "Manual de Psicología de la Motivación", "link": "https://link.amazon/B0a48ro38"},
    {"titulo": "Psicología + Biblia = Sabiduría y Felicidad", "link": "https://link.amazon/B01Dbo2sd"},
    {"titulo": "Gran Guía Visual de la Psicología", "link": "https://link.amazon/B05oFn5m8"},
    {"titulo": "Psicología Oscura: Guía esencial de persuasión", "link": "https://link.amazon/B06iblozj"},
    {"titulo": "Psicología del color: Sentimientos y razón", "link": "https://link.amazon/B0fGUqwUw"},
    {"titulo": "Psico Cuentos: Inteligencia emocional", "link": "https://link.amazon/B02pmWFFv"}
]

# --- BASE DE DATOS DE CONTENIDO VIRAL ---
PACK_GUIONES = {
    "1. Trucos contra manipuladores": {
        "cabecera": "3 TRUCOS DE PSICOLOGÍA OSCURA",
        "titulo_yt": "3 Trucos de Psicología Oscura para Dominar Cualquier Situación #Shorts",
        "escenas": [
            {"texto": "Si alguien te falta al respeto en público, haz esto inmediatamente.", "prompt": "mysterious man in dark room cinematic 8k"},
            {"texto": "Uno: mírale a los ojos en silencio durante cuatro segundos. Destruirás su seguridad.", "prompt": "intense eyes in shadow dark aesthetic 8k"},
            {"texto": "Dos: pregúntale con voz calmada si está bien. Quedará en evidencia frente a todos.", "prompt": "two shadowy figures talking dark room 8k"},
            {"texto": "Tienes audiolibros prohibidos de persuasión en el enlace de la descripción.", "prompt": "leather gold book on dark desk candlelight"}
        ]
    },
    "2. Detectar mentiras": {
        "cabecera": "TÉCNICAS DEL FBI",
        "titulo_yt": "Cómo Saber si te Mienten en 5 Segundos según el FBI #psicologia",
        "escenas": [
            {"texto": "Así descubres a un mentiroso en menos de cinco segundos.", "prompt": "interrogation room dark lamp cinematic"},
            {"texto": "Si repite tu pregunta antes de responder, está ganando tiempo para inventar.", "prompt": "nervous man sweating shadow 8k"},
            {"texto": "Pídele que cuente la historia hacia atrás. Los mentirosos siempre se bloquean.", "prompt": "chess piece falling slow motion dark 8k"},
            {"texto": "Aprende a leer la mente de los demás con los libros del enlace fijado.", "prompt": "classified dossier dark leather book desk"}
        ]
    },
    "3. El Efecto Escasez": {
        "cabecera": "LA LEY DEL DESAPEGO",
        "titulo_yt": "Por Qué Cuanto Más Das, Menos Te Valoran #psicologia #shorts",
        "escenas": [
            {"texto": "Deja de estar siempre disponible para todo el mundo.", "prompt": "lone man walking away foggy street night 8k"},
            {"texto": "El cerebro humano desprecia lo gratuito y se obsesiona con lo escaso.", "prompt": "gold pocket watch on dark velvet luxury"},
            {"texto": "Retira tu atención en silencio y verás cómo empiezan a buscarte.", "prompt": "silhouette confident man tall skyscraper window"},
            {"texto": "Domina las leyes de la persuasión escuchando libros gratis en mi perfil.", "prompt": "minimalist dark book golden light 8k"}
        ]
    },
    "4. Triangulación Visual": {
        "cabecera": "EL TRUCO DE LA MIRADA",
        "titulo_yt": "El Truco Visual para Enamorar o Intimidar a Alguien #lenguajecorporal",
        "escenas": [
            {"texto": "Usa la mirada triangular para controlar lo que la otra persona siente por ti.", "prompt": "close up of a person eyes looking sharp cinematic 8k"},
            {"texto": "Si quieres seducir: mira a su ojo izquierdo, luego al derecho y baja a sus labios.", "prompt": "soft neon lighting romance tension aesthetic 8k"},
            {"texto": "Si quieres intimidar: mira a sus ojos y luego al centro de su frente. Sentirá inferioridad.", "prompt": "intense cold stare shadow background 8k"},
            {"texto": "Domina el lenguaje corporal experto en el enlace de la descripción.", "prompt": "mysterious figure silhouette against window"}
        ]
    },
    "5. El Efecto Halo": {
        "cabecera": "EL SESGO DE LA BELLEZA",
        "titulo_yt": "Por Qué la Gente Atractiva lo Tiene Más Fácil (Efecto Halo) #curiosidades",
        "escenas": [
            {"texto": "El efecto Halo es el sesgo psicológico más injusto de la humanidad.", "prompt": "angelic glowing silhouette dark background 8k"},
            {"texto": "Tu cerebro asume automáticamente que la gente atractiva es más inteligente y buena.", "prompt": "beautiful person walking in slow motion crowd 8k"},
            {"texto": "Por eso los criminales atractivos reciben condenas más cortas en los juicios.", "prompt": "gavel striking in dark courtroom shadow 8k"},
            {"texto": "Descubre cómo hackear tu mente con los audiolibros del comentario fijado.", "prompt": "golden brain glowing aesthetic"}
        ]
    },
    "6. Gaslighting Sutil": {
        "cabecera": "CÓMO TE DESTRUYEN LA MENTE",
        "titulo_yt": "Si Alguien te Dice Estas 3 Frases, Huye Inmediatamente #manipulacion",
        "escenas": [
            {"texto": "El gaslighting es la técnica de manipulación más peligrosa que existe.", "prompt": "person holding head in hands dark room foggy 8k"},
            {"texto": "Si te dicen: 'eres demasiado sensible' o 'eso nunca pasó así'...", "prompt": "two people arguing shadow dramatic lighting 8k"},
            {"texto": "Están hackeando tu memoria para que dudes de tu propia cordura.", "prompt": "shattered mirror reflecting confused face 8k"},
            {"texto": "Aprende a defenderte de narcisistas con los manuales de mi perfil.", "prompt": "padlocked leather diary dark aesthetic"}
        ]
    },
    "7. Efecto Zeigarnik": {
        "cabecera": "POR QUÉ NO PUEDES OLVIDAR",
        "titulo_yt": "El Truco Psicológico para que Alguien Piense en Ti Todo el Día",
        "escenas": [
            {"texto": "Si quieres que alguien no deje de pensar en ti, usa el Efecto Zeigarnik.", "prompt": "person staring at glowing phone screen dark room 8k"},
            {"texto": "El cerebro humano odia las tareas inconclusas y las recuerda el doble de tiempo.", "prompt": "puzzle missing one piece dark velvet 8k"},
            {"texto": "Vete en el mejor momento de la cita o deja un mensaje sin terminar. Se obsesionarán.", "prompt": "footsteps walking away in foggy street 8k"},
            {"texto": "Conviértete en un maestro de la mente con el enlace de la descripción.", "prompt": "brain glowing inside a glass jar neon"}
        ]
    },
    "8. Leer el lenguaje corporal": {
        "cabecera": "DETECTA LA VERDAD OCULTA",
        "titulo_yt": "Lo que Sus Pies Dicen de Ti (Lenguaje Corporal Oculto) #shorts",
        "escenas": [
            {"texto": "La cara puede mentir a la perfección, pero los pies jamás lo hacen.", "prompt": "feet stepping on dark floor dramatic light 8k"},
            {"texto": "Si alguien apunta con los pies hacia la salida, desea marcharse aunque sonría.", "prompt": "person looking at watch dark room 8k"},
            {"texto": "Analiza las microexpresiones y descubre quién te esconde la verdad.", "prompt": "close up eyes detective dark 8k"},
            {"texto": "Conviértete en un experto leyendo personas con el libro de la descripción.", "prompt": "magnifying glass over dark text book"}
        ]
    },
    "9. Paradoja de la Elección": {
        "cabecera": "POR QUÉ DUDAS TANTO",
        "titulo_yt": "El Truco para Tomar Decisiones Perfectas al Instante #psicologia",
        "escenas": [
            {"texto": "Cuantas más opciones tienes, más infeliz serás con tu decisión final.", "prompt": "person standing at crossroads dark foggy forest 8k"},
            {"texto": "Se llama Paradoja de la Elección, y paraliza tu cerebro por miedo a equivocarte.", "prompt": "hundreds of glowing doors in infinite dark hallway 8k"},
            {"texto": "Reduce siempre tus opciones a solo tres, y tu mente elegirá sin estrés.", "prompt": "three glowing doors in dark room cinematic 8k"},
            {"texto": "Mejora tu toma de decisiones escuchando los audiolibros de mi perfil.", "prompt": "glowing lightbulb above open book"}
        ]
    },
    "10. Técnica del Espejo": {
        "cabecera": "EL HACK DE LA SIMPATÍA",
        "titulo_yt": "Cómo Caerle Bien a Alguien en Solo 10 Segundos #manipulacion",
        "escenas": [
            {"texto": "¿Quieres agradar al instante? Utiliza la técnica del espejo camuflado.", "prompt": "two people sitting talking cinematic dark light 8k"},
            {"texto": "Copia sutilmente su postura, el tono de su voz y sus gestos con las manos.", "prompt": "mirror reflection of a confident person 8k"},
            {"texto": "Su subconsciente pensará: 'esta persona es como yo', y bajará sus defensas.", "prompt": "handshake in shadows glowing edge 8k"},
            {"texto": "Domina la persuasión absoluta con los libros prohibidos de mi enlace.", "prompt": "book with a silver key on top dark aesthetic"}
        ]
    }
}

# ==============================================================================
# HISTORIAL
# ==============================================================================
def cargar_historial():
    if not os.path.exists(ARCHIVO_HISTORIAL): return []
    with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def guardar_historial(tema):
    with open(ARCHIVO_HISTORIAL, "a", encoding="utf-8") as f:
        f.write(f"{tema}\n")

# ==============================================================================
# LÓGICA AUDIOVISUAL
# ==============================================================================
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
    comunicador = edge_tts.Communicate(texto, voz, rate="+12%")
    await comunicador.save(ruta_mp3)

def descargar_fondo_ia(prompt: str, ruta_img: str, seed: int):
    # Mejora: Usamos explícitamente el modelo 'flux' para evitar errores y subir el fotorrealismo
    prm = urllib.parse.quote(f"{prompt}, vertical 9:16, dark moody cinematography, hyperrealistic, no text")
    url = f"https://image.pollinations.ai/prompt/{prm}?width=1080&height=1920&seed={seed}&nologo=true&model=flux"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(ruta_img, "wb") as f:
            f.write(r.content)
        Image.open(ruta_img).verify()
    except Exception as e:
        print(f"⚠️ Fondo IA falló, creando fondo oscuro de emergencia...")
        Image.new("RGB", (1080, 1920), (14, 18, 28)).save(ruta_img)

def quemar_textos(ruta_in, cabecera, texto, num_escena, total_escenas, ruta_out):
    img = Image.open(ruta_in).convert("RGBA").resize((1080, 1920), Image.LANCZOS)
    capa = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    dr_capa = ImageDraw.Draw(capa)
    dr_capa.rectangle([(0, 0), (1080, 230)], fill=(0, 0, 0, 150))
    dr_capa.rectangle([(0, 1120), (1080, 1680)], fill=(0, 0, 0, 125))
    img = Image.alpha_composite(img, capa).convert("RGB")
    draw = ImageDraw.Draw(img)

    fuente = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    f_cab = ImageFont.truetype(fuente, 44)
    f_sub = ImageFont.truetype(fuente, 72)

    bbox_c = draw.textbbox((0, 0), cabecera, font=f_cab)
    draw.text(((1080 - (bbox_c[2] - bbox_c[0])) / 2, 95), cabecera, font=f_cab, fill="#FFFFFF", stroke_width=4, stroke_fill="#000000")

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
        es_ultima = num_escena == total_escenas - 1
        if es_ultima and idx >= mitad: color = "#00FF88"
        elif es_ultima or idx >= mitad: color = "#FFE600"
        else: color = "#FFFFFF"
        bbox = draw.textbbox((0, 0), lin, font=f_sub)
        draw.text(((1080 - (bbox[2] - bbox[0])) / 2, y), lin, font=f_sub, fill=color, stroke_width=6, stroke_fill="#000000")
        y += (bbox[3] - bbox[1]) + 26
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

        descargar_fondo_ia(esc["prompt"], r_raw, random.randint(100, 9999))
        quemar_textos(r_raw, datos["cabecera"], esc["texto"], i, len(datos["escenas"]), r_sub)

        base = ImageClip(r_sub).with_duration(dur)
        zoom = base.resized(lambda t: 1.0 + 0.028 * t).with_position(("center", "center"))
        escena = CompositeVideoClip([zoom], size=(1080, 1920)).with_duration(dur).with_audio(audio)
        clips.append(escena)

    final = concatenate_videoclips(clips, method="compose")
    r_bgm = os.path.join(carpeta, "bgm.wav")
    crear_musica_fondo(r_bgm, final.duration)
    bgm = AudioFileClip(r_bgm).with_volume_scaled(0.18).with_duration(final.duration)

    mezcla = CompositeAudioClip([final.audio, bgm])
    mp4_out = os.path.join(carpeta, "VIDEO_FINAL.mp4")
    final.with_audio(mezcla).write_videofile(mp4_out, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
    return mp4_out

# ==============================================================================
# ENVÍO A TELEGRAM CON BLOQUES COPY-PASTE (TOCAR PARA COPIAR)
# ==============================================================================
def enviar_video_telegram(video_path, titulo_yt, libro_elegido):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    
    # <code> permite copiar todo el bloque de texto con un simple toque en Telegram
    caption = (
        f"🧠 <b>¡NUEVO VÍDEO LISTO!</b>\n\n"
        f"🔴 <b>YOUTUBE (Toca el texto para copiarlo):</b>\n"
        f"<code>{titulo_yt}\n\n"
        f"¿Quieres dominar tu mente y la de los demás? Descubre los secretos de la psicología humana.\n\n"
        f"🎧 Consigue cualquier audiolibro GRATIS con tu prueba de Audible: {LINK_AUDIBLE}\n"
        f"📚 Libro recomendado de hoy ({libro_elegido['titulo']}): {libro_elegido['link']}\n\n"
        f"#psicologia #psicologiaoscura #desarrollopersonal #manipulacion #curiosidades</code>\n\n"
        f"🎵 <b>TIKTOK (Toca el texto para copiarlo):</b>\n"
        f"<code>{titulo_yt} 🧠 ¡Descubre el secreto en el link de mi perfil (Audiolibro GRATIS)! 🤫 #psicologia #psicologiaoscura #manipulacion #lenguajecorporal #mentalidad</code>"
    )

    try:
        with open(video_path, "rb") as vid:
            requests.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "HTML", "supports_streaming": "true", "width": 1080, "height": 1920},
                files={"video": vid},
                timeout=180,
            )
        return True
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")
        return False

# ==============================================================================
# EJECUCIÓN PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    historial = cargar_historial()
    pendientes = [k for k in PACK_GUIONES if k not in historial]

    if not pendientes:
        print("ℹ️ Historial reiniciado. Volviendo a empezar.")
        open(ARCHIVO_HISTORIAL, "w").close()
        pendientes = list(PACK_GUIONES.keys())

    clave_elegida = random.choice(pendientes)
    datos = PACK_GUIONES[clave_elegida]
    
    # Elegimos un libro al azar de tu lista para este vídeo
    libro_al_azar = random.choice(LIBROS_AFILIADOS)

    ruta_mp4 = producir_video(clave_elegida, datos)
    enviar_video_telegram(ruta_mp4, datos["titulo_yt"], libro_al_azar)
    guardar_historial(clave_elegida)
    print("🎉 Proceso completado.")
