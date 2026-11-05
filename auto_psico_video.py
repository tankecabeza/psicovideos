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
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeAudioClip,
    CompositeVideoClip, concatenate_videoclips,
)

# Imports para YouTube API
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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
# MEGA BASE DE DATOS DE GUIONES (24 TEMÁTICAS VARIADAS)
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
    "2. Detectar mentiras FBI": {
        "cabecera": "TÉCNICAS DEL FBI",
        "titulo_yt": "Cómo Saber si te Mienten en 5 Segundos según el FBI #Shorts #Psicologia",
        "escenas": [
            {"texto": "Así descubres a un mentiroso en menos de cinco segundos según exagentes del FBI.", "prompt": "dark interrogation room single hanging lamp cinematic"},
            {"texto": "Si repite exactamente tu pregunta antes de responder, está ganando tiempo para inventar.", "prompt": "nervous man sweating in dark shadow portrait"},
            {"texto": "Pídele que cuente la historia en orden inverso. Los mentirosos siempre se bloquean.", "prompt": "king chess piece falling on board dramatic lighting"},
            {"texto": "Descubre los manuales de lectura corporal en los enlaces de la descripción.", "prompt": "top secret dossier folder on dark wooden table"}
        ]
    },
    "3. El Efecto Escasez": {
        "cabecera": "LA LEY DEL DESAPEGO",
        "titulo_yt": "Por Qué Cuanto Más Das, Menos Te Valoran (Ley de Escasez) #Shorts #Psicologia",
        "escenas": [
            {"texto": "Deja de estar siempre disponible al instante para todo el mundo.", "prompt": "lone man walking away foggy street night neon"},
            {"texto": "El cerebro humano desprecia lo abundante y se obsesiona con lo escaso.", "prompt": "luxury gold pocket watch on black velvet"},
            {"texto": "Retira tu atención en silencio cuando no te valoren y empezarán a buscarte.", "prompt": "confident man silhouette looking out skyscraper window night"},
            {"texto": "Domina las leyes de la persuasión con los libros recomendados en la descripción.", "prompt": "open book glowing with warm golden light in dark library"}
        ]
    },
    "4. Triangulación Visual": {
        "cabecera": "EL TRUCO DE LA MIRADA",
        "titulo_yt": "El Truco Visual para Seducir o Intimidar en Segundos #Shorts #LenguajeCorporal",
        "escenas": [
            {"texto": "Usa la mirada triangular para controlar lo que otra persona siente al hablar contigo.", "prompt": "sharp eyes closeup dark moody portrait photography"},
            {"texto": "Para generar atracción: mira a su ojo izquierdo, luego al derecho y baja a sus labios.", "prompt": "romantic silhouette couple dim neon lighting aesthetic"},
            {"texto": "Para imponer respeto: mira a sus ojos y sube al centro de su frente. Desactivará su ego.", "prompt": "cold serious stare businessman dark background"},
            {"texto": "Aprende todos los secretos del lenguaje corporal en el enlace de la descripción.", "prompt": "mysterious mask on dark marble table"}
        ]
    },
    "5. El Efecto Halo": {
        "cabecera": "EL SESGO DE LA BELLEZA",
        "titulo_yt": "Por Qué la Gente Atractiva lo Tiene Más Fácil (Efecto Halo) #Shorts #Curiosidades",
        "escenas": [
            {"texto": "El efecto Halo es el sesgo inconsciente más poderoso de la mente humana.", "prompt": "silhouette with glowing halo light dark background"},
            {"texto": "En solo medio segundo, tu cerebro asume que alguien bien vestido es más honesto y capaz.", "prompt": "elegant man adjusting tie in dark luxury hallway"},
            {"texto": "Incluso en los tribunales, los acusados con buena presencia reciben penas un veinte por ciento menores.", "prompt": "wooden gavel on dark judge desk dramatic shadow"},
            {"texto": "Hackea los sesgos de tu mente con los audiolibros gratis de la descripción.", "prompt": "glowing human brain digital art dark background"}
        ]
    },
    "6. Gaslighting Sutil": {
        "cabecera": "MANIPULACIÓN ENCUBIERTA",
        "titulo_yt": "Si Alguien te Dice Estas 3 Frases, Te Está Manipulando #Shorts #PsicologiaOscura",
        "escenas": [
            {"texto": "El luz de gas o gaslighting es la técnica de manipulación más destructiva que existe.", "prompt": "person holding head in hands dark foggy room"},
            {"texto": "Si te repiten frases como: estás loco, eres demasiado sensible o eso nunca pasó...", "prompt": "shadow of menacing figure on dark wall"},
            {"texto": "Están reescribiendo tu memoria poco a poco para que dependas de su versión de la realidad.", "prompt": "cracked mirror reflecting distorted face in dark"},
            {"texto": "Aprende a blindar tu mente contra manipuladores en el enlace de la descripción.", "prompt": "heavy iron padlock on old book dark mood"}
        ]
    },
    "7. Efecto Zeigarnik": {
        "cabecera": "OBSESIÓN PSICOLÓGICA",
        "titulo_yt": "El Truco Psicológico para que Alguien No Pueda Olvidarte #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si quieres que alguien no deje de pensar en ti, aplica el Efecto Zeigarnik.", "prompt": "person looking at phone screen in dark bedroom night"},
            {"texto": "Nuestra mente borra lo que ya ha terminado, pero se queda atrapada en lo que queda a medias.", "prompt": "jigsaw puzzle missing final piece dark table"},
            {"texto": "Termina la conversación en su punto más alto y su cerebro te recordará todo el día.", "prompt": "silhouette walking into dark mist streetlight"},
            {"texto": "Descubre más leyes del comportamiento humano en los libros de la descripción.", "prompt": "hourglass with golden sand in dark room"}
        ]
    },
    "8. Los pies no mienten": {
        "cabecera": "LENGUAJE CORPORAL OCULTO",
        "titulo_yt": "Lo que Sus Pies Revelan de Sus Intenciones Ocultas #Shorts #LenguajeCorporal",
        "escenas": [
            {"texto": "El rostro humano está entrenado para fingir, pero los pies siempre dicen la verdad.", "prompt": "leather shoes on dark wet street reflection"},
            {"texto": "Si hablas con alguien y sus pies apuntan hacia la puerta, quiere irse aunque te sonría.", "prompt": "two people standing in hallway focus on shoes shadow"},
            {"texto": "Si cruza los tobillos debajo de la silla en una negociación, está ocultando información.", "prompt": "person sitting on chair in dark office ankles crossed"},
            {"texto": "Domina los seis libros del lenguaje corporal en el enlace de la descripción.", "prompt": "magnifying glass over old book pages dark"}
        ]
    },
    "9. Paradoja de la Elección": {
        "cabecera": "POR QUÉ DUDAS TANTO",
        "titulo_yt": "La Regla de 3 para Tomar Decisiones sin Estrés #Shorts #DesarrolloPersonal",
        "escenas": [
            {"texto": "Tener demasiadas opciones no te hace más libre, te hace más infeliz.", "prompt": "person standing in front of many doors dark corridor"},
            {"texto": "Se llama Paradoja de la Elección: a partir de cinco alternativas, tu cerebro entra en fatiga.", "prompt": "overwhelmed man in dark room surrounded by screens"},
            {"texto": "Para decidir como un estratega, descarta todo rápido y quédate solo con tres caminos.", "prompt": "three glowing paths in dark forest night"},
            {"texto": "Entrena tu enfoque mental con los audiolibros recomendados en la descripción.", "prompt": "compass on dark map candlelight"}
        ]
    },
    "10. Técnica del Espejo": {
        "cabecera": "EL HACK DE LA EMPATÍA",
        "titulo_yt": "Cómo Caerle Bien a Cualquier Persona en 10 Segundos #Shorts #Persuasion",
        "escenas": [
            {"texto": "¿Quieres ganarte la confianza de un desconocido en menos de un minuto?", "prompt": "two businessmen shaking hands in dark luxury lounge"},
            {"texto": "Imita con dos segundos de retraso su postura, la velocidad al hablar y sus gestos.", "prompt": "reflection in dark water surface moody"},
            {"texto": "Sus neuronas espejo se activarán y sentirá una conexión inexplicable contigo.", "prompt": "glowing neural network connection dark background"},
            {"texto": "Tienes la guía maestra de persuasión en los enlaces de la descripción.", "prompt": "silver key on dark velvet cushion"}
        ]
    },
    "11. El Efecto Franklin": {
        "cabecera": "CONVIERTE ENEMIGOS EN ALIADOS",
        "titulo_yt": "El Efecto Ben Franklin: Cómo Hacer que un Enemigo te Aprecie #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si alguien te tiene manía sin motivo, no intentes hacerle un favor. Pídeselo tú a él.", "prompt": "two rivals facing each other dark chess game"},
            {"texto": "Pídele algo minúsculo, como que te preste un bolígrafo o te dé un consejo rápido.", "prompt": "fountain pen on dark mahogany desk"},
            {"texto": "Su cerebro resolverá la disonancia cognitiva convenciéndose de que en realidad le caes bien.", "prompt": "scales of balance in dark moody lighting"},
            {"texto": "Aprende psicología aplicada en los libros y audiolibros de la descripción.", "prompt": "old portrait painting style dark library"}
        ]
    },
    "12. El Anclaje en Negociación": {
        "cabecera": "PSICOLOGÍA DEL DINERO",
        "titulo_yt": "El Truco del Anclaje que Usan los Negociadores Expertos #Shorts #Negocios",
        "escenas": [
            {"texto": "En cualquier negociación, la primera cifra que se dice en voz alta gana la partida.", "prompt": "boardroom table dark moody skyscraper view"},
            {"texto": "Se llama Sesgo de Anclaje: el cerebro usa el primer número como referencia absoluta.", "prompt": "heavy ship anchor underwater dark blue abyss"},
            {"texto": "Si pides primero algo elevado, la contraoferta siempre será mucho más alta de lo normal.", "prompt": "stack of gold coins in dark shadow"},
            {"texto": "Domina el arte de negociar con los libros recomendados en la descripción.", "prompt": "briefcase on dark leather chair"}
        ]
    },
    "13. El Efecto Pratfall": {
        "cabecera": "EL PODER DE LA IMPERFECCIÓN",
        "titulo_yt": "Por Qué Ser Demasiado Perfecto Hace que la Gente Desconfíe #Shorts #Psicologia",
        "escenas": [
            {"texto": "Intentar parecer perfecto todo el tiempo genera rechazo y envidia en los demás.", "prompt": "cold marble statue in dark museum"},
            {"texto": "Según la psicología, cometer un pequeño error torpe en público dispara tu carisma.", "prompt": "coffee cup spilling on dark table slow motion"},
            {"texto": "Se llama Efecto Pratfall: muestras humanidad y haces que los demás se sientan cómodos.", "prompt": "charismatic man smiling in dim moody bar"},
            {"texto": "Mejora tu inteligencia social con los libros del enlace en la descripción.", "prompt": "cracked kintsugi bowl with gold veins dark"}
        ]
    },
    "14. Bombardeo de Amor": {
        "cabecera": "LA TRAMPA NARCISISTA",
        "titulo_yt": "Qué es el Love Bombing y Cómo Detectarlo a Tiempo #Shorts #Relaciones",
        "escenas": [
            {"texto": "Desconfía de quien te promete amor eterno y te llena de regalos en la primera semana.", "prompt": "red rose burning in dark room cinematic"},
            {"texto": "Los perfiles narcisistas usan el bombardeo de afecto para crear adicción a su validación.", "prompt": "golden cage in dark room dramatic light"},
            {"texto": "En cuanto estés enganchado, retirarán todo el cariño de golpe para tener el control.", "prompt": "wilted flower on cold stone floor dark"},
            {"texto": "Protege tu paz mental con las guías de psicología de la descripción.", "prompt": "glowing shield emblem in dark mist"}
        ]
    },
    "15. La Regla de los 3 Segundos": {
        "cabecera": "DOMINA EL CARISMA",
        "titulo_yt": "La Pausa de 3 Segundos que usan los Líderes Más Carismáticos #Shorts #Liderazgo",
        "escenas": [
            {"texto": "Las personas más respetadas nunca responden al instante cuando les hacen una pregunta.", "prompt": "leader standing on dark stage spotlight"},
            {"texto": "Hacen una pausa de dos a tres segundos mirando al interlocutor antes de hablar.", "prompt": "watch hands moving closeup dark background"},
            {"texto": "Ese breve silencio demuestra calma absoluta y hace que cada palabra parezca oro.", "prompt": "microphone in dark studio moody lighting"},
            {"texto": "Desarrolla una mentalidad inquebrantable con los audiolibros de la descripción.", "prompt": "mountain peak in dark stormy clouds"}
        ]
    },
    "16. Psicología del Color Rojo": {
        "cabecera": "PSICOLOGÍA DEL COLOR",
        "titulo_yt": "Cómo los Colores que Vistes Manipulan a Quienes te Rodean #Shorts #Curiosidades",
        "escenas": [
            {"texto": "El color que llevas puesto altera el pulso cardíaco de las personas que te miran.", "prompt": "person in red coat walking in dark black and white street"},
            {"texto": "El azul marino proyecta autoridad y lealtad; por eso se usa en juicios y bancos.", "prompt": "dark navy blue suit closeup luxury texture"},
            {"texto": "El negro impone distancia y poder, mientras que el rojo activa la urgencia y atracción.", "prompt": "red neon light reflecting on dark sunglasses"},
            {"texto": "Descubre el libro oficial de la psicología del color en la descripción.", "prompt": "prism splitting light in dark room"}
        ]
    },
    "17. El Efecto Pigmalión": {
        "cabecera": "LA PROFECÍA AUTOCUMPLIDA",
        "titulo_yt": "Cómo las Expectativas de los Demás Cambian tu Rendimiento #Shorts #Motivacion",
        "escenas": [
            {"texto": "Trata a un hombre como lo que es y seguirá igual; trátalo como puede llegar a ser y se transformará.", "prompt": "sculptor carving marble statue in dark studio"},
            {"texto": "El Efecto Pigmalión demuestra que rendimos según lo que creemos que esperan de nosotros.", "prompt": "runner in dark stadium starting block spotlight"},
            {"texto": "Aléjate de quienes dudan de tu capacidad, porque tu subconsciente absorberá sus límites.", "prompt": "chains breaking in dark dramatic lighting"},
            {"texto": "Potencia tu motivación al máximo con los libros de la descripción.", "prompt": "torch fire burning in dark cave"}
        ]
    },
    "18. La Técnica del Disco Rayado": {
        "cabecera": "CÓMO DECIR QUE NO",
        "titulo_yt": "La Técnica Psicológica para Decir 'No' sin Sentirte Culpable #Shorts #Psicologia",
        "escenas": [
            {"texto": "Cuando dices que no, el error más grave que puedes cometer es dar excusas largas.", "prompt": "hand raised stop gesture in dark shadow"},
            {"texto": "Un manipulador usará tus propias excusas como puntos débiles para seguir insistiendo.", "prompt": "chess pieces surrounding a lone king dark"},
            {"texto": "Repite la misma frase corta y tranquila una y otra vez. Se quedarán sin munición.", "prompt": "vinyl record spinning in dark room neon"},
            {"texto": "Aprende asertividad y defensa verbal en los enlaces de la descripción.", "prompt": "fortress wall in dark night fog"}
        ]
    },
    "19. El Efecto Dunning-Kruger": {
        "cabecera": "LA PARADOJA DE LA IGNORANCIA",
        "titulo_yt": "Por Qué los Más Ignorantes son los Más Ruidosos #Shorts #Psicologia",
        "escenas": [
            {"texto": "Cuanto menos sabe una persona sobre un tema, más segura está de tener toda la razón.", "prompt": "man shouting in dark room megaphone shadow"},
            {"texto": "Se conoce como efecto Dunning-Kruger: la ignorancia da una confianza ciega.", "prompt": "blindfolded statue in dark dramatic light"},
            {"texto": "Por el contrario, las mentes más brillantes suelen dudar porque conocen la complejidad real.", "prompt": "old philosopher reading in dark library"},
            {"texto": "Alimenta tu mente cada día con los audiolibros gratis de la descripción.", "prompt": "glowing tree of knowledge dark background"}
        ]
    },
    "20. Microexpresión de Desprecio": {
        "cabecera": "LA SEÑAL MÁS PELIGROSA",
        "titulo_yt": "El Gesto de 1 Segundo que Delata a un Falso Amigo #Shorts #LenguajeCorporal",
        "escenas": [
            {"texto": "Existe un gesto facial que dura menos de medio segundo y predice la traición.", "prompt": "half face in shadow dramatic portrait dark"},
            {"texto": "Si al contar un logro tuyo, alguien levanta solo una comisura de los labios...", "prompt": "subtle smirk closeup in dark lighting"},
            {"texto": "Es la microexpresión universal del desprecio y la envidia. Nunca falla.", "prompt": "snake hidden in dark grass moody"},
            {"texto": "Aprende a leer cada gesto humano con el pack de libros de la descripción.", "prompt": "human face wireframe scan dark screen"}
        ]
    },
    "21. Ley de Parkinson": {
        "cabecera": "HACKEA TU PRODUCTIVIDAD",
        "titulo_yt": "Por Qué Postergas Todo hasta el Último Minuto (Ley de Parkinson) #Shorts",
        "escenas": [
            {"texto": "Si te das una semana para hacer un trabajo de dos horas, tardarás exactamente una semana.", "prompt": "clock melting in dark room surreal"},
            {"texto": "La Ley de Parkinson dicta que el trabajo se expande hasta ocupar todo el tiempo disponible.", "prompt": "man working late at night dark desk laptop glow"},
            {"texto": "Ponte plazos artificialmente cortos y verás cómo tu enfoque se multiplica por diez.", "prompt": "stopwatch ticking closeup dark background"},
            {"texto": "Domina tu disciplina y motivación con los libros de la descripción.", "prompt": "metronome in dark room dramatic light"}
        ]
    },
    "22. La Mirada al Mentón": {
        "cabecera": "PSICOLOGÍA DEL LIDERAZGO",
        "titulo_yt": "Qué Pasa Cuando Subes el Mentón 2 Centímetros al Hablar #Shorts #Carisma",
        "escenas": [
            {"texto": "En situaciones de tensión, tu cuello revela instantáneamente tu rango en el grupo.", "prompt": "man in dark suit looking up confident shadow"},
            {"texto": "Cuando tenemos miedo, bajamos la barbilla por instinto para proteger la garganta.", "prompt": "boxer in dark ring guard up dramatic"},
            {"texto": "Mantener el mentón ligeramente elevado envía una señal biológica de calma y liderazgo.", "prompt": "lion in the dark looking at camera intense"},
            {"texto": "Descubre los secretos del lenguaje no verbal en la descripción del vídeo.", "prompt": "golden crown on dark stone"}
        ]
    },
    "23. El Sesgo del Costo Hundido": {
        "cabecera": "LA TRAMPA DE NO SOLTAR",
        "titulo_yt": "El Error Psicológico que te Mantiene en Malas Decisiones #Shorts #Psicologia",
        "escenas": [
            {"texto": "¿Por qué nos cuesta tanto abandonar un mal negocio o una relación que ya no funciona?", "prompt": "sinking ship in dark stormy ocean painting"},
            {"texto": "Tu cerebro odia admitir que el tiempo y esfuerzo que ya invertiste se han perdido.", "prompt": "burning money in dark ashtray moody"},
            {"texto": "Los grandes estrategas no miran lo que ya costó, solo evalúan lo que les costará seguir ahí.", "prompt": "scissors cutting a red thread in the dark"},
            {"texto": "Aprende a pensar con claridad con los libros recomendados en la descripción.", "prompt": "lighthouse beam in dark night sea"}
        ]
    },
    "24. El Secreto de los Cuentos": {
        "cabecera": "EL PODER DE LAS HISTORIAS",
        "titulo_yt": "Por Qué una Buena Historia Convence Más que Mil Datos #Shorts #Persuasion",
        "escenas": [
            {"texto": "Cuando das datos fríos, el cerebro de quien te escucha activa sus barreras críticas.", "prompt": "cold computer data screen in dark room"},
            {"texto": "Pero cuando cuentas una historia, su mente baja la guardia y libera oxitocina.", "prompt": "campfire in dark forest sparks flying"},
            {"texto": "Quien domina el arte de contar historias, domina las emociones de los demás.", "prompt": "open magical book with glowing particles dark"},
            {"texto": "Explora la psicología a través de las historias en el enlace de la descripción.", "prompt": "lantern glowing on dark wooden path"}
        ]
    }
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
# GENERADOR PROCEDURAL Y DESCARGA IA
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
# AUDIO, SUBTÍTULOS Y PRODUCCIÓN VÍDEO (API 1.0.3)
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

        base = ImageClip(r_sub).set_duration(dur)
        zoom = base.resize(lambda t: 1.0 + 0.032 * t).set_position(("center", "center"))
        escena = CompositeVideoClip([zoom], size=(1080, 1920)).set_duration(dur).set_audio(audio)
        clips.append(escena)

    final = concatenate_videoclips(clips, method="compose")
    r_bgm = os.path.join(carpeta, "bgm.wav")
    crear_musica_fondo(r_bgm, final.duration)
    
    bgm = AudioFileClip(r_bgm).volumex(0.18).set_duration(final.duration)

    mezcla = CompositeAudioClip([final.audio, bgm])
    mp4_out = os.path.join(carpeta, "VIDEO_FINAL.mp4")
    
    final.set_audio(mezcla).write_videofile(
        mp4_out, fps=24, codec="libx264", audio_codec="aac",
        preset="veryfast", ffmpeg_params=["-pix_fmt", "yuv420p", "-crf", "23"], logger=None
    )
    return mp4_out

