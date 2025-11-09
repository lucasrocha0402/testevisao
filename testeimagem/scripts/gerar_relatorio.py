#!/usr/bin/env python3
"""
Gera o relatório de alertas críticos processados pela IA em formato PDF.

O PDF é salvo em /workspace/output/relatorio_alertas.pdf (montado no n8n).
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ModuleNotFoundError as exc:  # pragma: no cover - avisar faltas em runtime
    raise SystemExit(
        "psycopg2 não está instalado no container. "
        "Execute `pip install psycopg2-binary` antes de rodar o script."
    ) from exc

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "reportlab não está instalado no container. "
        "Execute `pip install reportlab` antes de rodar o script."
    ) from exc


def get_connection():
    """Abre conexão com Postgres usando env vars do docker-compose."""
    params = {
        "host": os.getenv("REPORT_DB_HOST", os.getenv("DB_HOST", "postgres")),
        "port": int(os.getenv("REPORT_DB_PORT", os.getenv("DB_PORT", "5432"))),
        "dbname": os.getenv("REPORT_DB_NAME", os.getenv("DB_NAME", "sma_db")),
        "user": os.getenv("REPORT_DB_USER", os.getenv("DB_USER", "sma_user")),
        "password": os.getenv(
            "REPORT_DB_PASSWORD", os.getenv("DB_PASSWORD", "senhaforte123")
        ),
    }
    return psycopg2.connect(**params)


def _fetch_with_join(cur):
    cur.execute(
        """
        SELECT
            e.integration_id,
            e.created_at,
            COALESCE(r.location, e.raw_payload->>'location', e.raw_payload->'payload'->>'location', '-') AS location,
            COALESCE(e.triage->>'ia_categoria', e.triage->>'triage_level', e.triage_level) AS ia_categoria,
            COALESCE(e.triage->>'ia_urgencia', e.triage->>'triage_reason') AS ia_urgencia,
            COALESCE(e.resumo, e.triage->>'ia_resumo', e.triage->>'resumo') AS ia_resumo
        FROM events e
        LEFT JOIN register r ON r.integration_id::text = e.integration_id::text
        WHERE e.is_alarm IS TRUE
          AND e.status IN ('processado', 'completo')
        ORDER BY e.created_at DESC NULLS LAST;
        """
    )
    return cur.fetchall()


def fetch_events(conn):
    """Busca alertas críticos processados pela IA, com fallback caso a tabela register não exista."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        try:
            return _fetch_with_join(cur)
        except psycopg2.errors.UndefinedTable:
            conn.rollback()
            cur.execute(
                """
                SELECT
                    integration_id,
                    created_at,
                    COALESCE(raw_payload->>'location', raw_payload->'payload'->>'location', '-') AS location,
                    COALESCE(triage->>'ia_categoria', triage->>'triage_level', triage_level) AS ia_categoria,
                    COALESCE(triage->>'ia_urgencia', triage->>'triage_reason') AS ia_urgencia,
                    COALESCE(resumo, triage->>'ia_resumo', triage->>'resumo') AS ia_resumo
                FROM events
                WHERE is_alarm IS TRUE
                  AND status IN ('processado', 'completo')
                ORDER BY created_at DESC NULLS LAST;
                """
            )
            return cur.fetchall()


def build_pdf(rows):
    """Gera o arquivo PDF no diretório de saída."""
    output_dir = Path(os.getenv("REPORT_OUTPUT_DIR", "/workspace/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "relatorio_alertas.pdf"

    generated_at = datetime.now(timezone.utc).astimezone()

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    cell_style = styles["BodyText"].clone("TableCell")
    cell_style.leading = 12
    cell_style.spaceAfter = 2

    story = [
        Paragraph("Relatório de Alertas Críticos - SMA v2.0", styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            f"Gerado em: {generated_at.strftime('%d/%m/%Y %H:%M:%S %Z')}",
            styles["Normal"],
        ),
        Spacer(1, 8),
    ]

    resumo_texto = (
        "Resumo: Nenhum alerta crítico foi processado pela IA no período."
        if not rows
        else f"Resumo: Foram encontrados {len(rows)} alertas críticos processados pela IA."
    )
    story.append(Paragraph(resumo_texto, styles["Normal"]))
    story.append(Spacer(1, 12))

    header = [
        "Data/Hora do Evento",
        "Localização do Dispositivo",
        "Categoria (IA)",
        "Urgência (IA)",
        "Resumo para o Gestor (IA)",
    ]
    data = [header]

    body_style = styles["BodyText"]

    if not rows:
        data.append(["Sem registros encontrados"] + [""] * (len(header) - 1))
    else:
        for row in rows:
            data.append(
                [
                    Paragraph(
                        row["created_at"].strftime("%d/%m/%Y %H:%M:%S") if row["created_at"] else "-",
                        cell_style,
                    ),
                    Paragraph(row.get("location") or "-", cell_style),
                    Paragraph(row.get("ia_categoria") or "-", cell_style),
                    Paragraph(row.get("ia_urgencia") or "-", cell_style),
                    Paragraph(row.get("ia_resumo") or "-", cell_style),
                ]
            )

    col_widths = [0.18 * doc.width, 0.24 * doc.width, 0.18 * doc.width, 0.14 * doc.width, 0.26 * doc.width]

    table = Table(
        data,
        repeatRows=1,
        colWidths=col_widths,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d3436")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecf0f1")]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.gray),
            ]
        )
    )

    story.append(table)
    doc.build(story)
    return pdf_path


def main():
    conn = get_connection()
    try:
        rows = fetch_events(conn)
    finally:
        conn.close()

    pdf_path = build_pdf(rows)
    print(json.dumps({"status": "ok", "output": str(pdf_path)}))


if __name__ == "__main__":
    main()

