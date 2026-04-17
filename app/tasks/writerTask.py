from crewai import Task
from app.agents import writerAgent

writerTask = Task(
    description="""
Estructura del post que debes escribir:

Gancho (1-2 líneas):
- Debe detener el scroll.
- Puede ser una afirmación provocadora, una estadística inesperada, una pregunta incómoda, o una tensión del sector.
- Evita aperturas genéricas como "En el mundo de los seguros..." o "La transformación digital es..."

Definición del concepto (OBLIGATORIO — justo después del gancho):
- Antes de desarrollar cualquier análisis, diagnóstico o prescripción, DEFINE el concepto central del tema en términos simples.
- Máximo 2-3 líneas. El lector debe entender qué es X antes de leer por qué importa.
- Esto aplica a TODOS los temas sin excepción.

Desarrollo (3-5 párrafos cortos):
- Responde literalmente lo que se pidió: si el usuario preguntó "cuáles son", enuméralos con descripción breve de cada uno; si preguntó "qué es", explícalo con ejemplos concretos del sector.
- Usa los datos de la investigación para enriquecer la respuesta, NO para cambiar el tema hacia análisis estratégico o recomendaciones operativas.
- Conecta el insight con las implicaciones prácticas para una aseguradora.
- Cuando uses datos o cifras, cítalos de forma natural e integrada al texto. Ejemplo: "Según McKinsey (2024),..." o "Un estudio de Swiss Re indica que...". No uses notas al pie ni corchetes numéricos: LinkedIn no los renderiza.
- Si la fuente es una organización reconocida por el sector (Swiss Re, Munich Re, MAPFRE, McKinsey, Deloitte, IAIS, FASECOLDA, etc.), inclúyela siempre: aumenta credibilidad ante la audiencia aseguradora.
- No acumules más de 2 citas en el mismo post: afecta la fluidez de lectura en LinkedIn.

### REGLAS DE ESCRITURA OBLIGATORIAS (aplicar antes del Paso 3)

REGLA: CONTEXTUALIZACIÓN DE ACTORES NO SECTORIALES
Si el post menciona una organización que no sea aseguradora, reaseguradora,
consultora global (McKinsey, Deloitte, PwC, Accenture, Gartner) o medio
especializado del sector (Swiss Re, Munich Re, Lloyd's, Insurance Journal,
FASECOLDA, AMIS, CNseg, MAPFRE), incluye una línea de contexto que explique
qué es y por qué es relevante para aseguradoras en LATAM.
❌ "La AECID anunció una inversión de €25M..."
✅ "La AECID —agencia de cooperación internacional de España— anunció
   una inversión de €25M con foco explícito en inclusión financiera en LATAM..."
Si no puedes contextualizar al actor con los datos disponibles → señalarlo en
## ALERTAS antes de entregar.

REGLA: CLAIMS COMPARATIVOS REQUIEREN CIFRA + FUENTE + AÑO
Frases como "freno estructural", "baja penetración", "tendencia creciente",
"mínimos históricos", "crecimiento acelerado" o cualquier afirmación que
compare el estado actual del mercado con otro periodo, región o benchmark
NUNCA pueden aparecer sin cifra + fuente + año inmediatamente adjuntos.
❌ "...atacar el gran freno estructural de la región—baja penetración—..."
✅ "...atacar la baja penetración de seguros en LATAM (promedio regional:
   3% del PIB vs. 8% en mercados desarrollados, Swiss Re 2023)..."
Si la investigación no provee el dato → NO usar el claim y señalarlo en
## ALERTAS con la nota: [claim comparativo sin respaldo — no incluido].

REGLA: UN SOLO CIERRE, MODO REFLEXIÓN
El post termina con exactamente UNA pregunta de cierre.
Está formulada en modo experiencia o reflexión:
✅ "¿Qué ves tú...?" / "¿Dónde lo notas en tu operación?" / "¿Cuál es tu lectura?"
Nunca en modo prescriptivo o imperativo, aunque no nombre un cargo directivo:
❌ "¿Qué parte de tu cadena de valor tienes que rediseñar primero?"
❌ "¿Qué deberías cambiar antes de escalar?"
Si el borrador tiene dos preguntas al final → eliminar la prescriptiva,
conservar la reflexiva.

Cierre (1-2 líneas):
- DEBE ser una pregunta abierta que cualquier profesional del sector pueda responder desde su realidad, sin importar su cargo.
- NUNCA dirijas el cierre a un perfil directivo específico (CIO, VP, Director de Operaciones, C-level) a menos que la solicitud original lo pida.
- Evita cierres tipo "¿Quieres saber más? Contáctanos."

Hashtags:
- Entre 3 y 5, relevantes para el sector y el tema.
- Ejemplos de referencia: #Seguros #TransformacionDigital #Insurtech #ExperienciaDelAsegurado #Siniestros
- Tener en cuenta que no llevan tildes.

### VERIFICACIÓN OBLIGATORIA ANTES DE ENTREGAR EL POST

VERIFICACIÓN 1 — HASHTAGS SIN TILDES (OBLIGATORIO, SIN EXCEPCIÓN)
Esta verificación es la última acción antes de entregar el post.
No es opcional. No se omite aunque el post parezca listo.

PASO 1: Localiza TODOS los hashtags del post.
PASO 2: Por cada hashtag, revisa carácter por carácter si contiene
         tilde o carácter especial (á é í ó ú ü ñ Á É Í Ó Ú Ü Ñ).
PASO 3: Si encuentra alguno → corregirlo directamente en el texto
         antes de entregar. No señalarlo en ## ALERTAS.

Ejemplos de corrección obligatoria:
❌ #TransformaciónDigital → ✅ #TransformacionDigital
❌ #Tarificación         → ✅ #Tarificacion
❌ #InnovaciónAbierta    → ✅ #InnovacionAbierta
❌ #GobernanzaDeDatos    → ✅ #GobernanzaDeDatos (sin tilde, ya correcto)
❌ #LatAm                → ✅ #LatAm (sin tilde, ya correcto)

Si el post se entrega con un hashtag con tilde →
es un fallo de entrega, no de contenido.

VERIFICACIÓN 2 — ACTORES NO OBVIOS SIEMPRE CONTEXTUALIZADOS
Antes de entregar, identifica cada organización, plataforma, hub, alianza o
entidad mencionada en el post que no sea una aseguradora global, reaseguradora,
consultora de primer nivel o medio especializado del sector reconocido.
Para cada uno de esos actores, verifica que el post incluya una frase de contexto
que explique qué es y por qué es relevante para el sector asegurador en LATAM.
Si falta esa frase → agrégala antes de entregar. No señalarla en ## ALERTAS:
resolverla directamente en el texto.
❌ "MIA Hub firmó una colaboración con AACS..."
✅ "MIA Hub —plataforma global de conexión entre insurtechs y aseguradoras—
   firmó una colaboración con AACS..."

VERIFICACIÓN 3 — UN SOLO CIERRE, SIN FILTRO DE ROL
Antes de entregar, lee las últimas 3 líneas del post.
Verifica que haya exactamente UNA pregunta de cierre.
Verifica que esa pregunta no comience con ni contenga filtros de rol o tipo
de organización ("Si sos aseguradora", "Para equipos de TI", "Si liderás
transformación", "Para directivos", etc.).
Si hay dos preguntas → fusiónalas en una o elimina la menos reflexiva.
Si hay filtro de rol → elimínalo y reformula la pregunta para que cualquier
profesional del sector pueda responderla sin importar su cargo u organización.

VERIFICACIÓN 4 — DATOS O ALERTA EXPLÍCITA
Antes de entregar, verifica si el post contiene al menos una cifra cuantitativa
con fuente y año que respalde el argumento central.
Si la investigación recibida no provee ningún dato cuantitativo utilizable →
señalarlo en ## ALERTAS con la nota exacta:
[Sin datos cuantitativos disponibles en la investigación recibida —
el argumento se sostiene por lógica operativa y caso concreto]
No inventar cifras. No omitir la alerta si no hay datos.
---

Aquí están tus inputs:

<solicitud_original>
{topic}
</solicitud_original>

<investigacion>
[La investigación elaborada por el agente investigador está disponible en el contexto de esta tarea]
</investigacion>
    """,
    agent=writerAgent.writer,
    expected_output="""
Responde SIEMPRE con esta estructura exacta:

## POST
[texto del post listo para edición]

## DECISIÓN EDITORIAL
[2-3 líneas explicando si seguiste la solicitud original o tomaste un ángulo distinto, y por qué]

## ALTERNATIVAS DESCARTADAS
[1-2 ángulos que consideraste pero no usaste, para explorar en iteraciones futuras]

## FUENTES UTILIZADAS
[Lista las fuentes citadas en el post con el formato:
Organización/Autor (año si está disponible) — claim específico que respaldaron]

## ALERTAS
[Datos relevantes de la investigación que no pudiste usar por falta de fuente, o problemas estructurales que el editor deba revisar. Si no hay alertas, escribe: "Sin alertas."]
    """,
)