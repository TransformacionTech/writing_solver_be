"""
Seed script: loads reference posts into ChromaDB so the Editor agent
has concrete examples of approved output for each common request type.

Run once:  python -m app.scripts.seed_rag
"""

from app.services.rag_service import add_document

REFERENCE_POSTS: list[dict[str, str]] = [
    # --- Tipo: "¿Qué es X?" ---------------------------------------------------
    {
        "type": "que_es",
        "content": (
            "¿Tu aseguradora sigue vendiendo pólizas como hace 20 años?\n\n"
            "El seguro embebido es, en esencia, una póliza integrada directamente "
            "en la compra de otro producto o servicio. No se vende aparte: aparece "
            "en el momento justo, dentro del flujo de compra del cliente.\n\n"
            "Ejemplo concreto: compras un vuelo y antes de pagar te ofrecen un "
            "seguro de cancelación con un solo clic. No buscaste la póliza; la "
            "póliza te encontró a ti.\n\n"
            "Según Swiss Re (2024), el mercado de seguros embebidos alcanzará "
            "USD 722 mil millones en primas para 2030. En LATAM, fintechs como "
            "Chubb y aseguradoras locales ya integran coberturas en plataformas "
            "de e-commerce y movilidad.\n\n"
            "La diferencia clave con el seguro tradicional: el embebido elimina "
            "la fricción de distribución. No compite por atención; se inserta donde "
            "la atención ya existe.\n\n"
            "¿En tu organización ya están explorando canales de distribución "
            "embebida o sigue siendo un tema pendiente?\n\n"
            "#Seguros #SeguroEmbebido #Insurtech #TransformaciónDigital"
        ),
    },
    # --- Tipo: "Tendencias de X" -----------------------------------------------
    {
        "type": "tendencias",
        "content": (
            "El 73% de los asegurados en LATAM espera resolver un siniestro "
            "desde el celular. ¿Tu operación está lista?\n\n"
            "Las tendencias en experiencia del asegurado para 2025 apuntan a un "
            "cambio que ya no es opcional. Experiencia del asegurado significa, en "
            "términos simples, cada interacción que un cliente tiene con su "
            "aseguradora — desde la cotización hasta el pago del siniestro.\n\n"
            "Tres tendencias están marcando el ritmo:\n\n"
            "1. Autoservicio real: no un PDF descargable, sino portales donde el "
            "cliente gestiona su póliza completa sin llamar a nadie.\n\n"
            "2. Siniestros en minutos: automatización con IA para liquidar "
            "reclamos simples en menos de 24 horas. Lemonade lo hace en 3 segundos "
            "para casos básicos.\n\n"
            "3. Hiperpersonalización: pólizas que se ajustan al comportamiento real "
            "del usuario, no a tablas actuariales genéricas. Según McKinsey (2024), "
            "las aseguradoras que personalizan retienen 1.5x más clientes.\n\n"
            "¿Cuál de estas tendencias ves más lejos de implementarse en tu "
            "realidad diaria?\n\n"
            "#Seguros #ExperienciaDelAsegurado #Insurtech #Siniestros "
            "#TransformaciónDigital"
        ),
    },
    # --- Tipo: "Oportunidades y retos de X" ------------------------------------
    {
        "type": "oportunidades_retos",
        "content": (
            "La IA generativa promete reducir costos operativos en seguros un 40%. "
            "Pero nadie habla de lo que puede salir mal.\n\n"
            "Inteligencia artificial generativa en seguros se refiere a modelos de "
            "IA capaces de crear texto, analizar documentos y tomar decisiones a "
            "partir de datos no estructurados — desde correos de siniestros hasta "
            "informes médicos.\n\n"
            "Las oportunidades son claras: automatizar la suscripción de riesgos "
            "simples, acelerar la detección de fraude y generar comunicaciones "
            "personalizadas a escala. Deloitte (2024) estima que las aseguradoras "
            "early adopters reducirán su ratio combinado entre 3 y 5 puntos.\n\n"
            "Pero los retos no son menores. Primero, la regulación: en Colombia, "
            "México y Brasil aún no hay marcos claros para decisiones automatizadas "
            "en seguros. Segundo, la calidad de datos — los modelos son tan buenos "
            "como la información con la que se entrenan, y muchas aseguradoras "
            "todavía operan con silos. Tercero, el riesgo reputacional: un modelo "
            "que deniega un siniestro injustamente escala rápido en redes.\n\n"
            "¿Qué pesa más en tu contexto: las oportunidades de eficiencia o los "
            "riesgos de implementar sin el marco regulatorio resuelto?\n\n"
            "#Seguros #InteligenciaArtificial #IAGenerativa #Insurtech "
            "#GestiónDeRiesgos"
        ),
    },
]


def seed() -> None:
    for post in REFERENCE_POSTS:
        doc_id = add_document(
            content=post["content"],
            metadata={"type": post["type"], "source": "seed_reference"},
        )
        print(f"[OK] Post tipo '{post['type']}' -> {doc_id}")
    print(f"\n{len(REFERENCE_POSTS)} posts de referencia cargados en ChromaDB.")


if __name__ == "__main__":
    seed()
