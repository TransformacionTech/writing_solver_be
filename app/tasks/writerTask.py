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