# -*- coding: utf-8 -*-
"""
certificate_generator.py
========================
Модуль звітності для SecureWipe Pro (Етап 7 — Документування).

Генерує офіційний Сертифікат знищення носія у форматі PDF відповідно до
вимог стандарту NIST SP 800-88r2 "Guidelines for Media Sanitization".

Модуль працює з реальними даними операції, які формує програма
(метод знищення, об'єкт, час, результат верифікації). Поля, які
програма не визначає автоматично (виробник, модель, серійний номер,
ПІБ оператора та верифікатора), залишаються порожніми для заповнення
вручну та подальшого фізичного підпису.

Залежності: reportlab (pip install reportlab)
"""

import os
from datetime import datetime
from typing import Dict, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


# ────────────────────────────────────────────────────────────────
#  РЕЄСТРАЦІЯ ШРИФТІВ З ПІДТРИМКОЮ КИРИЛИЦІ
# ────────────────────────────────────────────────────────────────
def _register_fonts() -> tuple:
    """
    Реєструє шрифти з підтримкою кирилиці. Повертає (regular, bold).
    Якщо DejaVu недоступний, відкочується на стандартний Helvetica
    (без гарантії коректного відображення українських літер).
    """
    candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
        ("C:/Windows/Fonts/DejaVuSans.ttf", "C:/Windows/Fonts/DejaVuSans-Bold.ttf"),
    ]
    for reg, bold in candidates:
        if os.path.exists(reg) and os.path.exists(bold):
            try:
                pdfmetrics.registerFont(TTFont("Cyr", reg))
                pdfmetrics.registerFont(TTFont("Cyr-Bold", bold))
                return "Cyr", "Cyr-Bold"
            except Exception:
                continue
    # Резервний варіант
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = _register_fonts()


