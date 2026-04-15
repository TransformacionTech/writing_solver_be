"""SendGrid email service for curation reports."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import sendgrid
from sendgrid.helpers.mail import Mail, To

from app.core.config import settings


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

def _build_html(report: dict[str, Any]) -> str:
    """
    Build the HTML body for the curation report email.

    Expected `report` structure:
    {
        "title": str,
        "sources": [{"name": str, "url": str}],
        "summary": str,
        "topics_by_source": [{"source": str, "topics": [str]}],
        "posts": [
            {
                "title": str,
                "content": str,
                "why_relevant": str,
                "source": str,
            }
        ],
        "run_date": str,
    }
    """
    run_date = report.get("run_date", datetime.now().strftime("%d/%m/%Y"))

    sources_html = "".join(
        f'<li><a href="{s["url"]}" style="color:#6200EA">{s["name"]}</a></li>'
        for s in report.get("sources", [])
    )

    topics_by_source_html = "".join(
        f"""
        <div style="margin-bottom:12px">
            <strong style="color:#333">{ts["source"]}</strong>
            <ul style="margin:4px 0 0 0;padding-left:20px;color:#555">
                {"".join(f"<li>{t}</li>" for t in ts["topics"])}
            </ul>
        </div>
        """
        for ts in report.get("topics_by_source", [])
    )

    posts_html = "".join(
        f"""
        <div style="background:#f9f6ff;border-left:4px solid #6200EA;padding:16px 20px;
                    margin-bottom:20px;border-radius:0 8px 8px 0">
            <h3 style="margin:0 0 8px 0;color:#3d0099;font-size:1rem">Post {i + 1}: {p["title"]}</h3>
            <div style="white-space:pre-wrap;color:#333;font-size:0.9rem;line-height:1.6">
                {p["content"]}
            </div>
            <div style="margin-top:12px;padding-top:10px;border-top:1px solid #ddd">
                <strong style="color:#6200EA;font-size:0.82rem">¿Por qué es relevante?</strong>
                <p style="margin:4px 0 0 0;color:#555;font-size:0.85rem">{p["why_relevant"]}</p>
            </div>
        </div>
        """
        for i, p in enumerate(report.get("posts", []))
    )

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Curación de Contenidos — Tech And Solve</title>
    </head>
    <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif">
        <div style="max-width:680px;margin:32px auto;background:#fff;border-radius:12px;
                    overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08)">

            <!-- Header -->
            <div style="background:linear-gradient(135deg,#6200EA,#3d0099);
                        padding:28px 32px;color:#fff">
                <div style="font-size:0.78rem;opacity:0.8;margin-bottom:4px">
                    Curación automática · {run_date}
                </div>
                <h1 style="margin:0;font-size:1.5rem;font-weight:700">
                    {report.get("title", "Novedades del Sector")}
                </h1>
            </div>

            <!-- Body -->
            <div style="padding:28px 32px">

                <!-- Fuentes -->
                <h2 style="font-size:0.95rem;text-transform:uppercase;letter-spacing:1px;
                           color:#6200EA;margin:0 0 8px 0">Fuentes consultadas</h2>
                <ul style="margin:0 0 24px 0;padding-left:20px;color:#555">
                    {sources_html}
                </ul>

                <!-- Resumen -->
                <h2 style="font-size:0.95rem;text-transform:uppercase;letter-spacing:1px;
                           color:#6200EA;margin:0 0 8px 0">Resumen de las fuentes</h2>
                <p style="margin:0 0 24px 0;color:#333;line-height:1.7;font-size:0.92rem">
                    {report.get("summary", "")}
                </p>

                <!-- Temas por fuente -->
                <h2 style="font-size:0.95rem;text-transform:uppercase;letter-spacing:1px;
                           color:#6200EA;margin:0 0 12px 0">Temas sugeridos por fuente</h2>
                <div style="margin-bottom:24px">
                    {topics_by_source_html}
                </div>

                <!-- Posts recomendados -->
                <h2 style="font-size:0.95rem;text-transform:uppercase;letter-spacing:1px;
                           color:#6200EA;margin:0 0 16px 0">Posts recomendados</h2>
                {posts_html}

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

def send_curation_report(subscribers: list[str], report: dict[str, Any]) -> bool:
    """
    Send the curation report to all subscribers via SendGrid.
    Returns True on success, False on failure.
    """
    if not subscribers:
        return False

    if not settings.sendgrid_api_key or not settings.sendgrid_from_email:
        raise RuntimeError("SENDGRID_API_KEY and SENDGRID_FROM_EMAIL must be set.")

    html_content = _build_html(report)
    subject = f"📋 Curación de Contenidos — {report.get('title', 'Novedades del Sector')}"

    message = Mail(
        from_email=settings.sendgrid_from_email,
        to_emails=[To(email) for email in subscribers],
        subject=subject,
        html_content=html_content,
    )

    sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    response = sg.send(message)
    return response.status_code in (200, 202)


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
