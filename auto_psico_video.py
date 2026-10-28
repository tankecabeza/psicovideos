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

# Parche Pillow para MoviePy
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
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
    },
    "4. Controlar una conversacion": {
        "cabecera": "DOMINA CUALQUIER CONVERSACIÓN",
        "titulo_yt": "El Secreto Psicológico para Controlar a los Demás sin que lo Noten",
        "libro_afiliado": "Psicología Oscura y Manipulación",
        "escenas": [
            {"texto": "Quien hace las preguntas en una conversación, tiene el control absoluto.", "prompt": "interrogator sitting in dark room 8k"},
            {"texto": "Si intentan atacarte, no te defiendas. Devuelve la pregunta con otra pregunta.", "prompt": "mirror reflection dark aesthetic 8k"},
            {"texto": "Observa cómo la otra persona empieza a dudar de sus propias palabras.", "prompt": "confused person under dim light 8k"},
            {"texto": "Domina el arte de la manipulación mental con el libro del comentario fijado.", "prompt": "ancient secret book dark background"}
        ]
    },
    "5. El poder del silencio": {
        "cabecera": "EL ARMA DEL SILENCIO",
        "titulo_yt": "Por Qué el Silencio Incomoda Tanto a los Manipuladores #shorts",
        "libro_afiliado": "El Poder del Ahora",
        "escenas": [
            {"texto": "El silencio es una de las armas psicológicas más destructivas que existen.", "prompt": "silent dark room dramatic shadows 8k"},
            {"texto": "Cuando alguien te insulte o presione, no respondas al instante. Quédate en silencio.", "prompt": "person holding finger to lips quiet dark 8k"},
            {"texto": "El cerebro de la otra persona interpretará ese vacío como una amenaza y cederá.", "prompt": "broken glass shadow dark background 8k"},
            {"texto": "Descubre cómo usar la inteligencia emocional a tu favor en el enlace fijado.", "prompt": "mysterious glowing book dark room"}
        ]
    },
    "6. Sesgo de confirmacion": {
        "cabecera": "CÓMO MANIPULAN TU MENTE",
        "titulo_yt": "El Sesgo Oculto que Te Hace Creer Mentiras Todos los Días",
        "libro_afiliado": "Pensar Rápido, Pensar Despacio",
        "escenas": [
            {"texto": "Tu cerebro busca constantemente pruebas para confirmar lo que ya cree.", "prompt": "maze of mirrors dark moody 8k"},
            {"texto": "Por eso es tan fácil manipular a las masas sin que se den cuenta.", "prompt": "crowd of silhouettes in dark blue light 8k"},
            {"texto": "Para romper este ciclo, debes cuestionar aquello de lo que estás más seguro.", "prompt": "key opening a heavy dark door 8k"},
            {"texto": "Aprende cómo funciona realmente tu mente en el libro del comentario fijado.", "prompt": "brain glowing neon dark minimalist 8k"}
        ]
    },
    "7. La tecnica del pie en la puerta": {
        "cabecera": "TÉCNICA DE PERSUASIÓN LETAL",
        "titulo_yt": "Cómo Consigue la Gente que Digas 'Sí' a Todo #psicologia",
        "libro_afiliado": "Influencia: La Psicología de la Persuasión",
        "escenas": [
            {"texto": "¿Quieres que alguien acepte un favor grande? Empieza pidiendo algo ridículamente pequeño.", "prompt": "foot in dark doorway cinematic 8k"},
            {"texto": "Su cerebro aceptará por inercia para mantener la coherencia interna.", "prompt": "domino effect falling in shadows 8k"},
            {"texto": "Cuando quieras acordarte, habrá aceptado tus condiciones sin rechistar.", "prompt": "puppet strings shadow dark 8k"},
            {"texto": "Desbloquea las técnicas prohibidas de negociación en el enlace fijado.", "prompt": "locked leather diary dark aesthetic"}
        ]
    },
    "8. Leer el lenguaje corporal": {
        "cabecera": "DETECTA LA VERDAD OCULTA",
        "titulo_yt": "Lo que Sus Pies Dicen de Ti (Lenguaje Corporal Oculto) #shorts",
        "libro_afiliado": "El Cuerpo Habla (Joe Navarro)",
        "escenas": [
            {"texto": "La cara puede mentir a la perfección, pero los pies jamás lo hacen.", "prompt": "feet stepping on dark floor dramatic light 8k"},
            {"texto": "Si alguien apunta con los pies hacia la salida, desea marcharte aunque sonría.", "prompt": "person looking at watch dark room 8k"},
            {"texto": "Analiza las microexpresiones y descubre quién te esconde la verdad.", "prompt": "close up eyes detective dark 8k"},
            {"texto": "Conviértete en un experto leyendo personas con el libro del comentario fijado.", "prompt": "magnifying glass over dark text book"}
        ]
    }
}

# ==============================================================================
# LÓGICA AUDIOVISUAL
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
# ENVÍO A TELEGRAM
# ==============================================================================
def enviar_video_telegram(video_path, titulo_yt, libro, link):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Faltan los datos de Telegram en los Secrets.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    
    caption = (
        f"🧠 <b>¡NUEVO VÍDEO DE PSICOLOGÍA LISTO!</b>\n\n"
        f"📌 <b>Título:</b> {titulo_yt}\n"
        f"📖 <b>Libro afiliado:</b> {libro}\n\n"
        f"🔗 <b>Enlace afiliado:</b> {link}\n\n"
        f"<i>Descarga este vídeo y súbelo a TikTok y YouTube Shorts.</i>"
    )

    print("📲 Enviando vídeo a Telegram...")
    try:
        with open(video_path, "rb") as vid:
            response = requests.post(
                url,
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": caption,
                    "parse_mode": "HTML"
                },
                files={"video": vid},
                timeout=120
            )
        if response.status_code == 200:
            print("✅ ¡Vídeo enviado a Telegram con éxito!")
            return True
        else:
            print(f"❌ Error de Telegram: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Excepción enviando a Telegram: {e}")
        return False

# ==============================================================================
# EJECUCIÓN PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    historial = cargar_historial()
    pendientes = [k for k in PACK_GUIONES.keys() if k not in historial]
    
    if not pendientes:
        print("ℹ️ Historial reiniciado.")
        open(ARCHIVO_HISTORIAL, 'w').close()
        pendientes = list(PACK_GUIONES.keys())
        
    clave_elegida = random.choice(pendientes)
    datos = PACK_GUIONES[clave_elegida]
    
    # 1. Renderizar vídeo
    ruta_mp4 = producir_video(clave_elegida, datos)
    
    # 2. Enviar a Telegram
    enviar_video_telegram(ruta_mp4, datos["titulo_yt"], datos["libro_afiliado"], LINK_AFILIADO)
    
    # 3. Guardar historial
    guardar_historial(clave_elegida)
    print("🎉 Proceso completado.")
