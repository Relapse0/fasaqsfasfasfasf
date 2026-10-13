"""Генерация QR-кодов (библиотека qrcode, без внешних API)."""
from __future__ import annotations

import io

import qrcode


def make_qr(data: str) -> io.BytesIO:
    """Возвращает PNG с QR-кодом в BytesIO."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