# ==============================================================================
# ENVÍO A TELEGRAM
# ==============================================================================
def enviar_pack_telegram(video_path, titulo_yt, libro_elegido):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Faltan credenciales de Telegram. Omitiendo.")
        return False

    titulo_yt_limpio = titulo_yt[:100].strip()

    descripcion_yt = (
        f"¿Quieres dominar tu mente y entender el comportamiento humano?\n\n"
        f"🎧 Prueba Audible 30 días GRATIS (Audiolibros ilimitados):\n{LINK_AUDIBLE}\n\n"
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
# ENVÍO A INSTAGRAM
# ==============================================================================
def publicar_instagram_reel(video_path, titulo_yt, libro_elegido):
    INSTA_USER = os.getenv("INSTA_USER")
    INSTA_PASS = os.getenv("INSTA_PASS")
    INSTA_SESSION = os.getenv("INSTA_SESSION")
    
    if not all([INSTA_USER, INSTA_PASS, INSTA_SESSION]):
        print("⚠️ Faltan credenciales de Instagram. Omitiendo.")
        return False

    titulo_limpio = titulo_yt[:100].strip()
    descripcion_ig = (
        f"{titulo_limpio}\n\n"
        f"¿Quieres dominar tu mente y entender el comportamiento humano?\n\n"
        f"🎧 Prueba Audible 30 días GRATIS (Audiolibros ilimitados):\n{LINK_AUDIBLE}\n\n"
        f"📚 Libro recomendado de hoy: {libro_elegido['titulo']}\n"
        f"👉 Consíguelo aquí: {libro_elegido['link']}\n\n"
        f"#publi #psicologia #psicologiaoscura #lenguajecorporal #persuasion #manipulacion #desarrollopersonal #shorts"
    )

    print("📱 Conectando a Instagram mediante sesión inyectada...")
    try:
        from instagrapi import Client
        cl = Client()
        cl.delay_range = [2, 6] 
        
        sesion_guardada = json.loads(INSTA_SESSION)
        cl.settings = sesion_guardada
        cl.set_settings(sesion_guardada)
        
        cl.login(INSTA_USER, INSTA_PASS)
        
        print("🚀 Subiendo Reel a Instagram...")
        cl.clip_upload(
            video_path,
            descripcion_ig,
            extra_data={
                "custom_accessibility_caption": "Vídeo animado de psicología y comportamiento humano.",
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
# ENVÍO AUTOMÁTICO A YOUTUBE SHORTS
# ==============================================================================
def publicar_youtube_short(video_path, titulo_yt, libro_elegido):
    YT_CLIENT_ID = os.getenv("YT_CLIENT_ID")
    YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
    YT_REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")

    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]):
        print("⚠️ Faltan credenciales de YouTube en los Secrets. Omitiendo subida a YouTube.")
        return False

    print("📺 Conectando a YouTube Data API...")
    try:
        creds = Credentials(
            None,
            refresh_token=YT_REFRESH_TOKEN,
            client_id=YT_CLIENT_ID,
            client_secret=YT_CLIENT_SECRET,
            token_uri="https://oauth2.googleapis.com/token"
        )

        youtube = build("youtube", "v3", credentials=creds)

        descripcion_yt = (
            f"¿Quieres dominar tu mente y entender el comportamiento humano?\n\n"
            f"🎧 Prueba Audible 30 días GRATIS (Audiolibros ilimitados):\n{LINK_AUDIBLE}\n\n"
            f"📚 Libro recomendado de hoy: {libro_elegido['titulo']}\n"
            f"👉 Consíguelo aquí: {libro_elegido['link']}\n\n"
            f"#publi #psicologia #psicologiaoscura #lenguajecorporal #persuasion #manipulacion #desarrollopersonal #shorts"
        )

        body = {
            "snippet": {
                "title": titulo_yt,
                "description": descripcion_yt,
                "tags": ["psicologia", "shorts", "psicologia oscura", "desarrollo personal"],
                "categoryId": "27"  # Educación
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"    Subiendo a YouTube: {int(status.progress() * 100)}%")

        print(f"✅ ¡Short publicado con éxito en YouTube! ID: {response.get('id')}")
        return True
    except Exception as e:
        print(f"❌ Error subiendo a YouTube: {e}")
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
    
    # 1. Enviar a Telegram
    exito_telegram = enviar_pack_telegram(ruta_mp4, datos["titulo_yt"], libro_al_azar)
    
    # 2. Publicar en Instagram
    exito_ig = publicar_instagram_reel(ruta_mp4, datos["titulo_yt"], libro_al_azar)

    # 3. Publicar en YouTube Shorts
    exito_yt = publicar_youtube_short(ruta_mp4, datos["titulo_yt"], libro_al_azar)
    
    # Guarda en el historial si al menos una plataforma procesó el vídeo con éxito
    if exito_telegram or exito_ig or exito_yt:
        guardar_historial(clave_elegida)
        print("🎉 Proceso completado con éxito.")
    else:
        print("⚠️ Hubo un fallo general en la distribución. No se marca como publicado.")