# ────────────────────────────────────────────────────────────────
#  ВАЛІДАЦІЯ ВХІДНИХ ДАНИХ
# ────────────────────────────────────────────────────────────────
def _safe(value, default: str = "________________") -> str:
    """Повертає рядкове значення або прочерк для ручного заповнення."""
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def _format_dt(iso_or_text: Optional[str]) -> str:
    """Приводить ISO-8601 час до читабельного вигляду; інакше повертає як є."""
    if not iso_or_text:
        return "________________"
    try:
        dt = datetime.fromisoformat(str(iso_or_text).replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return str(iso_or_text)


# ────────────────────────────────────────────────────────────────
#  ОСНОВНА ФУНКЦІЯ ГЕНЕРАЦІЇ СЕРТИФІКАТА
# ────────────────────────────────────────────────────────────────
def generate_certificate(data: Dict, output_path: str) -> Dict:
    """
    Генерує PDF-сертифікат знищення носія.

    Параметри
    ----------
    data : dict
        Словник з даними операції. Очікувані ключі (усі — опціональні,
        відсутні замінюються прочерками для ручного заповнення):
            media_id            : {manufacturer, model, capacity_gb}
            sanitization_method : str   (напр., "NIST Purge - NVMe Sanitize")
            timestamps          : {start_time, end_time}  (ISO-8601)
            verification_result : {status, bad_blocks_found, verification_method}
            operator_id         : str
            verifier_id         : str
            object_path         : str   (шлях/диск, який стирали)
            log_sha256          : str   (хеш запису журналу, якщо є)
            standard            : str   (за замовчуванням NIST SP 800-88r2)

    output_path : str
        Шлях до PDF-файлу, який буде створено.

    Повертає
    --------
    dict : {'success': bool, 'path': str | None, 'error': str}
    """
    try:
        # ── розбір вхідних даних з безпечними значеннями за замовчуванням ──
        media = data.get("media_id", {}) or {}
        verif = data.get("verification_result", {}) or {}
        times = data.get("timestamps", {}) or {}

        manufacturer = _safe(media.get("manufacturer"))
        model = _safe(media.get("model"))
        capacity = media.get("capacity_gb")
        capacity_str = f"{capacity} ГБ" if capacity else "________________"

        method = _safe(data.get("sanitization_method"))
        standard = data.get("standard") or "NIST SP 800-88r2"

        start = _format_dt(times.get("start_time"))
        end = _format_dt(times.get("end_time"))

        v_status = _safe(verif.get("status"), "—")
        v_method = _safe(verif.get("verification_method"))
        bad_blocks = verif.get("bad_blocks_found")
        bad_blocks_str = str(bad_blocks) if bad_blocks is not None else "0"

        operator = _safe(data.get("operator_id"))
        verifier = _safe(data.get("verifier_id"))
        obj_path = _safe(data.get("object_path"))
        log_hash = _safe(data.get("log_sha256"), "—")

        cert_no = datetime.now().strftime("SWP-%Y%m%d-%H%M%S")

        # ── стилі ──
        st_title = ParagraphStyle("title", fontName=FONT_BOLD, fontSize=16,
                                  alignment=1, spaceAfter=2, leading=20)
        st_subtitle = ParagraphStyle("subtitle", fontName=FONT, fontSize=10,
                                     alignment=1, textColor=colors.HexColor("#444444"),
                                     spaceAfter=2, leading=13)
        st_h = ParagraphStyle("h", fontName=FONT_BOLD, fontSize=11,
                              textColor=colors.HexColor("#1a1a1a"),
                              spaceBefore=7, spaceAfter=4, leading=14)
        st_normal = ParagraphStyle("n", fontName=FONT, fontSize=9.5, leading=13)
        st_disc = ParagraphStyle("disc", fontName=FONT, fontSize=9,
                                alignment=4, leading=13,
                                textColor=colors.HexColor("#222222"))
        st_cell = ParagraphStyle("cell", fontName=FONT, fontSize=9.5, leading=12)
        st_cell_b = ParagraphStyle("cellb", fontName=FONT_BOLD, fontSize=9.5, leading=12)
        st_small = ParagraphStyle("small", fontName=FONT, fontSize=8,
                                 alignment=1, textColor=colors.HexColor("#777777"))

        elements = []

        # ── ШАПКА ──
        elements.append(Paragraph("СЕРТИФІКАТ ЗНИЩЕННЯ ДАНИХ НОСІЯ", st_title))
        elements.append(Paragraph("MEDIA SANITIZATION CERTIFICATE", st_subtitle))
        elements.append(Paragraph(
            f"відповідно до / in accordance with {standard} та / and IEEE 2883-2022",
            st_subtitle))
        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="100%", thickness=1.2,
                                   color=colors.HexColor("#1a1a1a")))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(
            f"№ сертифіката (Certificate No.): {cert_no}", st_normal))
        elements.append(Spacer(1, 8))

        # ── РОЗДІЛ 1: НОСІЙ ──
        elements.append(Paragraph("1. Відомості про носій (Media Information)", st_h))
        media_rows = [
            [Paragraph("Виробник (Manufacturer)", st_cell_b), Paragraph(manufacturer, st_cell)],
            [Paragraph("Модель (Model)", st_cell_b), Paragraph(model, st_cell)],
            [Paragraph("Ємність (Capacity)", st_cell_b), Paragraph(capacity_str, st_cell)],
            [Paragraph("Об'єкт стирання (Target)", st_cell_b), Paragraph(obj_path, st_cell)],
        ]
        t_media = Table(media_rows, colWidths=[70 * mm, 100 * mm])
        t_media.setStyle(_table_style())
        elements.append(t_media)

        # ── РОЗДІЛ 2: МЕТОД ЗНИЩЕННЯ ──
        elements.append(Paragraph("2. Метод знищення даних (Sanitization Method)", st_h))
        method_rows = [
            [Paragraph("Застосований метод (Method)", st_cell_b), Paragraph(method, st_cell)],
            [Paragraph("Стандарт (Standard)", st_cell_b), Paragraph(standard, st_cell)],
            [Paragraph("Час початку (Start Time)", st_cell_b), Paragraph(start, st_cell)],
            [Paragraph("Час завершення (End Time)", st_cell_b), Paragraph(end, st_cell)],
        ]
        t_method = Table(method_rows, colWidths=[70 * mm, 100 * mm])
        t_method.setStyle(_table_style())
        elements.append(t_method)

        # ── РОЗДІЛ 3: ВЕРИФІКАЦІЯ ──
        elements.append(Paragraph("3. Результат верифікації (Verification Result)", st_h))
        status_color = colors.HexColor("#1a7a30") if v_status.upper() == "SUCCESS" \
            else colors.HexColor("#a11")
        st_status = ParagraphStyle("status", fontName=FONT_BOLD, fontSize=9.5,
                                   leading=12, textColor=status_color)
        verif_rows = [
            [Paragraph("Статус (Status)", st_cell_b), Paragraph(v_status, st_status)],
            [Paragraph("Метод верифікації (Verification Method)", st_cell_b), Paragraph(v_method, st_cell)],
            [Paragraph("Виявлено пошкоджених блоків (Bad Blocks)", st_cell_b), Paragraph(bad_blocks_str, st_cell)],
            [Paragraph("Хеш запису журналу (Log SHA-256)", st_cell_b),
             Paragraph(f'<font size="7">{log_hash}</font>', st_cell)],
        ]
        t_verif = Table(verif_rows, colWidths=[70 * mm, 100 * mm])
        t_verif.setStyle(_table_style())
        elements.append(t_verif)

        # ── ДИСКЛЕЙМЕР ──
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=0.6,
                                   color=colors.HexColor("#999999")))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(
            "This document serves as proof that the media described below has been "
            "sanitized in accordance with NIST SP 800-88r2 guidelines and data "
            "recovery is computationally infeasible.", st_disc))
        elements.append(Spacer(1, 3))
        elements.append(Paragraph(
            "Цей документ підтверджує, що описаний носій було піддано процедурі "
            "знищення даних (Media Sanitization) відповідно до вимог стандарту "
            "NIST SP 800-88r2, унаслідок чого відновлення даних є обчислювально "
            "неможливим.", st_disc))
        elements.append(Spacer(1, 10))

        # ── ПІДПИСИ ──
        elements.append(Paragraph("4. Підписи (Signatures)", st_h))
        sign_rows = [
            [Paragraph("Оператор (Operator)", st_cell_b),
             Paragraph("Верифікатор (Verifier)", st_cell_b)],
            [Paragraph(operator, st_cell), Paragraph(verifier, st_cell)],
            [Paragraph("Підпис / Signature: ____________", st_cell),
             Paragraph("Підпис / Signature: ____________", st_cell)],
            [Paragraph("Дата / Date: ____________", st_cell),
             Paragraph("Дата / Date: ____________", st_cell)],
        ]
        t_sign = Table(sign_rows, colWidths=[85 * mm, 85 * mm], rowHeights=[None, 22, 22, 16])
        t_sign.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), FONT),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#444444")),
            ("LINEAFTER", (0, 0), (0, -1), 0.8, colors.HexColor("#444444")),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#bbbbbb")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(t_sign)

        elements.append(Spacer(1, 14))
        elements.append(Paragraph(
            f"Згенеровано SecureWipe Pro · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · "
            f"Документ є доказовим при регуляторних перевірках", st_small))

        # ── ЗБІРКА ДОКУМЕНТА ──
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            topMargin=18 * mm, bottomMargin=18 * mm,
            leftMargin=20 * mm, rightMargin=20 * mm,
            title="Сертифікат знищення носія", author="SecureWipe Pro",
        )
        doc.build(elements)
        return {"success": True, "path": output_path, "error": ""}

    except PermissionError:
        return {"success": False, "path": None,
                "error": "Немає прав на запис PDF-файлу за вказаним шляхом."}
    except Exception as e:
        return {"success": False, "path": None, "error": str(e)}


def _table_style() -> TableStyle:
    """Спільний стиль для інформаційних таблиць сертифіката."""
    return TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f2f2")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#444444")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ])


# ────────────────────────────────────────────────────────────────
#  ДЕМОНСТРАЦІЙНИЙ ЗАПУСК (CLI)
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo = {
        "media_id": {
            "manufacturer": "TOSHIBA",
            "model": "KBG30ZMS512G NVMe",
            "capacity_gb": 512,
        },
        "sanitization_method": "NIST Purge - NVMe Sanitize",
        "timestamps": {
            "start_time": "2026-06-06T19:15:57",
            "end_time": "2026-06-06T19:16:31",
        },
        "verification_result": {
            "status": "SUCCESS",
            "bad_blocks_found": 0,
            "verification_method": "Зчитування контрольних секторів (100% нульових)",
        },
        "operator_id": None,                # для ручного заповнення
        "verifier_id": None,                # для ручного заповнення
        "object_path": "E:\\",
        "log_sha256": "885d3980c6fe7941c5a27063355c1c0518f5d4a2875be5293ebcd5ac002f4ca0",
        "standard": "NIST SP 800-88r2",
    }
    res = generate_certificate(demo, "certificate_demo.pdf")
    print(res)