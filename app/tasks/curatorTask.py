from crewai import Task
from app.agents import curatorAgent

curatorTask = Task(
    description="""
Analiza los artículos recientes obtenidos de las fuentes monitoreadas y los temas ya
procesados anteriormente. Tu objetivo es identificar exactamente 3 temas nuevos y relevantes
para el sector asegurador latinoamericano.

<articulos_recientes>
{articles}
</articulos_recientes>

<temas_ya_procesados>
{processed_topics}
</temas_ya_procesados>

INSTRUCCIONES:
1. Lee todos los artículos.
2. Descarta cualquier tema que ya esté en la lista de temas procesados (similitud semántica).
3. Consolida artículos que traten el mismo tema en un único hallazgo.
4. Si solo hay artículos de una fuente, genera 3 ángulos distintos desde esa fuente.
5. Para cada uno de los 3 temas, entrega la síntesis estructurada indicada.
    """,
    agent=curatorAgent.curator,
    expected_output="""
Responde SIEMPRE con exactamente 3 bloques, uno por tema, usando este formato:

---
TEMA 1
Título: [título corto del tema]
Resumen: [2-3 párrafos que sintetizan la información encontrada sobre este tema]
Datos clave: [lista de 2-4 datos concretos con sus fuentes]
Fuentes usadas: [lista de URLs o nombres de sitio]
Relevancia sectorial: [1-2 líneas sobre por qué importa para aseguradoras en LATAM]
---

---
TEMA 2
Título: [título corto del tema]
Resumen: [2-3 párrafos que sintetizan la información encontrada sobre este tema]
Datos clave: [lista de 2-4 datos concretos con sus fuentes]
Fuentes usadas: [lista de URLs o nombres de sitio]
Relevancia sectorial: [1-2 líneas sobre por qué importa para aseguradoras en LATAM]
---

---
TEMA 3
Título: [título corto del tema]
Resumen: [2-3 párrafos que sintetizan la información encontrada sobre este tema]
Datos clave: [lista de 2-4 datos concretos con sus fuentes]
Fuentes usadas: [lista de URLs o nombres de sitio]
Relevancia sectorial: [1-2 líneas sobre por qué importa para aseguradoras en LATAM]
---
    """,
)
