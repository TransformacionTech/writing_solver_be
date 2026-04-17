"""SendGrid email service for curation reports."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

import sendgrid
from sendgrid.helpers.mail import Mail, To

from app.core.config import settings

logger = logging.getLogger(__name__)


def name_from_email(email: str) -> str:
    """Extract a presentable name from an email address.

    Examples:
      transformacion@techandsolve.com  -> 'Transformacion'
      juan.perez@foo.com               -> 'Juan Perez'
      maria_lopez@foo.com              -> 'Maria Lopez'
    """
    local = email.split("@")[0]
    cleaned = re.sub(r"[._\-]+", " ", local).strip()
    return cleaned.title() if cleaned else email


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

def _build_html(report: dict[str, Any], recipient_name: str = "") -> str:
    """
    Build the HTML body for the curation report email.

    Expected `report` structure:
    {
        "title": str,
        "sources": [{"name": str, "url": str}],
        "summary": str,
        "topics_by_source": [{"source": str, "topics": [str]}],
        "posts": [...],
        "run_date": str,
        "intro_text": str,   # cuerpo del saludo, escrito con tono T&S
    }
    `recipient_name` se inyecta en el saludo "Hola, {nombre}".
    """
    run_date = report.get("run_date", datetime.now().strftime("%d/%m/%Y"))
    intro_text = report.get(
        "intro_text",
        "Te presento el informe de los posts sugeridos para este día con los "
        "temas publicados recientemente en las fuentes monitoreadas.",
    )
    greeting = f"Hola, {recipient_name}." if recipient_name else "Hola."
    posts = report.get("posts", [])

    # CHANGE 3 — Resumen de esta quincena: por cada post, título + why_relevant
    quincena_summary_html = "".join(
        f"""
        <div style="margin-bottom:14px">
            <p style="margin:0 0 4px 0;color:#333;font-size:0.92rem;font-weight:600">
                {i + 1}. {p["title"]}
            </p>
            <p style="margin:0;color:#555;font-size:0.88rem;line-height:1.6">
                {p.get("why_relevant", "")}
            </p>
        </div>
        """
        for i, p in enumerate(posts)
    )

    # CHANGE 4 — Posts de esta quincena: lista numerada de títulos, sin URLs
    titles_list_html = "".join(
        f'<li style="margin-bottom:4px;color:#333">{p["title"]}</li>'
        for p in posts
    )

    # CHANGE 5 — bloques de post sin "¿Por qué es relevante?"
    posts_html = "".join(
        f"""
        <div style="background:#f9f6ff;border-left:4px solid #6200EA;padding:16px 20px;
                    margin-bottom:20px;border-radius:0 8px 8px 0">
            <h3 style="margin:0 0 8px 0;color:#3d0099;font-size:1rem">Post {i + 1}: {p["title"]}</h3>
            <div style="white-space:pre-wrap;color:#333;font-size:0.9rem;line-height:1.6">
                {p["content"]}
            </div>
        </div>
        """
        for i, p in enumerate(posts)
    )

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tus 3 contenidos de esta quincena · Tech And Solve</title>
    </head>
    <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif">
        <div style="max-width:680px;margin:32px auto;background:#fff;border-radius:12px;
                    overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08)">

            <!-- CHANGE 1 — Header -->
            <div style="background:linear-gradient(135deg,#6200EA,#3d0099);
                        padding:28px 32px;color:#fff">
                <div style="font-size:0.95rem;font-weight:600">
                    Tus 3 contenidos de esta quincena · {run_date}
                </div>
            </div>

            <!-- Body -->
            <div style="padding:28px 32px">

                <!-- CHANGE 2 — Saludo + intro -->
                <p style="margin:0 0 8px 0;font-size:1rem;color:#333;font-weight:600">
                    {greeting}
                </p>
                <p style="margin:0 0 24px 0;color:#333;line-height:1.7;font-size:0.95rem">
                    {intro_text}
                </p>

                <!-- CHANGE 3 — Resumen de esta quincena -->
                <h2 style="font-size:0.95rem;text-transform:uppercase;letter-spacing:1px;
                           color:#6200EA;margin:0 0 12px 0">Resumen de esta quincena</h2>
                <div style="margin-bottom:24px">
                    {quincena_summary_html}
                </div>

                <!-- CHANGE 4 — Posts de esta quincena -->
                <h2 style="font-size:0.95rem;text-transform:uppercase;letter-spacing:1px;
                           color:#6200EA;margin:0 0 12px 0">Posts de esta quincena</h2>
                <ol style="margin:0 0 24px 0;padding-left:20px;color:#333">
                    {titles_list_html}
                </ol>

                <!-- CHANGE 5 — Post blocks (sin "¿Por qué es relevante?") -->
                <h2 style="font-size:0.95rem;text-transform:uppercase;letter-spacing:1px;
                           color:#6200EA;margin:0 0 16px 0">Posts recomendados</h2>
                {posts_html}

                <!-- CHANGE 6 — Feedback CTA -->
                <div style="margin-top:8px;padding:18px 20px;background:#f9f6ff;
                            border-radius:8px;color:#333;font-size:0.9rem;line-height:1.6">
                    <p style="margin:0 0 6px 0;font-weight:600">¿Qué te parecen los posts de esta quincena?</p>
                    <p style="margin:0">
                        Si algo te gustó, no funcionó o quieres que ajustemos el enfoque,
                        responde este correo con tu comentario.
                        Tu feedback se tiene en cuenta para seguir mejorando
                        los próximos contenidos.
                    </p>
                </div>

            </div>

            <!-- Footer -->
            <div style="background:#f9f9f9;padding:16px 32px;border-top:1px solid #eee;
                        text-align:center;font-size:0.78rem;color:#aaa">
                Generado automáticamente por Writing Solver · Tech And Solve
            </div>
        </div>
    </body>
    </html>
    """


