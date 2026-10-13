"""Обёртка над Jinja2 для сборки текстовых сообщений из шаблонов."""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_template(name: str, **context) -> str:
    """Рендерит шаблон ``name`` (например, 'wrapped_text.j2')."""
    template = _env.get_template(name)
    return template.render(**context)
