import os
import sys
import time
import random
import asyncio
import urllib.parse
import html
import requests
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import edge_tts
from moviepy.editor import VideoClip, AudioFileClip

from instagrapi import Client
from instagrapi.types import StoryLink
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ARCHIVO_HISTORIAL = "historial_videos.txt"

# Enlaces de promoción del libro
LINK_LIBRO = "https://tankecabeza.gumroad.com/l/arquitectura-mente/OFERTA"
LINK_CORTO = "https://bit.ly/4AkPY0T"
RUTA_PORTADA = "portada.jpg"

ESTILO_IMAGEN = (
    "cinematic vertical photo, dramatic lighting, dark moody atmosphere, "
    "psychology and human behavior theme, highly detailed, sharp focus, "
    "no text, no letters, no watermark"
)

# ==============================================================================
# BASE DE DATOS DE GUIONES (Corregidos y respaldados científicamente)
# ==============================================================================
PACK_GUIONES = {
    "1. Defensa contra manipuladores": {
        "cabecera": "3 TÉCNICAS DE DEFENSA MENTAL",
        "titulo_yt": "3 Técnicas para Desarmar a Quien Intenta Intimidarte #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si alguien te falta al respeto en público, prueba esta técnica de asertividad."},
            {"texto": "Uno: mantén el contacto visual en silencio durante unos segundos. Romperás su inercia agresiva."},
            {"texto": "Dos: pregúntale con voz calmada si se encuentra bien. Desplazarás la presión hacia su comportamiento."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "2. Detectar mentiras": {
        "cabecera": "PSICOLOGÍA DEL ENGAÑO",
        "titulo_yt": "Cómo Detectar Incongruencias al Escuchar una Historia #Shorts #Psicologia",
        "escenas": [
            {"texto": "Detectar mentiras no es magia, se basa en analizar la sobrecarga cognitiva."},
            {"texto": "Si alguien repite tu pregunta antes de responder, podría estar ganando tiempo para elaborar el engaño."},
            {"texto": "Pídele que cuente un detalle en orden inverso. Al requerir más esfuerzo mental, las historias falsas suelen desmoronarse."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "3. El Efecto Escasez": {
        "cabecera": "LA LEY DEL DESAPEGO",
        "titulo_yt": "Por Qué Cuanto Más Das, Menos Te Valoran (Ley de Escasez) #Shorts #Psicologia",
        "escenas": [
            {"texto": "Deja de estar siempre disponible al instante para todo el mundo."},
            {"texto": "El cerebro humano tiende a normalizar lo abundante y a valorar más lo escaso."},
            {"texto": "Proteger tu tiempo y tu atención es el primer paso para que los demás también los respeten."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "4. Triangulación Visual": {
        "cabecera": "EL TRUCO DE LA MIRADA",
        "titulo_yt": "El Truco Visual para Mostrar Seguridad al Hablar #Shorts #LenguajeCorporal",
        "escenas": [
            {"texto": "El triángulo visual que formas con tus ojos determina el tono de la conversación."},
            {"texto": "Una mirada social recorre los ojos y la boca, generando cercanía e interés."},
            {"texto": "Pero si quieres proyectar autoridad, mantén la mirada en el triángulo entre sus ojos y su frente."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "5. El Efecto Halo": {
        "cabecera": "EL SESGO DE LA BELLEZA",
        "titulo_yt": "Por Qué la Gente Atractiva lo Tiene Más Fácil (Efecto Halo) #Shorts #Curiosidades",
        "escenas": [
            {"texto": "El efecto Halo es uno de los sesgos cognitivos más potentes de la mente humana."},
            {"texto": "Nuestra mente asume que si alguien tiene un rasgo positivo, como ser atractivo, también será más honesto o capaz."},
            {"texto": "Incluso en los tribunales, los acusados con buena presencia tienden a recibir juicios más favorables."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "6. Gaslighting Sutil": {
        "cabecera": "MANIPULACIÓN ENCUBIERTA",
        "titulo_yt": "Si Alguien te Dice Estas 3 Frases, Te Está Manipulando #Shorts #PsicologiaOscura",
        "escenas": [
            {"texto": "El luz de gas o gaslighting es la técnica de manipulación más destructiva que existe."},
            {"texto": "Si te repiten frases como: estás loco, eres demasiado sensible o eso nunca pasó..."},
            {"texto": "Están reescribiendo tu memoria poco a poco para que dependas de su versión de la realidad."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "7. Efecto Zeigarnik": {
        "cabecera": "OBSESIÓN PSICOLÓGICA",
        "titulo_yt": "El Truco Psicológico para que Alguien No Pueda Olvidarte #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si quieres que alguien no deje de pensar en ti, aplica el Efecto Zeigarnik."},
            {"texto": "Nuestra mente archiva lo que ya ha terminado, pero se queda procesando lo que queda a medias."},
            {"texto": "Termina la conversación en un punto alto y su cerebro tenderá a recordarte más tiempo."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "8. Los pies no mienten": {
        "cabecera": "LENGUAJE CORPORAL OCULTO",
        "titulo_yt": "Lo que Sus Pies Revelan de Sus Intenciones Ocultas #Shorts #LenguajeCorporal",
        "escenas": [
            {"texto": "Estamos entrenados para controlar la expresión del rostro, pero solemos olvidar los pies."},
            {"texto": "Si hablas con alguien y sus pies apuntan hacia la puerta, es probable que desee marcharse."},
            {"texto": "Es una respuesta instintiva del sistema nervioso para prepararnos para la acción o la huida."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "9. Paradoja de la Elección": {
        "cabecera": "POR QUÉ DUDAS TANTO",
        "titulo_yt": "La Regla de 3 para Tomar Decisiones sin Estrés #Shorts #DesarrolloPersonal",
        "escenas": [
            {"texto": "Tener demasiadas opciones no te hace más libre, te genera fatiga decisional."},
            {"texto": "Se llama Paradoja de la Elección: cuantas más alternativas, más ansiedad por miedo a equivocarnos."},
            {"texto": "Para decidir de forma eficiente, descarta lo irrelevante y quédate solo con tres opciones finales."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "10. Técnica del Espejo": {
        "cabecera": "EL HACK DE LA EMPATÍA",
        "titulo_yt": "Cómo Conectar Rápido con Cualquier Persona #Shorts #Persuasion",
        "escenas": [
            {"texto": "¿Quieres generar confianza con un desconocido de forma natural?"},
            {"texto": "Sincroniza sutilmente tu lenguaje corporal, igualando su tono de voz o postura."},
            {"texto": "Este reflejo activa las neuronas espejo y fomenta una sensación inconsciente de familiaridad."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "11. El Efecto Franklin": {
        "cabecera": "CONVIERTE ENEMIGOS EN ALIADOS",
        "titulo_yt": "El Efecto Ben Franklin: Cómo Hacer que te Aprecien Más #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si quieres mejorar la relación con alguien distante, no le hagas un favor. Pídeselo tú a él."},
            {"texto": "Pídele algo minúsculo, como que te preste un bolígrafo o te dé una opinión."},
            {"texto": "Por disonancia cognitiva, su cerebro justificará la ayuda asumiendo que en el fondo le caes bien."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "12. El Anclaje en Negociación": {
        "cabecera": "PSICOLOGÍA DEL DINERO",
        "titulo_yt": "El Truco del Anclaje que Usan los Negociadores Expertos #Shorts #Negocios",
        "escenas": [
            {"texto": "En cualquier negociación, la primera cifra que se dice condiciona todo el proceso."},
            {"texto": "Se llama Sesgo de Anclaje: el cerebro usa ese primer dato como punto de referencia absoluto."},
            {"texto": "Establecer la cifra inicial te da el control de las expectativas de la otra parte."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "13. El Efecto Pratfall": {
        "cabecera": "EL PODER DE LA IMPERFECCIÓN",
        "titulo_yt": "Por Qué Ser Demasiado Perfecto Genera Desconfianza #Shorts #Psicologia",
        "escenas": [
            {"texto": "Intentar parecer infalible todo el tiempo suele generar distancia emocional con los demás."},
            {"texto": "La psicología muestra que admitir un pequeño error nos hace parecer más humanos y accesibles."},
            {"texto": "Se llama Efecto Pratfall: mostrar vulnerabilidad hace que los demás se sientan cómodos a tu lado."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "14. Bombardeo de Amor": {
        "cabecera": "LA TRAMPA NARCISISTA",
        "titulo_yt": "Qué es el Love Bombing y Cómo Detectarlo a Tiempo #Shorts #Relaciones",
        "escenas": [
            {"texto": "Presta atención si alguien te promete amor eterno y devoción absoluta en la primera semana."},
            {"texto": "Muchos perfiles manipuladores usan el bombardeo de afecto para crear dependencia rápida."},
            {"texto": "Una vez forjado el vínculo, el afecto desaparece para dar paso al control y la exigencia."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "15. La Regla de los 3 Segundos": {
        "cabecera": "DOMINA EL CARISMA",
        "titulo_yt": "La Pausa de 3 Segundos que usan los Líderes Más Carismáticos #Shorts #Liderazgo",
        "escenas": [
            {"texto": "Las personas más respetadas evitan reaccionar impulsivamente a las preguntas difíciles."},
            {"texto": "Hacen una pausa de dos o tres segundos, respiran y mantienen el contacto visual."},
            {"texto": "Ese breve silencio demuestra autocontrol y dota de mayor peso a sus palabras."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "16. Psicología del Color Rojo": {
        "cabecera": "PSICOLOGÍA DEL COLOR",
        "titulo_yt": "Cómo los Colores que Vistes Afectan tu Percepción #Shorts #Curiosidades",
        "escenas": [
            {"texto": "El color que vistes tiene un impacto sutil pero real en cómo te perciben los demás."},
            {"texto": "El azul oscuro proyecta estabilidad y rigor profesional, ideal para entornos formales."},
            {"texto": "El rojo, en cambio, está asociado evolutivamente a la dominancia, el dinamismo y la atracción."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "17. El Efecto Pigmalión": {
        "cabecera": "LA PROFECÍA AUTOCUMPLIDA",
        "titulo_yt": "Cómo las Expectativas de los Demás Cambian tu Rendimiento #Shorts #Motivacion",
        "escenas": [
            {"texto": "Las personas tienden a rendir al nivel de las expectativas que se tienen sobre ellas."},
            {"texto": "El Efecto Pigmalión demuestra que creer en la capacidad de alguien mejora sus resultados reales."},
            {"texto": "Rodéate de personas que confíen en ti, porque tu entorno modela tus propios límites."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "18. La Técnica del Disco Rayado": {
        "cabecera": "CÓMO DECIR QUE NO",
        "titulo_yt": "La Técnica Psicológica para Decir 'No' sin Sentirte Culpable #Shorts #Psicologia",
        "escenas": [
            {"texto": "Cuando necesites establecer un límite, evita dar excusas largas y detalladas."},
            {"texto": "Un interlocutor insistente usará esas excusas para intentar convencerte de lo contrario."},
            {"texto": "Usa la técnica del disco rayado: repite tu negativa de forma breve, amable y firme."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "19. El Efecto Dunning-Kruger": {
        "cabecera": "LA PARADOJA DE LA IGNORANCIA",
        "titulo_yt": "Por Qué Quien Menos Sabe Suele Ser Quien Más Habla #Shorts #Psicologia",
        "escenas": [
            {"texto": "Las personas con menos habilidades en un área tienden a sobreestimar su capacidad real."},
            {"texto": "Se conoce como efecto Dunning-Kruger: la falta de conocimientos impide ver los propios errores."},
            {"texto": "Por el contrario, los verdaderos expertos suelen dudar más, porque conocen la complejidad del tema."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "20. Microexpresión de Desprecio": {
        "cabecera": "LA SEÑAL MÁS PELIGROSA",
        "titulo_yt": "El Gesto que Puede Delatar Superioridad o Desprecio #Shorts #LenguajeCorporal",
        "escenas": [
            {"texto": "Las emociones verdaderas a veces escapan en gestos faciales que duran fracciones de segundo."},
            {"texto": "Si al contar un logro, alguien eleva solo una comisura de los labios de forma asimétrica..."},
            {"texto": "Suele ser la microexpresión universal del desprecio o la superioridad moral. Obsérvalo con atención."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "21. Ley de Parkinson": {
        "cabecera": "HACKEA TU PRODUCTIVIDAD",
        "titulo_yt": "Por Qué Postergas Todo hasta el Último Minuto (Ley de Parkinson) #Shorts",
        "escenas": [
            {"texto": "Si te das una semana para hacer un trabajo de dos horas, probablemente tardes toda la semana."},
            {"texto": "La Ley de Parkinson sostiene que el trabajo se expande hasta agotar el tiempo disponible."},
            {"texto": "Acortar tus plazos de entrega de forma artificial es clave para multiplicar tu concentración."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "22. La Mirada al Mentón": {
        "cabecera": "PSICOLOGÍA DEL LIDERAZGO",
        "titulo_yt": "Cómo Proyectar Seguridad Controlando tu Postura Cervical #Shorts #Carisma",
        "escenas": [
            {"texto": "En situaciones de tensión social, la postura del cuello revela tu nivel de comodidad."},
            {"texto": "Cuando nos sentimos amenazados, tendemos a bajar la barbilla instintivamente para protegernos."},
            {"texto": "Mantener el mentón paralelo al suelo transmite calma, aplomo y seguridad en uno mismo."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "23. El Sesgo del Costo Hundido": {
        "cabecera": "LA TRAMPA DE NO SOLTAR",
        "titulo_yt": "El Error Psicológico que te Mantiene en Malas Decisiones #Shorts #Psicologia",
        "escenas": [
            {"texto": "¿Por qué nos cuesta tanto abandonar un proyecto o relación que claramente ya no funciona?"},
            {"texto": "Es el Sesgo del Costo Hundido: nos duele asumir que el tiempo y esfuerzo invertidos no volverán."},
            {"texto": "La clave está en tomar decisiones basadas en el futuro, no en lo que ya has gastado en el pasado."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "24. El Secreto de los Cuentos": {
        "cabecera": "EL PODER DE LAS HISTORIAS",
        "titulo_yt": "Por Qué una Buena Historia Convence Más que Mil Datos #Shorts #Persuasion",
        "escenas": [
            {"texto": "Cuando presentamos datos fríos, el cerebro del oyente activa sus filtros críticos y analíticos."},
            {"texto": "Pero una buena narrativa envuelve el mensaje en emoción, facilitando la retención del mensaje."},
            {"texto": "Quien sabe estructurar la información en forma de historia, domina el arte de la comunicación."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "25. Técnica de la Confusión": {
        "cabecera": "CÓMO FRENAR DISCUSIONES",
        "titulo_yt": "La Técnica para Desarmar la Agresividad Verbal #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si alguien te alza la voz de forma irracional, entrar en su juego solo escalará el conflicto."},
            {"texto": "Prueba a romper su patrón introduciendo una frase completamente fuera de contexto."},
            {"texto": "El cerebro agresor debe detenerse a procesar la anomalía, lo que a menudo desinfla la tensión inicial."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "26. Ilusión de Alternativa": {
        "cabecera": "DEFENSA CONTRA VENTAS",
        "titulo_yt": "Cómo Detectar Cuándo te Están Forzando a Elegir #Shorts #Persuasion",
        "escenas": [
            {"texto": "En persuasión comercial, rara vez te preguntan si quieres hacer algo. Te dan a elegir el cómo."},
            {"texto": "Por ejemplo: ¿Prefieres que te enviemos el producto el martes o el jueves?"},
            {"texto": "Es la ilusión de alternativa: limitan tus opciones para que olvides que podías simplemente decir que no."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "27. Refuerzo Intermitente": {
        "cabecera": "LA TRAMPA TÓXICA",
        "titulo_yt": "Por Qué te Obsesionas con Quien te Ignora #Shorts #Relaciones",
        "escenas": [
            {"texto": "El refuerzo intermitente es el mismo mecanismo que genera adicción en los juegos de azar."},
            {"texto": "Si alguien te da validación intensa un día y frialdad al siguiente, tu cerebro entra en alerta."},
            {"texto": "Esa montaña rusa de incertidumbre segrega dopamina y puede confundirse erróneamente con amor intenso."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "28. Efecto Espectador": {
        "cabecera": "PSICOLOGÍA SOCIAL",
        "titulo_yt": "Si Estás en Peligro, NUNCA Pidas Ayuda Así #Shorts #Supervivencia",
        "escenas": [
            {"texto": "En una emergencia rodeado de gente, pedir ayuda al aire puede ser contraproducente."},
            {"texto": "El Efecto Espectador hace que la responsabilidad se diluya: todos asumen que actuará otro."},
            {"texto": "Para romper este bloqueo, señala a una persona concreta: Tú, el de la camisa roja, llama a emergencias."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "29. El Toque de Midas": {
        "cabecera": "HACK DE CONFIANZA",
        "titulo_yt": "Cómo el Contacto Físico Sutil Mejora la Receptividad #Shorts #LenguajeCorporal",
        "escenas": [
            {"texto": "Un roce de apenas un segundo en el antebrazo puede aumentar significativamente la receptividad de alguien."},
            {"texto": "En sociología se conoce como el Toque de Midas. Subraya la conexión y humaniza la interacción."},
            {"texto": "Suele funcionar mejor en contextos cordiales y de servicio, siempre respetando el espacio personal."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "30. Efecto Forer": {
        "cabecera": "POR QUÉ CREES EN HORÓSCOPOS",
        "titulo_yt": "El Truco Psicológico detrás de los Videntes y Horóscopos #Shorts #Curiosidades",
        "escenas": [
            {"texto": "El Efecto Forer explica por qué es tan fácil identificarse con textos de astrología o tarot."},
            {"texto": "Nuestro cerebro procesa descripciones genéricas y vagas como si fueran altamente personalizadas."},
            {"texto": "Si te dicen: 'A veces necesitas tu espacio, pero valoras a tus amigos', asumirás que te están leyendo la mente."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "31. Ley de Reciprocidad": {
        "cabecera": "NORMAS SOCIALES INVISIBLES",
        "titulo_yt": "Por Qué Sentimos la Obligación de Devolver Favores #Shorts #Persuasion",
        "escenas": [
            {"texto": "Cuando alguien hace algo por nosotros, incluso sin pedirlo, sentimos una fuerte deuda social."},
            {"texto": "La norma de reciprocidad es un pilar de la cooperación humana desde la prehistoria."},
            {"texto": "Es el motivo por el que en marketing te ofrecen muestras gratuitas: predisponen tu voluntad de compra."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "32. Triángulo de Karpman": {
        "cabecera": "DINÁMICAS TÓXICAS",
        "titulo_yt": "Aléjate de Quien Siempre Juega a ser la Víctima #Shorts",
        "escenas": [
            {"texto": "El Triángulo Dramático de Karpman describe el ciclo de las relaciones conflictivas crónicas."},
            {"texto": "Alguien adopta el rol de Víctima para forzarte a ser su Salvador constante."},
            {"texto": "Pero en cuanto intentes poner límites o dejes de ceder, te convertirán inmediatamente en su Perseguidor."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "33. Técnica BYAF": {
        "cabecera": "REDUCE LA RESISTENCIA",
        "titulo_yt": "Usa estas Palabras para Facilitar que te Digan que SÍ #Shorts",
        "escenas": [
            {"texto": "Para que alguien acepte una propuesta, el primer paso es desactivar su reactancia defensiva."},
            {"texto": "La técnica BYAF consiste en añadir: Pero Eres Libre De Elegir, al final de tu petición."},
            {"texto": "Al devolverle verbalmente el control de la decisión, paradójicamente incrementas las probabilidades de éxito."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "34. Efecto de Arrastre": {
        "cabecera": "MANIPULACIÓN DE MASAS",
        "titulo_yt": "Por Qué Haces Cosas Solo Porque la Mayoría lo Hace #Shorts",
        "escenas": [
            {"texto": "Nuestro cerebro evolucionó para buscar la seguridad del grupo y evitar el aislamiento social."},
            {"texto": "El Efecto Bandwagon hace que a menudo ignoremos nuestra propia lógica para seguir a la masa."},
            {"texto": "Es el mecanismo exacto que usan las marcas al poner la etiqueta de 'El más vendido' en sus productos."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "35. El Lenguaje de las Pupilas": {
        "cabecera": "SEÑALES INVOLUNTARIAS",
        "titulo_yt": "Lo que la Dilatación Pupilar Revela Sobre el Interés #Shorts #Amor",
        "escenas": [
            {"texto": "Aunque la luz ambiental es el factor principal, las pupilas también responden a las emociones."},
            {"texto": "Ante estímulos que nos resultan muy atractivos o estimulantes, el sistema nervioso autónomo las dilata."},
            {"texto": "Una midriasis sutil durante una conversación relajada puede ser un indicador no verbal de interés genuino."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "36. Posturas Expansivas": {
        "cabecera": "HACKEA TU CEREBRO",
        "titulo_yt": "Cómo tu Postura Corporal Cambia tu Sensación de Confianza #Shorts #Confianza",
        "escenas": [
            {"texto": "La conexión mente-cuerpo funciona en ambas direcciones. Tu postura no solo refleja, también moldea tu actitud."},
            {"texto": "Adoptar posturas expansivas y erguidas antes de un evento tenso mejora la autopercepción de competencia."},
            {"texto": "Ocupar espacio físico envía señales de preparación a tu cerebro, reduciendo la sensación de vulnerabilidad."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "37. El Pie en la Puerta": {
        "cabecera": "TÉCNICA DE PERSUASIÓN",
        "titulo_yt": "Cómo Lograr Aceptación Usando el Compromiso Progresivo #Shorts",
        "escenas": [
            {"texto": "Pedir un favor enorme de entrada suele activar las defensas y generar rechazo inmediato."},
            {"texto": "La estrategia del Pie en la Puerta sugiere empezar pidiendo algo minúsculo y fácil de aceptar."},
            {"texto": "Una vez la persona ha accedido a lo pequeño, su necesidad de ser coherente facilita que acepte el favor grande."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "38. Efecto Spotlight": {
        "cabecera": "ANSIEDAD SOCIAL",
        "titulo_yt": "Por Qué Crees que Todos te Miran (Y Por Qué es Falso) #Shorts #Ansiedad",
        "escenas": [
            {"texto": "¿Sientes que todos juzgan tu forma de vestir o ese pequeño error que cometiste en público?"},
            {"texto": "Es el Efecto Spotlight. Nuestro egocentrismo natural magnifica cuánta atención nos prestan los demás."},
            {"texto": "La realidad es liberadora: la inmensa mayoría de la gente está demasiado ocupada pensando en sí misma."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "39. Paradoja de Abilene": {
        "cabecera": "DINÁMICAS DE GRUPO",
        "titulo_yt": "Por Qué los Grupos Toman Decisiones que Nadie Quería #Shorts #PsicologiaSocial",
        "escenas": [
            {"texto": "A veces un grupo ejecuta un plan que, individualmente, ninguno de sus miembros deseaba hacer."},
            {"texto": "Es la Paradoja de Abilene: sucede porque todos creen erróneamente que los demás sí están de acuerdo y prefieren callar."},
            {"texto": "Romper el silencio asertivamente a menudo revela que muchos otros compartían tu misma opinión."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "40. Sesgo de Confirmación": {
        "cabecera": "EL ENGAÑO DE LA MENTE",
        "titulo_yt": "Por Qué Argumentar con Datos Fríos Rara Vez Funciona #Shorts #Psicologia",
        "escenas": [
            {"texto": "Es casi imposible cambiar las creencias arraigadas de alguien usando únicamente la lógica pura."},
            {"texto": "El sesgo de confirmación hace que filtremos los datos para procesar solo aquellos que nos dan la razón."},
            {"texto": "Ante la evidencia en contra, muchas personas se atrincheran aún más en su postura original."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "41. Principio de Contraste": {
        "cabecera": "TRAMPAS DE VENTAS",
        "titulo_yt": "El Sesgo Perceptivo que Usan para que Gastes Más #Shorts",
        "escenas": [
            {"texto": "Si compras un artículo costoso, el vendedor hábil siempre te ofrecerá los accesorios complementarios justo después."},
            {"texto": "Debido al Principio de Contraste, el cerebro percibe cincuenta euros como una cifra menor si acaba de gastar mil."},
            {"texto": "Hackean tu percepción alterando el orden en que evalúas el impacto económico."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "42. Efecto de Mera Exposición": {
        "cabecera": "EL SECRETO DE LA FAMILIARIDAD",
        "titulo_yt": "Por Qué el Roce y la Repetición Generan Atracción #Shorts #Amor",
        "escenas": [
            {"texto": "Cuanto más expuestos estamos a un rostro, un sonido o una idea, más favorable nos suele parecer."},
            {"texto": "Es el Efecto de Mera Exposición, un pilar fundamental en la psicología de la publicidad y la afinidad social."},
            {"texto": "Aparecer de forma constante y amigable genera una preferencia inconsciente basada puramente en la familiaridad."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "43. Condicionamiento Clásico": {
        "cabecera": "CREA ANCLAJES EMOCIONALES",
        "titulo_yt": "Cómo Funciona la Memoria Olfativa y las Emociones #Shorts",
        "escenas": [
            {"texto": "El cerebro asocia rápidamente estímulos sensoriales a estados emocionales intensos."},
            {"texto": "Si siempre llevas el mismo perfume en momentos de gran alegría compartida, estarás creando un anclaje."},
            {"texto": "Tiempo después, el simple hecho de percibir ese aroma puede reactivar emociones positivas de forma casi automática."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "44. El Vínculo Traumático": {
        "cabecera": "RELACIONES TÓXICAS",
        "titulo_yt": "Por Qué Duele Tanto Soltar un Entorno Conflictivo #Shorts #Psicologia",
        "escenas": [
            {"texto": "Si te resulta imposible alejarte de una dinámica abusiva, no es por debilidad de carácter."},
            {"texto": "Los ciclos de castigo y recompensa intensa pueden generar lo que se denomina un Vínculo Traumático."},
            {"texto": "Alteran la química del cerebro creando respuestas biológicas muy similares al síndrome de abstinencia."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "45. Ley de Atracción (Proximidad)": {
        "cabecera": "EL PODER DE LA DISTANCIA",
        "titulo_yt": "Cómo Funciona la Proxemia en la Comunicación Interpersonal #Shorts",
        "escenas": [
            {"texto": "Invadir el espacio íntimo de alguien de forma abrupta activa sus defensas biológicas de inmediato."},
            {"texto": "Sin embargo, acercarse levemente durante un segundo para enfatizar un punto y volver a retroceder..."},
            {"texto": "Es un uso estratégico de la proxemia que genera interés sin llegar a activar la alerta de amenaza."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "46. Sesgo de Supervivencia": {
        "cabecera": "EL ENGAÑO DEL ÉXITO",
        "titulo_yt": "Por Qué Copiar a los Millonarios Rara Vez Funciona #Shorts",
        "escenas": [
            {"texto": "Si replicas la rutina de las personas más ricas del mundo, lo más probable es que no te hagas millonario."},
            {"texto": "Caemos en el Sesgo de Supervivencia: solo analizamos a los que triunfaron, ignorando a los miles que fracasaron haciendo lo mismo."},
            {"texto": "El éxito suele requerir factores sistémicos y contextos que ningún gurú puede venderte en un curso."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "47. Reactancia Psicológica": {
        "cabecera": "PSICOLOGÍA INVERSA",
        "titulo_yt": "Por Qué Prohibir Algo Aumenta el Deseo de Hacerlo #Shorts",
        "escenas": [
            {"texto": "El ser humano protege biológicamente su sensación de libertad y autonomía."},
            {"texto": "Si se nos prohíbe algo de forma tajante, solemos experimentar Reactancia Psicológica, un deseo de recuperar el control."},
            {"texto": "Es la razón por la que advertencias muy restrictivas suelen provocar el comportamiento opuesto al deseado."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "48. El Bostezo Contagioso": {
        "cabecera": "TEST DE EMPATÍA SOCIAL",
        "titulo_yt": "Por Qué el Bostezo nos Ayuda a Conectar en Grupo #Shorts",
        "escenas": [
            {"texto": "El bostezo no es solo un indicador de cansancio, tiene un fuerte componente de empatía y vínculo social."},
            {"texto": "Es tan contagioso que, a menudo, basta con ver a alguien bostezar para que nuestro cuerpo lo replique."},
            {"texto": "Algunos estudios sugieren que sincronizarnos de esta manera ayuda a mantener la cohesión del grupo."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "49. Efecto Zeigarnik en el Amor": {
        "cabecera": "EL ARTE DE LA DOSIFICACIÓN",
        "titulo_yt": "Por Qué Dejar Espacio al Misterio Genera Interés #Shorts",
        "escenas": [
            {"texto": "Revelar absolutamente todos tus pensamientos en una primera interacción puede saturar al interlocutor."},
            {"texto": "A nuestro cerebro le fascinan las historias que aún están por completarse."},
            {"texto": "Dosificar la información y dejar espacio al descubrimiento mutuo mantiene la intriga y fomenta el interés a largo plazo."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
        ]
    },
    "50. El Poder de los Nombres": {
        "cabecera": "EL SONIDO MÁS ATRACTIVO",
        "titulo_yt": "Por Qué Recordar Nombres Mejora tus Relaciones #Shorts",
        "escenas": [
            {"texto": "Para la mayoría de personas, su propio nombre es una de las palabras con mayor carga emocional del idioma."},
            {"texto": "Mencionarlo con naturalidad durante una conversación capta la atención de forma automática y subconsciente."},
            {"texto": "Es un indicador de respeto y memoria que facilita la creación de vínculos sólidos desde el primer momento."},
            {"texto": "Descarga mi libro Arquitectura de la Mente en el enlace de mi perfil."}
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
# IMÁGENES CON IA (LEONARDO -> POLLINATIONS -> RESPALDO)
# ==============================================================================
def crear_fondo_respaldo(ruta, semilla):
    rnd = random.Random(semilla)
    c1 = np.array([rnd.randint(10, 60), rnd.randint(10, 40), rnd.randint(40, 110)], dtype=float)
    c2 = np.array([rnd.randint(0, 25), rnd.randint(0, 25), rnd.randint(0, 40)], dtype=float)
    grad = np.linspace(0, 1, 1920).reshape(-1, 1, 1)
    arr = (c1 * (1 - grad) + c2 * grad) * np.ones((1920, 1080, 3))
    Image.fromarray(arr.astype("uint8")).save(ruta, "JPEG", quality=92)

def descargar_imagen_leonardo(prompt, ruta):
    API_KEY = os.getenv("LEONARDO_API_KEY")
    if not API_KEY:
        return False
    
    print("    🧠 Intentando con Leonardo AI...")
    url_gen = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "height": 1024,
        "width": 576, # Ratio 9:16 nativo para evitar distorsiones
        "prompt": prompt,
        "num_images": 1
    }
    
    try:
        r = requests.post(url_gen, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        gen_id = r.json().get("sdGenerationJob", {}).get("generationId")
        if not gen_id: return False
        
        url_get = f"https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}"
        for _ in range(15):
            time.sleep(4)
            r_get = requests.get(url_get, headers=headers, timeout=30)
            status = r_get.json().get("generations_by_pk", {}).get("status")
            if status == "COMPLETE":
                img_url = r_get.json()["generations_by_pk"]["generated_images"][0]["url"]
                # Añadido timeout de seguridad a la descarga
                img_data = requests.get(img_url, timeout=60).content
                with open(ruta, "wb") as f:
                    f.write(img_data)
                Image.open(ruta).convert("RGB").save(ruta, "JPEG", quality=92)
                return True
            elif status == "FAILED":
                return False
    except Exception as e:
        print(f"    ⚠️ Error en Leonardo AI: {e}")
        return False
    return False

def descargar_imagen_pollinations(prompt, ruta, semilla):
    print("    🌺 Intentando con Pollinations AI...")
    prompt_limpio = prompt[:380]
    url = (
        "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt_limpio)
        + f"?width=1080&height=1920&model=flux&nologo=true&seed={semilla}"
    )
    for intento in range(3):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                with open(ruta, "wb") as f:
                    f.write(r.content)
                Image.open(ruta).convert("RGB").save(ruta, "JPEG", quality=92)
                return True
            print(f"    ⚠️ Respuesta {r.status_code} de Pollinations (intento {intento + 1})")
        except Exception as e:
            print(f"    ⚠️ Error de conexión Pollinations (intento {intento + 1}): {e}")
        time.sleep(3)
    return False

def descargar_imagen_ia(prompt, ruta, semilla):
    if descargar_imagen_leonardo(prompt, ruta):
        return True
    if descargar_imagen_pollinations(prompt, ruta, semilla):
        return True
    return False

def crear_escena_portada(ruta_destino):
    if not os.path.exists(RUTA_PORTADA):
        return False
    try:
        portada = Image.open(RUTA_PORTADA).convert("RGB")
        fondo = portada.resize((1080, 1920), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28))
        capa_oscura = Image.new("RGB", (1080, 1920), (8, 10, 22))
        fondo = Image.blend(fondo, capa_oscura, 0.62)

        max_w, max_h = 680, 860
        w_orig, h_orig = portada.size
        ratio = min(max_w / w_orig, max_h / h_orig)
        new_w, new_h = int(w_orig * ratio), int(h_orig * ratio)
        portada_nitida = portada.resize((new_w, new_h), Image.LANCZOS)

        borde = 8
        marco = Image.new("RGB", (new_w + borde * 2, new_h + borde * 2), (255, 230, 0))
        marco.paste(portada_nitida, (borde, borde))

        pos_x = (1080 - marco.width) // 2
        pos_y = 250 + (920 - marco.height) // 2
        fondo.paste(marco, (pos_x, pos_y))

        fondo.save(ruta_destino, "JPEG", quality=95)
        return True
    except Exception as e:
        print(f"    ⚠️ Error procesando portada.jpg: {e}")
        return False

def generar_imagenes(escenas, cabecera):
    carpeta = "render_tmp"
    rutas = []
    base_seed = random.randint(1, 10_000_000)
    total = len(escenas)

    for i, esc in enumerate(escenas):
        ruta = os.path.join(carpeta, f"img_{i}.jpg")
        es_escena_libro = (i == total - 1) or ("libro" in esc["texto"].lower())

        if es_escena_libro and crear_escena_portada(ruta):
            print(f"📕 Escena {i + 1}/{total}: Portada del libro ({RUTA_PORTADA}) integrada con éxito.", flush=True)
            rutas.append(ruta)
            continue

        descripcion = esc.get("img") or f"{cabecera.lower()}, {esc['texto']}"
        prompt = f"{descripcion}. {ESTILO_IMAGEN}"
        print(f"🖼️ Generando imagen {i + 1}/{total}...", flush=True)
        ok = descargar_imagen_ia(prompt, ruta, base_seed + i)
        if not ok:
            print("    ↪ Usando fondo de respaldo.")
            crear_fondo_respaldo(ruta, base_seed + i)
        rutas.append(ruta)
        time.sleep(3)
    return rutas

# ==============================================================================
# SUBTÍTULOS (Caché de fuentes y capas optimizado)
# ==============================================================================
def dibujar_subtitulos(frame, t, tiempos_textos, cabecera, capa_overlay, f_cab, f_sub):
    # Ya no procesamos rectángulos ni cargamos fuentes por frame. Se pasa pre-procesado.
    img = Image.fromarray(frame).resize((1080, 1920), Image.LANCZOS).convert("RGBA")
    img = Image.alpha_composite(img, capa_overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

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
        if actual:
            lineas.append(" ".join(actual))

        y = 1250
        for idx, lin in enumerate(lineas):
            color = "#00FF88" if idx == len(lineas) - 1 else "#FFFFFF"
            bbox = draw.textbbox((0, 0), lin, font=f_sub)
            draw.text(((1080 - (bbox[2] - bbox[0])) / 2, y), lin, font=f_sub, fill=color, stroke_width=5, stroke_fill="#000000")
            y += (bbox[3] - bbox[1]) + 20

    return np.array(img)

# ==============================================================================
# PRODUCCIÓN DEL VÍDEO
# ==============================================================================
def producir_video_imagenes(clave, datos):
    print(f"🎬 Iniciando producción con IMÁGENES IA + PORTADA: {clave}", flush=True)
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

    # Pre-calcular fuentes y overlay oscuro para ahorrar carga de CPU por frame
    try:
        f_cab = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
        f_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        f_cab = ImageFont.load_default()
        f_sub = ImageFont.load_default()

    capa_overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    dr_capa = ImageDraw.Draw(capa_overlay)
    dr_capa.rectangle([(0, 0), (1080, 230)], fill=(0, 0, 0, 160))
    dr_capa.rectangle([(0, 1200), (1080, 1720)], fill=(0, 0, 0, 150))

    def make_frame(t):
        idx = 0
        for i in range(n):
            if inicios[i] <= t:
                idx = i
        ini = inicios[idx]
        fin = inicios[idx + 1] if idx + 1 < n else dur_total
        prog = min(max((t - ini) / max(fin - ini, 0.1), 0.0), 1.0)
        
        if idx == n - 1:
            z = 1.0 + 0.04 * prog
        else:
            z = 1.0 + 0.12 * prog if idx % 2 == 0 else 1.12 - 0.12 * prog
            
        w, h = 1080 / z, 1920 / z
        izq, arr = (1080 - w) / 2, (1920 - h) / 2
        recorte = imagenes[idx].crop((izq, arr, izq + w, arr + h)).resize((1080, 1920), Image.BILINEAR)
        return dibujar_subtitulos(np.array(recorte), t, tiempos_textos, cabecera, capa_overlay, f_cab, f_sub)

    print("✍️ Montando vídeo con subtítulos sincronizados...")
    video = VideoClip(make_frame, duration=dur_total).set_audio(audio)

    mp4_out = "render_tmp/VIDEO_FINAL.mp4"
    video.write_videofile(
        mp4_out, fps=24, codec="libx264", audio_codec="aac",
        preset="veryfast", ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None
    )
    return mp4_out

# ==============================================================================
# PUBLICACIÓN
# ==============================================================================
def enviar_pack_telegram(video_path, titulo_yt):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Faltan credenciales de Telegram. Omitiendo.")
        return False

    # Truncar título y escapar HTML para evitar roturas de formato en Telegram
    titulo_yt_limpio = html.escape(titulo_yt[:100].strip())
    
    descripcion_yt = html.escape(
        f"¿Quieres entender el comportamiento humano?\n\n"
        f"📕 Descarga mi libro 'Arquitectura de la Mente' con DESCUENTO:\n"
        f"👉 {LINK_CORTO}\n"
        f"🔗 Enlace directo: {LINK_LIBRO}\n\n"
        f"#psicologia #lenguajecorporal #desarrollopersonal #shorts"
    )
    descripcion_tiktok = html.escape(
        f"{titulo_yt_limpio} 🧠 Descarga mi libro 'Arquitectura de la Mente' en el enlace de mi perfil o aquí 👉 {LINK_CORTO} "
        f"#psicologia #lenguajecorporal #autoestima"
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
        f"¿Quieres entender el comportamiento humano?\n\n"
        f"📕 Consigue mi libro 'Arquitectura de la Mente' en el enlace de mi perfil o entrando en:\n"
        f"👉 {LINK_CORTO}\n"
        f"🔗 {LINK_LIBRO}\n\n"
        f"#psicologia #lenguajecorporal #desarrollopersonal #shorts"
    )

    print("📱 Conectando a Instagram mediante sesión inyectada...")
    try:
        try:
            sesion_guardada = json.loads(INSTA_SESSION)
        except json.JSONDecodeError as e:
            print(f"❌ Error crítico: El Secreto INSTA_SESSION no es un JSON válido. Detalle: {e}")
            return False

        cl = Client()
        cl.delay_range = [2, 6]
        
        # --- PARCHE PARA EVITAR EL ERROR 404 de /v1/qe/expose/ ---
        cl.qe_sync = lambda *args, **kwargs: None 
        # ---------------------------------------------------------
        
        cl.settings = sesion_guardada
        cl.set_settings(sesion_guardada)
        cl.login(INSTA_USER, INSTA_PASS)

        print("🚀 Subiendo Reel a Instagram...")
        cl.clip_upload(
            video_path,
            descripcion_ig,
            extra_data={
                "custom_accessibility_caption": "Vídeo de psicología y comportamiento humano.",
                "like_and_view_counts_disabled": 0,
                "disable_comments": 0,
            }
        )
        print("✅ ¡Reel publicado con éxito en Instagram!")

        print("🚀 Subiendo Historia con enlace al libro...")
        try:
            enlace = StoryLink(webUri=LINK_CORTO)
            cl.video_upload_to_story(
                video_path,
                links=[enlace]
            )
            print("✅ ¡Historia publicada con éxito con el enlace!")
        except Exception as e:
            print(f"❌ Error subiendo la Historia: {e}")

        return True
    except Exception as e:
        print(f"❌ Error general en Instagram: {e}")
        return False

def publicar_youtube_short(video_path, titulo_yt):
    YT_CLIENT_ID = os.getenv("YT_CLIENT_ID")
    YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
    YT_REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")

    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]):
        print("⚠️ Faltan credenciales de YouTube en los Secrets. Omitiendo.")
        return False

    # Truncado crítico para la API de YouTube (límite 100 caracteres)
    titulo_limpio_yt = titulo_yt[:100].strip()

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
            f"¿Quieres entender el comportamiento humano?\n\n"
            f"📕 Descarga mi manual 'Arquitectura de la Mente' con DESCUENTO aquí:\n"
            f"👉 {LINK_CORTO}\n"
            f"🔗 Enlace directo: {LINK_LIBRO}\n\n"
            f"#psicologia #lenguajecorporal #desarrollopersonal #shorts"
        )
        body = {
            "snippet": {
                "title": titulo_limpio_yt,
                "description": descripcion_yt,
                "tags": ["psicologia", "shorts", "desarrollo personal", "arquitectura de la mente"],
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

    exito_telegram = enviar_pack_telegram(ruta_mp4, datos["titulo_yt"])
    exito_ig = publicar_instagram_reel(ruta_mp4, datos["titulo_yt"])
    exito_yt = publicar_youtube_short(ruta_mp4, datos["titulo_yt"])

    if exito_telegram or exito_ig or exito_yt:
        guardar_historial(clave_elegida)
        print("🎉 Proceso completado con éxito.")
    else:
        print("⚠️ Hubo un fallo en la distribución.")