# ---------------------------------------------------------------------------
# Send
# ---------------------------------------------------------------------------

class SendResult:
    """Wrapper to carry status + diagnostics back to the caller."""
    def __init__(self, ok: bool, status_code: int, body: str, detail: str = ""):
        self.ok = ok
        self.status_code = status_code
        self.body = body
        self.detail = detail

    def __bool__(self) -> bool:
        return self.ok


def send_curation_report(subscribers: list[str], report: dict[str, Any]) -> SendResult:
    """
    Send the curation report to all subscribers via SendGrid.
    Returns SendResult (truthy on success).
    """
    if not subscribers:
        return SendResult(False, 0, "", "No hay suscriptores.")

    if not settings.sendgrid_api_key or not settings.sendgrid_from_email:
        raise RuntimeError("SENDGRID_API_KEY and SENDGRID_FROM_EMAIL must be set.")

    subject = f"Curación de Contenidos — {report.get('title', 'Novedades del Sector')}"

    # Send one email per subscriber for better deliverability + personalized greeting
    sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    all_ok = True
    last_status = 0
    last_body = ""

    for email in subscribers:
        recipient_name = name_from_email(email)
        html_content = _build_html(report, recipient_name=recipient_name)
        message = Mail(
            from_email=settings.sendgrid_from_email,
            to_emails=email,
            subject=subject,
            html_content=html_content,
        )
        response = sg.send(message)
        last_status = response.status_code
        last_body = response.body.decode() if response.body else ""

        logger.info(
            "SendGrid → %s | status=%s headers=%s body=%s",
            email, response.status_code, dict(response.headers or {}), last_body,
        )

        if response.status_code not in (200, 202):
            all_ok = False

    detail = f"status={last_status}, to={subscribers}, from={settings.sendgrid_from_email}"
    return SendResult(all_ok, last_status, last_body, detail)


def send_no_news_email(subscribers: list[str], run_date: str) -> bool:
    """Send a brief 'no news found' notification to subscribers."""
    if not subscribers:
        return False

    if not settings.sendgrid_api_key or not settings.sendgrid_from_email:
        raise RuntimeError("SENDGRID_API_KEY and SENDGRID_FROM_EMAIL must be set.")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <body style="font-family:Arial,sans-serif;padding:32px;color:#333">
        <h2 style="color:#6200EA">Sin novedades — {run_date}</h2>
        <p>El monitoreo automático de fuentes no encontró contenido nuevo
        en los últimos 15 días que no haya sido procesado previamente.</p>
        <p style="color:#888;font-size:0.85rem">
            Próxima revisión en 15 días · Writing Solver · Tech And Solve
        </p>
    </body>
    </html>
    """

    message = Mail(
        from_email=settings.sendgrid_from_email,
        to_emails=[To(email) for email in subscribers],
        subject=f"Sin novedades — Curación automática {run_date}",
        html_content=html_content,
    )

    sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    response = sg.send(message)
    return response.status_code in (200, 202)
