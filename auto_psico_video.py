import os
import sys
import time
import random
import asyncio
import urllib.parse
import requests
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from moviepy.editor import VideoClip, AudioFileClip

from instagrapi import Client
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ARCHIVO_HISTORIAL = "historial_videos.txt"

# Enlace directo de Gumroad con el código de descuento automático
LINK_LIBRO = "https://tankecabeza.gumroad.com/l/arquitectura-mente/OFERTA"

# Estilo común para todas las imágenes generadas con IA
ESTILO_IMAGEN = (
    "cinematic vertical photo, dramatic lighting, dark moody atmosphere, "
    "psychology and human behavior theme, highly detailed, sharp focus, "
    "no text, no letters, no watermark"
)

# ==============================================================================
# MEGA BASE DE DATOS DE 50 GUIONES COMPLETOS
# ==============================================================================
PACK_GUIONES = {
    "1. Trucos contra manipuladores": {
        "cabecera": "3 TRUCOS DE PSICOLOGÍA OSCURA",
        "titulo_yt": "3 Trucos de Psicología Oscura para Dominar Cualquier Situación #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si alguien te falta al respeto en público, aplica este truco inmediatamente."},
            {"texto": "Uno: mírale a los ojos en silencio durante cuatro segundos. Destruirás su seguridad."},
            {"texto": "Dos: pregúntale con voz calmada si se encuentra bien. Quedará en evidencia frente a todos."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "2. Detectar mentiras FBI": {
        "cabecera": "TÉCNICAS DEL FBI",
        "titulo_yt": "Cómo Saber si te Mienten en 5 Segundos según el FBI #Shorts #Psicologia",
        "escenas": [
            {"texto": "Así descubres a un mentiroso en menos de cinco segundos según exagentes del FBI."},
            {"texto": "Si repite exactamente tu pregunta antes de responder, está ganando tiempo para inventar."},
            {"texto": "Pídele que cuente la historia en orden inverso. Los mentirosos siempre se bloquean."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "3. El Efecto Escasez": {
        "cabecera": "LA LEY DEL DESAPEGO",
        "titulo_yt": "Por Qué Cuanto Más Das, Menos Te Valoran (Ley de Escasez) #Shorts #Psicologia",
        "escenas": [
            {"texto": "Deja de estar siempre disponible al instante para todo el mundo."},
            {"texto": "El cerebro humano desprecia lo abundante y se obsesiona con lo escaso."},
            {"texto": "Retira tu atención en silencio cuando no te valoren y empezarán a buscarte."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "4. Triangulación Visual": {
        "cabecera": "EL TRUCO DE LA MIRADA",
        "titulo_yt": "El Truco Visual para Seducir o Intimidar en Segundos #Shorts #LenguajeCorporal",
        "escenas": [
            {"texto": "Usa la mirada triangular para controlar lo que otra persona siente al hablar contigo."},
            {"texto": "Para generar atracción: mira a su ojo izquierdo, luego al derecho y baja a sus labios."},
            {"texto": "Para imponer respeto: mira a sus ojos y sube al centro de su frente. Desactivará su ego."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "5. El Efecto Halo": {
        "cabecera": "EL SESGO DE LA BELLEZA",
        "titulo_yt": "Por Qué la Gente Atractiva lo Tiene Más Fácil (Efecto Halo) #Shorts #Curiosidades",
        "escenas": [
            {"texto": "El efecto Halo es el sesgo inconsciente más poderoso de la mente humana."},
            {"texto": "En solo medio segundo, tu cerebro asume que alguien bien vestido es más honesto y capaz."},
            {"texto": "Incluso en los tribunales, los acusados con buena presencia reciben penas un veinte por ciento menores."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "6. Gaslighting Sutil": {
        "cabecera": "MANIPULACIÓN ENCUBIERTA",
        "titulo_yt": "Si Alguien te Dice Estas 3 Frases, Te Está Manipulando #Shorts #PsicologiaOscura",
        "escenas": [
            {"texto": "El luz de gas o gaslighting es la técnica de manipulación más destructiva que existe."},
            {"texto": "Si te repiten frases como: estás loco, eres demasiado sensible o eso nunca pasó..."},
            {"texto": "Están reescribiendo tu memoria poco a poco para que dependas de su versión de la realidad."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "7. Efecto Zeigarnik": {
        "cabecera": "OBSESIÓN PSICOLÓGICA",
        "titulo_yt": "El Truco Psicológico para que Alguien No Pueda Olvidarte #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si quieres que alguien no deje de pensar en ti, aplica el Efecto Zeigarnik."},
            {"texto": "Nuestra mente borra lo que ya ha terminado, pero se queda atrapada en lo que queda a medias."},
            {"texto": "Termina la conversación en su punto más alto y su cerebro te recordará todo el día."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "8. Los pies no mienten": {
        "cabecera": "LENGUAJE CORPORAL OCULTO",
        "titulo_yt": "Lo que Sus Pies Revelan de Sus Intenciones Ocultas #Shorts #LenguajeCorporal",
        "escenas": [
            {"texto": "El rostro humano está entrenado para fingir, pero los pies siempre dicen la verdad."},
            {"texto": "Si hablas con alguien y sus pies apuntan hacia la puerta, quiere irse aunque te sonría."},
            {"texto": "Si cruza los tobillos debajo de la silla en una negociación, está ocultando información."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "9. Paradoja de la Elección": {
        "cabecera": "POR QUÉ DUDAS TANTO",
        "titulo_yt": "La Regla de 3 para Tomar Decisiones sin Estrés #Shorts #DesarrolloPersonal",
        "escenas": [
            {"texto": "Tener demasiadas opciones no te hace más libre, te hace más infeliz."},
            {"texto": "Se llama Paradoja de la Elección: a partir de cinco alternativas, tu cerebro entra en fatiga."},
            {"texto": "Para decidir como un estratega, descarta todo rápido y quédate solo con tres caminos."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "10. Técnica del Espejo": {
        "cabecera": "EL HACK DE LA EMPATÍA",
        "titulo_yt": "Cómo Caerle Bien a Cualquier Persona en 10 Segundos #Shorts #Persuasion",
        "escenas": [
            {"texto": "¿Quieres ganarte la confianza de un desconocido en menos de un minuto?"},
            {"texto": "Imita con dos segundos de retraso su postura, la velocidad al hablar y sus gestos."},
            {"texto": "Sus neuronas espejo se activarán y sentirá una conexión inexplicable contigo."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "11. El Efecto Franklin": {
        "cabecera": "CONVIERTE ENEMIGOS EN ALIADOS",
        "titulo_yt": "El Efecto Ben Franklin: Cómo Hacer que un Enemigo te Aprecie #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si alguien te tiene manía sin motivo, no intentes hacerle un favor. Pídeselo tú a él."},
            {"texto": "Pídele algo minúsculo, como que te preste un bolígrafo o te dé un consejo rápido."},
            {"texto": "Su cerebro resolverá la disonancia cognitiva convenciéndose de que en realidad le caes bien."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "12. El Anclaje en Negociación": {
        "cabecera": "PSICOLOGÍA DEL DINERO",
        "titulo_yt": "El Truco del Anclaje que Usan los Negociadores Expertos #Shorts #Negocios",
        "escenas": [
            {"texto": "En cualquier negociación, la primera cifra que se dice en voz alta gana la partida."},
            {"texto": "Se llama Sesgo de Anclaje: el cerebro usa el primer número como referencia absoluta."},
            {"texto": "Si pides primero algo elevado, la contraoferta siempre será mucho más alta de lo normal."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "13. El Efecto Pratfall": {
        "cabecera": "EL PODER DE LA IMPERFECCIÓN",
        "titulo_yt": "Por Qué Ser Demasiado Perfecto Hace que la Gente Desconfíe #Shorts #Psicologia",
        "escenas": [
            {"texto": "Intentar parecer perfecto todo el tiempo genera rechazo y envidia en los demás."},
            {"texto": "Según la psicología, cometer un pequeño error torpe en público dispara tu carisma."},
            {"texto": "Se llama Efecto Pratfall: muestras humanidad y haces que los demás se sientan cómodos."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "14. Bombardeo de Amor": {
        "cabecera": "LA TRAMPA NARCISISTA",
        "titulo_yt": "Qué es el Love Bombing y Cómo Detectarlo a Tiempo #Shorts #Relaciones",
        "escenas": [
            {"texto": "Desconfía de quien te promete amor eterno y te llena de regalos en la primera semana."},
            {"texto": "Los perfiles narcisistas usan el bombardeo de afecto para crear adicción a su validación."},
            {"texto": "En cuanto estés enganchado, retirarán todo el cariño de golpe para tener el control."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "15. La Regla de los 3 Segundos": {
        "cabecera": "DOMINA EL CARISMA",
        "titulo_yt": "La Pausa de 3 Segundos que usan los Líderes Más Carismáticos #Shorts #Liderazgo",
        "escenas": [
            {"texto": "Las personas más respetadas nunca responden al instante cuando les hacen una pregunta."},
            {"texto": "Hacen una pausa de dos a tres segundos mirando al interlocutor antes de hablar."},
            {"texto": "Ese breve silencio demuestra calma absoluta y hace que cada palabra parezca oro."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "16. Psicología del Color Rojo": {
        "cabecera": "PSICOLOGÍA DEL COLOR",
        "titulo_yt": "Cómo los Colores que Vistes Manipulan a Quienes te Rodean #Shorts #Curiosidades",
        "escenas": [
            {"texto": "El color que llevas puesto altera el pulso cardíaco de las personas que te miran."},
            {"texto": "El azul marino proyecta autoridad y lealtad; por eso se usa en juicios y bancos."},
            {"texto": "El negro impone distancia y poder, mientras que el rojo activa la urgencia y atracción."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "17. El Efecto Pigmalión": {
        "cabecera": "LA PROFECÍA AUTOCUMPLIDA",
        "titulo_yt": "Cómo las Expectativas de los Demás Cambian tu Rendimiento #Shorts #Motivacion",
        "escenas": [
            {"texto": "Trata a un hombre como lo que es y seguirá igual; trátalo como puede llegar a ser y se transformará."},
            {"texto": "El Efecto Pigmalión demuestra que rendimos según lo que creemos que esperan de nosotros."},
            {"texto": "Aléjate de quienes dudan de tu capacidad, porque tu subconsciente absorberá sus límites."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "18. La Técnica del Disco Rayado": {
        "cabecera": "CÓMO DECIR QUE NO",
        "titulo_yt": "La Técnica Psicológica para Decir 'No' sin Sentirte Culpable #Shorts #Psicologia",
        "escenas": [
            {"texto": "Cuando dices que no, el error más grave que puedes cometer es dar excusas largas."},
            {"texto": "Un manipulador usará tus propias excusas como puntos débiles para seguir insistiendo."},
            {"texto": "Repite la misma frase corta y tranquila una y otra vez. Se quedarán sin munición."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "19. El Efecto Dunning-Kruger": {
        "cabecera": "LA PARADOJA DE LA IGNORANCIA",
        "titulo_yt": "Por Qué los Más Ignorantes son los Más Ruidosos #Shorts #Psicologia",
        "escenas": [
            {"texto": "Cuanto menos sabe una persona sobre un tema, más segura está de tener toda la razón."},
            {"texto": "Se conoce como efecto Dunning-Kruger: la ignorancia da una confianza ciega."},
            {"texto": "Por el contrario, las mentes más brillantes suelen dudar porque conocen la complejidad real."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "20. Microexpresión de Desprecio": {
        "cabecera": "LA SEÑAL MÁS PELIGROSA",
        "titulo_yt": "El Gesto de 1 Segundo que Delata a un Falso Amigo #Shorts #LenguajeCorporal",
        "escenas": [
            {"texto": "Existe un gesto facial que dura menos de medio segundo y predice la traición."},
            {"texto": "Si al contar un logro tuyo, alguien levanta solo una comisura de los labios..."},
            {"texto": "Es la microexpresión universal del desprecio y la envidia. Nunca falla."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "21. Ley de Parkinson": {
        "cabecera": "HACKEA TU PRODUCTIVIDAD",
        "titulo_yt": "Por Qué Postergas Todo hasta el Último Minuto (Ley de Parkinson) #Shorts",
        "escenas": [
            {"texto": "Si te das una semana para hacer un trabajo de dos horas, tardarás exactamente una semana."},
            {"texto": "La Ley de Parkinson dicta que el trabajo se expande hasta ocupar todo el tiempo disponible."},
            {"texto": "Ponte plazos artificialmente cortos y verás cómo tu enfoque se multiplica por diez."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "22. La Mirada al Mentón": {
        "cabecera": "PSICOLOGÍA DEL LIDERAZGO",
        "titulo_yt": "Qué Pasa Cuando Subes el Mentón 2 Centímetros al Hablar #Shorts #Carisma",
        "escenas": [
            {"texto": "En situaciones de tensión, tu cuello revela instantáneamente tu rango en el grupo."},
            {"texto": "Cuando tenemos miedo, bajamos la barbilla por instinto para proteger la garganta."},
            {"texto": "Mantener el mentón ligeramente elevado envía una señal biológica de calma y liderazgo."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "23. El Sesgo del Costo Hundido": {
        "cabecera": "LA TRAMPA DE NO SOLTAR",
        "titulo_yt": "El Error Psicológico que te Mantiene en Malas Decisiones #Shorts #Psicologia",
        "escenas": [
            {"texto": "¿Por qué nos cuesta tanto abandonar un mal negocio o una relación que ya no funciona?"},
            {"texto": "Tu cerebro odia admitir que el tiempo y esfuerzo que ya invertiste se han perdido."},
            {"texto": "Los grandes estrategas no miran lo que ya costó, solo evalúan lo que les costará seguir ahí."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "24. El Secreto de los Cuentos": {
        "cabecera": "EL PODER DE LAS HISTORIAS",
        "titulo_yt": "Por Qué una Buena Historia Convence Más que Mil Datos #Shorts #Persuasion",
        "escenas": [
            {"texto": "Cuando das datos fríos, el cerebro de quien te escucha activa sus barreras críticas."},
            {"texto": "Pero cuando cuentas una historia, su mente baja la guardia y libera oxitocina."},
            {"texto": "Quien domina el arte de contar historias, domina las emociones de los demás."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "25. Técnica de la Confusión": {
        "cabecera": "CÓMO GANAR DISCUSIONES",
        "titulo_yt": "La Técnica Psicológica para Desarmar a Alguien que te Grita #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si alguien te está gritando o atacando verbalmente, no te defiendas."},
            {"texto": "Míralo fijamente a la frente y haz una pregunta totalmente fuera de contexto."},
            {"texto": "Pregunta algo como: ¿Llevas los zapatos desatados? Su cerebro se reiniciará por la confusión."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "26. Ilusión de Alternativa": {
        "cabecera": "MANIPULACIÓN INVISIBLE",
        "titulo_yt": "El Truco para que Siempre Hagan lo que Tú Quieres #Shorts #Persuasion",
        "escenas": [
            {"texto": "Nunca preguntes a alguien si quiere hacer algo, dale dos opciones que te beneficien a ti."},
            {"texto": "En lugar de decir: ¿Nos vemos hoy?, di: ¿Prefieres vernos a las cinco o a las seis?"},
            {"texto": "Su cerebro elegirá la opción más cómoda, olvidando que podía haber dicho que no."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "27. Refuerzo Intermitente": {
        "cabecera": "LA TRAMPA TÓXICA",
        "titulo_yt": "Por Qué te Obsesionas con Quien te Ignora #Shorts #Relaciones",
        "escenas": [
            {"texto": "El refuerzo intermitente es la misma técnica que usan las máquinas tragaperras para crear adicción."},
            {"texto": "Si alguien te da mucha atención un día y te ignora al siguiente, tu cerebro libera dopamina por la incertidumbre."},
            {"texto": "Terminas obsesionándote no por amor, sino por adicción química a su validación."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "28. Efecto Espectador": {
        "cabecera": "PSICOLOGÍA SOCIAL",
        "titulo_yt": "Si Estás en Peligro, NUNCA Pidas Ayuda Así #Shorts #Supervivencia",
        "escenas": [
            {"texto": "Si tienes una emergencia en la calle, no grites pidiendo ayuda al aire."},
            {"texto": "Por el Efecto Espectador, todos pensarán que alguien más intervendrá y nadie hará nada."},
            {"texto": "Señala a una persona específica y dale una orden: Tú, el de la chaqueta azul, llama a emergencias."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "29. El Toque de Midas": {
        "cabecera": "HACK DE CONFIANZA",
        "titulo_yt": "El Contacto Físico de 1 Segundo que Multiplica tu Carisma #Shorts #LenguajeCorporal",
        "escenas": [
            {"texto": "Un roce de un segundo en el antebrazo de la otra persona aumenta la confianza en un sesenta por ciento."},
            {"texto": "La psicología lo llama el Toque de Midas. Humaniza la interacción instantáneamente."},
            {"texto": "Úsalo al pedir un favor o cerrar un trato, pero siempre de forma muy sutil y rápida."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "30. Efecto Forer": {
        "cabecera": "POR QUÉ CREES EN HORÓSCOPOS",
        "titulo_yt": "El Truco Psicológico detrás de los Videntes y Horóscopos #Shorts #Curiosidades",
        "escenas": [
            {"texto": "El Efecto Forer explica por qué crees que tu horóscopo siempre acierta."},
            {"texto": "Aceptamos descripciones vagas y generales como si fueran personalizadas solo para nosotros."},
            {"texto": "Si te dicen: 'A veces eres sociable, pero otras necesitas tu espacio', creerás que te están leyendo la mente."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "31. Ley de Reciprocidad": {
        "cabecera": "CÓMO CONSEGUIR FAVORES",
        "titulo_yt": "El Truco para que Alguien Sienta que te Debe un Favor #Shorts #Persuasion",
        "escenas": [
            {"texto": "Si quieres que alguien haga algo por ti, hazle tú un pequeño favor no solicitado primero."},
            {"texto": "La neurociencia demuestra que el ser humano odia estar en deuda social con otros."},
            {"texto": "Sentirá una presión psicológica inmensa por devolverte el favor cuando se lo pidas."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "32. Triángulo de Karpman": {
        "cabecera": "PERSONAS TÓXICAS",
        "titulo_yt": "Aléjate de Quien Juega a ser la Víctima (Triángulo Dramático) #Shorts",
        "escenas": [
            {"texto": "Cuidado con las personas que siempre se quejan de que el mundo está contra ellos."},
            {"texto": "Te arrastrarán a jugar el papel de Salvador para que les resuelvas la vida."},
            {"texto": "En cuanto dejes de complacerles, te convertirán en el Perseguidor y el malo de su historia."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "33. Técnica BYAF": {
        "cabecera": "TRIPLICA TUS VENTAS",
        "titulo_yt": "Usa estas 5 Palabras para Triplicar tus Posibilidades de un SÍ #Shorts",
        "escenas": [
            {"texto": "Existe una técnica psicológica que duplica la probabilidad de que te digan que sí."},
            {"texto": "Se llama BYAF por sus siglas en inglés: Pero Eres Libre De Elegir."},
            {"texto": "Al recordarle a la persona que tiene total libertad, reduces su mecanismo de defensa a cero."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "34. Efecto de Arrastre": {
        "cabecera": "MANIPULACIÓN DE MASAS",
        "titulo_yt": "Por Qué Haces Cosas que No Quieres Solo Porque Otros lo Hacen #Shorts",
        "escenas": [
            {"texto": "Tu cerebro está programado biológicamente para encajar en la tribu."},
            {"texto": "El Efecto de Arrastre hace que ignores tu propia lógica si ves a la mayoría haciendo otra cosa."},
            {"texto": "Es el sesgo exacto que usan las marcas para poner 'El más vendido' y que compres sin pensar."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "35. Falso Reflejo Pupilar": {
        "cabecera": "LENGUAJE DE LA ATRACCIÓN",
        "titulo_yt": "Cómo Saber si le Gustas a Alguien Mirando sus Pupilas #Shorts #Amor",
        "escenas": [
            {"texto": "Cuando miramos algo o a alguien que nos resulta muy atractivo, nuestras pupilas se dilatan."},
            {"texto": "Es una respuesta del sistema nervioso autónomo imposible de falsificar."},
            {"texto": "Si sus ojos se ven más oscuros y grandes al mirarte en un lugar iluminado, le gustas."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "36. Postura de Poder": {
        "cabecera": "HACKEA TU CEREBRO",
        "titulo_yt": "Haz esta Postura 2 Minutos para Eliminar el Miedo #Shorts #Confianza",
        "escenas": [
            {"texto": "Tu cuerpo no solo refleja cómo te sientes, también puede cambiar tus hormonas."},
            {"texto": "Párate con los brazos en jarra y las piernas separadas durante dos minutos."},
            {"texto": "Esta postura reduce el cortisol, la hormona del estrés, y dispara tu nivel de testosterona."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "37. El Pie en la Puerta": {
        "cabecera": "TÉCNICA DE PERSUASIÓN",
        "titulo_yt": "Cómo Lograr que Alguien te Diga que SÍ a un Gran Favor #Shorts",
        "escenas": [
            {"texto": "Nunca pidas un favor enorme de entrada porque activas las defensas de la otra persona."},
            {"texto": "Pide primero un favor diminuto que sea imposible de rechazar."},
            {"texto": "Una vez que hayan aceptado lo pequeño, su cerebro se compromete y aceptará el favor grande."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "38. Efecto Spotlight": {
        "cabecera": "ANSIEDAD SOCIAL",
        "titulo_yt": "Por Qué Crees que Todos te Miran (Y Por Qué es Mentira) #Shorts #Ansiedad",
        "escenas": [
            {"texto": "¿Sientes que todos te juzgan cuando entras a un sitio o cometes un pequeño error?"},
            {"texto": "Es el Efecto Spotlight. Tu cerebro magnifica cuánta atención te prestan los demás."},
            {"texto": "La realidad es que el noventa por ciento de la gente está demasiado preocupada por sí misma."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "39. Paradoja de Abilene": {
        "cabecera": "DINÁMICAS DE GRUPO",
        "titulo_yt": "Por Qué los Grupos Toman Decisiones Estúpidas #Shorts #PsicologiaSocial",
        "escenas": [
            {"texto": "A veces un grupo de personas hace un plan que en realidad ninguno de ellos quería hacer."},
            {"texto": "Se llama Paradoja de Abilene. Ocurre porque todos creen que los demás quieren hacerlo y callan."},
            {"texto": "No tengas miedo a ser el único en decir que no. Probablemente muchos piensen como tú."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "40. Sesgo de Confirmación": {
        "cabecera": "EL ENGAÑO DE LA MENTE",
        "titulo_yt": "Por Qué Discutir con un Fanático es Perder el Tiempo #Shorts #Psicologia",
        "escenas": [
            {"texto": "Es biológicamente imposible convencer con datos lógicos a alguien radicalizado."},
            {"texto": "El sesgo de confirmación hace que su cerebro solo procese la información que le da la razón."},
            {"texto": "Cualquier prueba en contra la ignorarán o la usarán para enfadarse aún más."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "41. Principio de Contraste": {
        "cabecera": "TRAMPAS DE VENTAS",
        "titulo_yt": "El Truco que Usan las Tiendas para que Gastes Más Dinero #Shorts",
        "escenas": [
            {"texto": "Si compras un traje caro, el vendedor siempre te ofrecerá la corbata después, nunca antes."},
            {"texto": "Por el Principio de Contraste, el cerebro ve cincuenta dólares como poco dinero tras gastar quinientos."},
            {"texto": "Hackean tu percepción matemática manipulando el orden en que te presentan los precios."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "42. Efecto de Mera Exposición": {
        "cabecera": "EL SECRETO DE LA ATRACCIÓN",
        "titulo_yt": "Cómo Hacer que Alguien se Enamore de ti por Repetición #Shorts #Amor",
        "escenas": [
            {"texto": "Cuanto más vemos una cara, más atractiva y confiable nos empieza a parecer."},
            {"texto": "Se llama Efecto de Mera Exposición. Es la razón por la que la publicidad repite los anuncios."},
            {"texto": "Aparecer de forma constante y sutil en la vida de alguien dispara su afinidad hacia ti."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "43. Condicionamiento Clásico": {
        "cabecera": "CREA ANCLAJES EMOCIONALES",
        "titulo_yt": "Cómo Hackear el Cerebro de Alguien Usando un Perfume #Shorts",
        "escenas": [
            {"texto": "Puedes condicionar a una persona para que asocie una emoción positiva a tu presencia."},
            {"texto": "Usa siempre el mismo perfume o gesto físico cuando se estén riendo a carcajadas contigo."},
            {"texto": "Meses después, solo con oler ese aroma, su cerebro liberará endorfinas automáticamente."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "44. El Vínculo Traumático": {
        "cabecera": "RELACIONES TÓXICAS",
        "titulo_yt": "Por Qué Duele Tanto Soltar a Quien te Hace Daño #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si no puedes alejarte de quien te maltrata emocionalmente, no eres débil."},
            {"texto": "Estás bajo un Vínculo Traumático. El ciclo de abuso segrega tanta adrenalina que altera tu química cerebral."},
            {"texto": "Es un síndrome real de abstinencia, exactamente igual que dejar una droga dura."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "45. Ley de Atracción (Proximidad)": {
        "cabecera": "EL PODER DE LA DISTANCIA",
        "titulo_yt": "El Contacto Físico y la Distancia Zonal para Conquistar #Shorts",
        "escenas": [
            {"texto": "Entrar en el espacio íntimo de alguien, a menos de medio metro, activa alarmas biológicas."},
            {"texto": "Pero si lo haces un segundo y retrocedes de inmediato, generas una tensión magnética."},
            {"texto": "Se llama baile de proxemia. Es el arma de seducción más silenciosa y efectiva que existe."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "46. Sesgo de Supervivencia": {
        "cabecera": "EL ENGAÑO DEL ÉXITO",
        "titulo_yt": "Por Qué No Debes Escuchar los Consejos de los Millonarios #Shorts",
        "escenas": [
            {"texto": "Si copias la rutina matutina de un millonario, no te harás millonario."},
            {"texto": "Es el Sesgo de Supervivencia: solo vemos a los pocos que triunfaron, no a los miles que fracasaron."},
            {"texto": "El éxito a menudo requiere mucha más suerte y contexto del que te quieren vender."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "47. Reactancia Psicológica": {
        "cabecera": "PSICOLOGÍA INVERSA",
        "titulo_yt": "Cómo Hacer que Alguien Haga Exactamente lo que Tú Quieres #Shorts",
        "escenas": [
            {"texto": "El ser humano tiene una necesidad biológica de proteger su libertad de elección."},
            {"texto": "Si le prohíbes algo a alguien de forma tajante, sentirá un deseo incontrolable de hacerlo."},
            {"texto": "Usa la reactancia a tu favor desafiando sus capacidades: Apuesto a que no eres capaz de hacerlo."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "48. Técnica del Bostezo": {
        "cabecera": "TEST DE EMPATÍA OCULTO",
        "titulo_yt": "Cómo Saber Quién te Está Mirando Disimuladamente en Grupo #Shorts",
        "escenas": [
            {"texto": "¿Quieres saber si alguien del grupo te está observando cuando no miras?"},
            {"texto": "Finge un bostezo enorme y exagerado. Y acto seguido mira a esa persona."},
            {"texto": "El bostezo es tan contagioso que, si te estaba mirando, bostezará inevitablemente."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "49. Efecto Zeigarnik en el Amor": {
        "cabecera": "EL ARTE DEL MISTERIO",
        "titulo_yt": "Por Qué Ser Demasiado Claro al Principio Mata la Atracción #Shorts",
        "escenas": [
            {"texto": "Si revelas todos tus sentimientos en la primera cita, aburrirás al cerebro del otro."},
            {"texto": "A la mente le fascinan los puzzles sin resolver. Debes dejar que adivinen un poco."},
            {"texto": "Retírate siempre antes de que la conversación muera. Les dejarás queriendo más."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
        ]
    },
    "50. El Poder de los Nombres": {
        "cabecera": "EL SONIDO MÁS DULCE",
        "titulo_yt": "La Palabra Mágica que Desbloquea la Confianza de Cualquiera #Shorts",
        "escenas": [
            {"texto": "Para cualquier persona, el sonido más importante de todo el idioma es su propio nombre."},
            {"texto": "Pronunciar su nombre al principio o al final de una frase capta su atención inconsciente al instante."},
            {"texto": "Aumenta tu carisma y dominancia usando el nombre de los demás de forma estratégica."},
            {"texto": "Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil."}
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
# AUDIO Y TIEMPOS
# ==============================================================================
async def generar_audio_y_tiempos(escenas, ruta_out):
    tiempos_textos = []
    tiempo_actual = 0.0
    carpeta = "render_tmp"
    os.makedirs(carpeta, exist_ok=True)

    voz = "es-ES-ElviraNeural"

    ruta_silencio = os.path.join(carpeta, "silence.wav")
    os.system(f"ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 0.2 -q:a 9 -acodec pcm_s16le {ruta_silencio} -y -hide_banner -loglevel error")

    with open("temp_list.txt", "w") as f_list:
        for i, esc in enumerate(escenas):
            ruta_mp3 = os.path.join(carpeta, f"voz_{i}.mp3")
            comunicador = edge_tts.Communicate(esc["texto"], voz, rate="+5%")
            await comunicador.save(ruta_mp3)

            audio_clip = AudioFileClip(ruta_mp3)
            dur = audio_clip.duration

            tiempos_textos.append((tiempo_actual, tiempo_actual + dur, esc["texto"]))
            tiempo_actual += dur + 0.2

            ruta_wav = os.path.join(carpeta, f"voz_{i}.wav")
            audio_clip.write_audiofile(ruta_wav, logger=None)
            audio_clip.close()
            f_list.write(f"file '{ruta_wav}'\n")
            f_list.write(f"duration {dur}\n")
            f_list.write(f"file '{ruta_silencio}'\n")
            f_list.write(f"duration 0.2\n")

    os.system(f"ffmpeg -f concat -safe 0 -i temp_list.txt -c copy {ruta_out} -y -hide_banner -loglevel error")

    return tiempos_textos

# ==============================================================================
# IMÁGENES CON IA (Pollinations, gratis y sin clave)
# ==============================================================================
def crear_fondo_respaldo(ruta, semilla):
    """Degradado oscuro por si falla la IA, para que el vídeo nunca se rompa."""
    rnd = random.Random(semilla)
    c1 = np.array([rnd.randint(10, 60), rnd.randint(10, 40), rnd.randint(40, 110)], dtype=float)
    c2 = np.array([rnd.randint(0, 25), rnd.randint(0, 25), rnd.randint(0, 40)], dtype=float)
    grad = np.linspace(0, 1, 1920).reshape(-1, 1, 1)
    arr = (c1 * (1 - grad) + c2 * grad) * np.ones((1920, 1080, 3))
    Image.fromarray(arr.astype("uint8")).save(ruta, "JPEG", quality=92)

def descargar_imagen_ia(prompt, ruta, semilla):
    prompt = prompt[:380]
    url = (
        "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
        + f"?width=1080&height=1920&model=flux&nologo=true&seed={semilla}"
    )
    for intento in range(3):
        try:
            r = requests.get(url, timeout=150)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                with open(ruta, "wb") as f:
                    f.write(r.content)
                Image.open(ruta).convert("RGB").save(ruta, "JPEG", quality=92)
                return True
            print(f"    ⚠️ Respuesta {r.status_code} de la IA de imágenes (intento {intento + 1})")
        except Exception as e:
            print(f"    ⚠️ Error de imagen (intento {intento + 1}): {e}")
        time.sleep(6 * (intento + 1))
    return False

def generar_imagenes(escenas, cabecera):
    carpeta = "render_tmp"
    rutas = []
    base_seed = random.randint(1, 10_000_000)
    for i, esc in enumerate(escenas):
        ruta = os.path.join(carpeta, f"img_{i}.jpg")
        descripcion = esc.get("img") or f"{cabecera.lower()}, {esc['texto']}"
        prompt = f"{descripcion}. {ESTILO_IMAGEN}"
        print(f"🖼️ Generando imagen {i + 1}/{len(escenas)}...", flush=True)
        ok = descargar_imagen_ia(prompt, ruta, base_seed + i)
        if not ok:
            print("    ↪ Usando fondo de respaldo.")
            crear_fondo_respaldo(ruta, base_seed + i)
        rutas.append(ruta)
        time.sleep(3)
    return rutas

# ==============================================================================
# SUBTÍTULOS
# ==============================================================================
def dibujar_subtitulos(frame, t, tiempos_textos, cabecera):
    img = Image.fromarray(frame).resize((1080, 1920), Image.LANCZOS).convert("RGBA")
    capa = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    dr_capa = ImageDraw.Draw(capa)

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

    bbox_c = draw.textbbox((0, 0), cabecera, font=f_cab)
    draw.text(((1080 - (bbox_c[2] - bbox_c[0])) / 2, 95), cabecera, font=f_cab, fill="#FFE600", stroke_width=4, stroke_fill="#000000")

    texto_actual = ""
    for inicio, fin, txt in tiempos_textos:
        if inicio <= t <= (fin + 0.2):
            texto_actual = txt
            break

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

# ==============================================================================
# PRODUCCIÓN DEL VÍDEO (imágenes IA + zoom suave + voz + subtítulos)
# ==============================================================================
def producir_video_imagenes(clave, datos):
    print(f"🎬 Iniciando producción con IMÁGENES IA: {clave}", flush=True)
    os.makedirs("render_tmp", exist_ok=True)
    audio_maestro = "render_tmp/audio_maestro.wav"

    tiempos_textos = asyncio.run(generar_audio_y_tiempos(datos["escenas"], audio_maestro))
    rutas_img = generar_imagenes(datos["escenas"], datos["cabecera"])
    imagenes = [Image.open(p).convert("RGB").resize((1080, 1920), Image.LANCZOS) for p in rutas_img]

    audio = AudioFileClip(audio_maestro)
    dur_total = audio.duration
    inicios = [t[0] for t in tiempos_textos]
    n = len(inicios)
    cabecera = datos["cabecera"]

    def make_frame(t):
        idx = 0
        for i in range(n):
            if inicios[i] <= t:
                idx = i
        ini = inicios[idx]
        fin = inicios[idx + 1] if idx + 1 < n else dur_total
        prog = min(max((t - ini) / max(fin - ini, 0.1), 0.0), 1.0)
        # Zoom suave: entra en las escenas pares, sale en las impares
        z = 1.0 + 0.12 * prog if idx % 2 == 0 else 1.12 - 0.12 * prog
        w, h = 1080 / z, 1920 / z
        izq, arr = (1080 - w) / 2, (1920 - h) / 2
        recorte = imagenes[idx].crop((izq, arr, izq + w, arr + h)).resize((1080, 1920), Image.BILINEAR)
        return dibujar_subtitulos(np.array(recorte), t, tiempos_textos, cabecera)

    print("✍️ Montando vídeo con subtítulos sincronizados...")
    video = VideoClip(make_frame, duration=dur_total).set_audio(audio)

    mp4_out = "render_tmp/VIDEO_FINAL.mp4"
    video.write_videofile(
        mp4_out, fps=24, codec="libx264", audio_codec="aac",
        preset="veryfast", ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None
    )
    return mp4_out

# ==============================================================================
# PUBLICACIÓN: TELEGRAM
# ==============================================================================
def enviar_pack_telegram(video_path, titulo_yt):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Faltan credenciales de Telegram. Omitiendo.")
        return False

    titulo_yt_limpio = titulo_yt[:100].strip()
    descripcion_yt = (
        f"¿Quieres dominar tu mente y entender el comportamiento humano?\n\n"
        f"📕 Descarga mi manual 'Arquitectura de la Mente Invisible' y "
        f"aprende a protegerte de la manipulación:\n👉 {LINK_LIBRO}\n\n"
        f"#psicologia #psicologiaoscura #lenguajecorporal #persuasion #manipulacion"
    )
    descripcion_tiktok = (
        f"{titulo_yt_limpio} 🧠 Descarga mi libro Arquitectura de la Mente Invisible en el enlace de mi perfil 🔗 "
        f"#psicologia #psicologiaoscura #lenguajecorporal"
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
            f"📋 <b>TOCA CADA CAJA PARA COPIARLA:</b>\n\n"
            f"1️⃣ <b>TÍTULO YOUTUBE SHORTS:</b>\n<code>{titulo_yt_limpio}</code>\n\n"
            f"2️⃣ <b>DESCRIPCIÓN YOUTUBE:</b>\n<code>{descripcion_yt}</code>\n\n"
            f"3️⃣ <b>DESCRIPCIÓN TIKTOK:</b>\n<code>{descripcion_tiktok}</code>"
        )
        requests.post(url_msg, data={"chat_id": TELEGRAM_CHAT_ID, "text": texto_copiable, "parse_mode": "HTML"}, timeout=30)
        print("✅ ¡Vídeo y textos enviados a Telegram!")
        return True
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")
        return False

# ==============================================================================
# PUBLICACIÓN: INSTAGRAM REELS
# ==============================================================================
def publicar_instagram_reel(video_path, titulo_yt):
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
        f"📕 Descarga mi manual 'Arquitectura de la Mente Invisible' y "
        f"aprende a protegerte de la manipulación:\n👉 {LINK_LIBRO}\n\n"
        f"#psicologia #psicologiaoscura #lenguajecorporal #persuasion #manipulacion #desarrollopersonal #shorts"
    )

    print("📱 Conectando a Instagram mediante sesión inyectada...")
    try:
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
                "custom_accessibility_caption": "Vídeo de psicología y comportamiento humano con imágenes ilustrativas.",
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
# PUBLICACIÓN: YOUTUBE SHORTS
# ==============================================================================
def publicar_youtube_short(video_path, titulo_yt):
    YT_CLIENT_ID = os.getenv("YT_CLIENT_ID")
    YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
    YT_REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")

    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]):
        print("⚠️ Faltan credenciales de YouTube en los Secrets. Omitiendo.")
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
            f"📕 Descarga mi manual 'Arquitectura de la Mente Invisible' y "
            f"aprende a protegerte de la manipulación:\n👉 {LINK_LIBRO}\n\n"
            f"#psicologia #psicologiaoscura #lenguajecorporal #persuasion #manipulacion #desarrollopersonal #shorts"
        )
        body = {
            "snippet": {
                "title": titulo_yt,
                "description": descripcion_yt,
                "tags": ["psicologia", "shorts", "psicologia oscura", "desarrollo personal"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

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
# MAIN
# ==============================================================================
if __name__ == "__main__":
    historial = cargar_historial()
    pendientes = [k for k in PACK_GUIONES if k not in historial]

    if not pendientes:
        print("🔄 Se completaron los 50 guiones. Reiniciando ciclo.")
        open(ARCHIVO_HISTORIAL, "w").close()
        pendientes = list(PACK_GUIONES.keys())

    clave_elegida = random.choice(pendientes)
    datos = PACK_GUIONES[clave_elegida]

    ruta_mp4 = producir_video_imagenes(clave_elegida, datos)

    # Publicación orientada a ventas propias
    exito_telegram = enviar_pack_telegram(ruta_mp4, datos["titulo_yt"])
    exito_ig = publicar_instagram_reel(ruta_mp4, datos["titulo_yt"])
    exito_yt = publicar_youtube_short(ruta_mp4, datos["titulo_yt"])

    if exito_telegram or exito_ig or exito_yt:
        guardar_historial(clave_elegida)
        print("🎉 Proceso completado con éxito.")
    else:
        print("⚠️ Hubo un fallo en la distribución.")
