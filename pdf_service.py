from __future__ import annotations
"""Renderiza un catálogo (objeto Catalog) a HTML y PDF vía WeasyPrint."""
import os
import sys
from pathlib import Path

# libgobject / pango / cairo en /opt/homebrew/lib (macOS Homebrew)
if sys.platform == "darwin":
    _brew = "/opt/homebrew/lib"
    if Path(_brew).is_dir():
        _cur = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        if _brew not in _cur.split(":"):
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = f"{_brew}:{_cur}" if _cur else _brew

from jinja2 import Environment, FileSystemLoader, select_autoescape

from db import APP_DIR, UPLOADS_DIR
from models import Catalog

PDF_TEMPLATES_DIR = APP_DIR / "pdf_templates"
FONTS_DIR = APP_DIR / "fonts"


def list_templates() -> list[dict[str, str]]:
    """Retorna las plantillas PDF disponibles (una por subcarpeta)."""
    result: list[dict[str, str]] = []
    if not PDF_TEMPLATES_DIR.exists():
        return result
    for folder in sorted(PDF_TEMPLATES_DIR.iterdir()):
        if not folder.is_dir():
            continue
        if not (folder / "template.html").exists():
            continue
        meta_file = folder / "meta.txt"
        label = folder.name.title()
        description = ""
        if meta_file.exists():
            lines = meta_file.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                label = lines[0].strip() or label
            if len(lines) > 1:
                description = " ".join(lines[1:]).strip()
        result.append({"key": folder.name, "label": label, "description": description})
    return result


def _build_context(catalog: Catalog) -> dict:
    """Arma el contexto Jinja2 que las plantillas PDF esperan."""
    company = {
        "name": catalog.company_name,
        "tagline": catalog.company_tagline,
        "description": catalog.company_description,
        "website": catalog.company_website,
        "phone": catalog.company_phone,
        "email": catalog.company_email,
        "country": catalog.company_country,
        "catalog_title": catalog.catalog_title,
        "catalog_subtitle": catalog.catalog_subtitle,
        "edition": catalog.edition,
        "category_label": catalog.category_label,
    }
    paragraphs = [p.strip() for p in (catalog.company_description or "").split("\n\n") if p.strip()]

    products = []
    for p in catalog.products:
        image_abs = ""
        if p.image_path:
            abs_path = UPLOADS_DIR / p.image_path
            if abs_path.exists():
                image_abs = abs_path.as_uri()
        products.append({
            "code": p.code or f"{p.sort_order + 1:02d}",
            "name": p.name,
            "tagline": p.tagline,
            "description": p.description,
            "price_label": p.price_label,
            "price_usd": p.price_usd,
            "usage": p.usage or "Consulta las indicaciones del envase.",
            "benefits": p.benefits or [],
            "ingredients": p.ingredients or [],
            "presentation": p.presentation or [],
            "image_path": image_abs,
        })

    tips_tuples = [(t.get("title", ""), t.get("body", "")) for t in (catalog.tips or [])]

    return {
        "company": company,
        "company_paragraphs": paragraphs,
        "products": products,
        "socials": catalog.socials or [],
        "tips": tips_tuples,
        "theme": catalog.theme or {},
        "fonts_url": FONTS_DIR.as_uri() + "/",
    }


def _env_for(template_key: str) -> tuple[Environment, str]:
    template_dir = PDF_TEMPLATES_DIR / template_key
    if not (template_dir / "template.html").exists():
        # Fallback a "editorial".
        template_dir = PDF_TEMPLATES_DIR / "editorial"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env, "template.html"


def render_html(catalog: Catalog) -> str:
    env, template_name = _env_for(catalog.template_name or "editorial")
    template = env.get_template(template_name)
    return template.render(**_build_context(catalog))


def render_pdf(catalog: Catalog, output_path: Path | None = None) -> bytes:
    from weasyprint import HTML

    html_content = render_html(catalog)
    base_url = str(PDF_TEMPLATES_DIR / (catalog.template_name or "editorial")) + "/"
    html = HTML(string=html_content, base_url=base_url)
    if output_path is not None:
        html.write_pdf(str(output_path))
        return output_path.read_bytes()
    return html.write_pdf()
