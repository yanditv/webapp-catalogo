from __future__ import annotations
"""FastAPI app — editor y generador de catálogos."""
import io
import json
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import (
    Depends, FastAPI, File, Form, HTTPException, Request, UploadFile,
)
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image
from sqlalchemy.orm import Session

from db import APP_DIR, UPLOADS_DIR, init_db, get_session
from models import Catalog, Product, DEFAULT_THEME, DEFAULT_TIPS
from pdf_service import list_templates, render_html, render_pdf

app = FastAPI(title="Catálogos · Editor")

STATIC_DIR = APP_DIR / "static"
UI_TEMPLATES_DIR = APP_DIR / "ui_templates"

STATIC_DIR.mkdir(exist_ok=True)
UI_TEMPLATES_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

_jinja = Environment(
    loader=FileSystemLoader(str(UI_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render(template: str, **ctx) -> HTMLResponse:
    tpl = _jinja.get_template(template)
    return HTMLResponse(tpl.render(**ctx))


@app.on_event("startup")
def _startup() -> None:
    init_db()


# ─────────────────────────────────────────────────────────────────────────
# Listado / creación de catálogos
# ─────────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index(db: Session = Depends(get_session)):
    catalogs = db.query(Catalog).order_by(Catalog.updated_at.desc()).all()
    return render("index.html", catalogs=catalogs, templates=list_templates())


@app.post("/catalogs")
def create_catalog(
    name: str = Form(...),
    template_name: str = Form("editorial"),
    db: Session = Depends(get_session),
):
    catalog = Catalog(
        name=name.strip() or "Nuevo catálogo",
        template_name=template_name,
        company_name="Mi empresa",
        company_tagline="",
        company_description="",
        company_website="",
        company_phone="",
        company_email="",
        company_country="",
        catalog_title=name.strip() or "Catálogo",
        catalog_subtitle="",
        edition="Edición 01",
        theme=dict(DEFAULT_THEME),
        socials=[],
        tips=list(DEFAULT_TIPS),
    )
    db.add(catalog)
    db.commit()
    db.refresh(catalog)
    return RedirectResponse(f"/catalogs/{catalog.id}/edit", status_code=303)


@app.post("/catalogs/{catalog_id}/duplicate")
def duplicate_catalog(catalog_id: int, db: Session = Depends(get_session)):
    src = db.get(Catalog, catalog_id)
    if not src:
        raise HTTPException(404)
    dst = Catalog(
        name=f"{src.name} (copia)",
        template_name=src.template_name,
        company_name=src.company_name,
        company_tagline=src.company_tagline,
        company_description=src.company_description,
        company_website=src.company_website,
        company_phone=src.company_phone,
        company_email=src.company_email,
        company_country=src.company_country,
        catalog_title=src.catalog_title,
        catalog_subtitle=src.catalog_subtitle,
        edition=src.edition,
        category_label=src.category_label,
        theme=dict(src.theme or {}),
        socials=list(src.socials or []),
        tips=list(src.tips or []),
    )
    db.add(dst)
    db.flush()
    for p in src.products:
        new_img = ""
        if p.image_path:
            src_abs = UPLOADS_DIR / p.image_path
            if src_abs.exists():
                dst_rel = f"catalog_{dst.id}/{uuid.uuid4().hex}{src_abs.suffix}"
                dst_abs = UPLOADS_DIR / dst_rel
                dst_abs.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_abs, dst_abs)
                new_img = dst_rel
        db.add(Product(
            catalog_id=dst.id,
            sort_order=p.sort_order,
            code=p.code,
            name=p.name,
            tagline=p.tagline,
            description=p.description,
            price_usd=p.price_usd,
            usage=p.usage,
            image_path=new_img,
            benefits=list(p.benefits or []),
            ingredients=list(p.ingredients or []),
            presentation=list(p.presentation or []),
        ))
    db.commit()
    return RedirectResponse(f"/catalogs/{dst.id}/edit", status_code=303)


@app.post("/catalogs/{catalog_id}/delete")
def delete_catalog(catalog_id: int, db: Session = Depends(get_session)):
    catalog = db.get(Catalog, catalog_id)
    if catalog:
        # Borrar uploads del catálogo.
        folder = UPLOADS_DIR / f"catalog_{catalog_id}"
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
        db.delete(catalog)
        db.commit()
    return RedirectResponse("/", status_code=303)


# ─────────────────────────────────────────────────────────────────────────
# Edición del catálogo
# ─────────────────────────────────────────────────────────────────────────
def _get_catalog_or_404(db: Session, catalog_id: int) -> Catalog:
    catalog = db.get(Catalog, catalog_id)
    if not catalog:
        raise HTTPException(404, "Catálogo no encontrado")
    return catalog


@app.get("/catalogs/{catalog_id}/edit", response_class=HTMLResponse)
def edit_catalog(catalog_id: int, db: Session = Depends(get_session)):
    catalog = _get_catalog_or_404(db, catalog_id)
    return render(
        "catalog_edit.html",
        catalog=catalog,
        templates=list_templates(),
    )


@app.post("/catalogs/{catalog_id}")
def save_catalog(
    catalog_id: int,
    name: str = Form(...),
    template_name: str = Form("editorial"),
    company_name: str = Form(""),
    company_tagline: str = Form(""),
    company_description: str = Form(""),
    company_website: str = Form(""),
    company_phone: str = Form(""),
    company_email: str = Form(""),
    company_country: str = Form(""),
    catalog_title: str = Form(""),
    catalog_subtitle: str = Form(""),
    edition: str = Form(""),
    category_label: str = Form("Salud & Bienestar"),
    theme_primary: str = Form(DEFAULT_THEME["primary"]),
    theme_primary_dark: str = Form(DEFAULT_THEME["primary_dark"]),
    theme_cream: str = Form(DEFAULT_THEME["cream"]),
    theme_accent: str = Form(DEFAULT_THEME["accent"]),
    theme_accent_warm: str = Form(DEFAULT_THEME["accent_warm"]),
    socials_json: str = Form("[]"),
    tips_json: str = Form("[]"),
    db: Session = Depends(get_session),
):
    catalog = _get_catalog_or_404(db, catalog_id)
    catalog.name = name
    catalog.template_name = template_name
    catalog.company_name = company_name
    catalog.company_tagline = company_tagline
    catalog.company_description = company_description
    catalog.company_website = company_website
    catalog.company_phone = company_phone
    catalog.company_email = company_email
    catalog.company_country = company_country
    catalog.catalog_title = catalog_title
    catalog.catalog_subtitle = catalog_subtitle
    catalog.edition = edition
    catalog.category_label = category_label

    theme = dict(catalog.theme or DEFAULT_THEME)
    theme.update({
        "primary": theme_primary,
        "primary_dark": theme_primary_dark,
        "cream": theme_cream,
        "accent": theme_accent,
        "accent_warm": theme_accent_warm,
    })
    catalog.theme = theme

    try:
        catalog.socials = json.loads(socials_json or "[]")
    except json.JSONDecodeError:
        catalog.socials = []
    try:
        catalog.tips = json.loads(tips_json or "[]")
    except json.JSONDecodeError:
        catalog.tips = []

    db.commit()
    return RedirectResponse(f"/catalogs/{catalog_id}/edit", status_code=303)


# ─────────────────────────────────────────────────────────────────────────
# Productos
# ─────────────────────────────────────────────────────────────────────────
def _save_image(catalog_id: int, upload: UploadFile) -> str:
    """Guarda la imagen (optimizada) y retorna la ruta relativa."""
    ext = Path(upload.filename or "img.jpg").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".jpg"
    rel = f"catalog_{catalog_id}/{uuid.uuid4().hex}{ext}"
    dst = UPLOADS_DIR / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    raw = upload.file.read()
    try:
        img = Image.open(io.BytesIO(raw))
        img.thumbnail((1600, 1600))
        save_kwargs: dict = {"optimize": True}
        if ext in {".jpg", ".jpeg"}:
            save_kwargs["quality"] = 88
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
        img.save(dst, **save_kwargs)
    except Exception:
        dst.write_bytes(raw)
    return rel


def _parse_multiline(text: str) -> list[str]:
    return [line.strip(" -•·\t") for line in (text or "").splitlines() if line.strip()]


@app.post("/catalogs/{catalog_id}/products")
def create_product(
    catalog_id: int,
    name: str = Form(...),
    code: str = Form(""),
    tagline: str = Form(""),
    description: str = Form(""),
    price_usd: float = Form(0.0),
    usage: str = Form(""),
    benefits: str = Form(""),
    ingredients: str = Form(""),
    presentation: str = Form(""),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_session),
):
    catalog = _get_catalog_or_404(db, catalog_id)
    max_order = max((p.sort_order for p in catalog.products), default=-1)
    image_rel = ""
    if image is not None and image.filename:
        image_rel = _save_image(catalog_id, image)
    product = Product(
        catalog_id=catalog_id,
        sort_order=max_order + 1,
        code=code or f"{max_order + 2:02d}",
        name=name,
        tagline=tagline,
        description=description,
        price_usd=price_usd or 0.0,
        usage=usage,
        image_path=image_rel,
        benefits=_parse_multiline(benefits),
        ingredients=_parse_multiline(ingredients),
        presentation=_parse_multiline(presentation),
    )
    db.add(product)
    db.commit()
    return RedirectResponse(f"/catalogs/{catalog_id}/edit#productos", status_code=303)


@app.get("/catalogs/{catalog_id}/products/{product_id}/edit", response_class=HTMLResponse)
def edit_product_form(
    catalog_id: int, product_id: int,
    db: Session = Depends(get_session),
):
    catalog = _get_catalog_or_404(db, catalog_id)
    product = db.get(Product, product_id)
    if not product or product.catalog_id != catalog_id:
        raise HTTPException(404)
    return render("product_edit.html", catalog=catalog, product=product)


@app.post("/catalogs/{catalog_id}/products/{product_id}")
def update_product(
    catalog_id: int,
    product_id: int,
    name: str = Form(...),
    code: str = Form(""),
    tagline: str = Form(""),
    description: str = Form(""),
    price_usd: float = Form(0.0),
    usage: str = Form(""),
    benefits: str = Form(""),
    ingredients: str = Form(""),
    presentation: str = Form(""),
    image: Optional[UploadFile] = File(None),
    remove_image: str = Form(""),
    db: Session = Depends(get_session),
):
    product = db.get(Product, product_id)
    if not product or product.catalog_id != catalog_id:
        raise HTTPException(404)
    product.name = name
    product.code = code or product.code
    product.tagline = tagline
    product.description = description
    product.price_usd = price_usd or 0.0
    product.usage = usage
    product.benefits = _parse_multiline(benefits)
    product.ingredients = _parse_multiline(ingredients)
    product.presentation = _parse_multiline(presentation)
    if remove_image:
        if product.image_path:
            old = UPLOADS_DIR / product.image_path
            if old.exists():
                old.unlink(missing_ok=True)
        product.image_path = ""
    if image is not None and image.filename:
        if product.image_path:
            old = UPLOADS_DIR / product.image_path
            if old.exists():
                old.unlink(missing_ok=True)
        product.image_path = _save_image(catalog_id, image)
    db.commit()
    return RedirectResponse(f"/catalogs/{catalog_id}/edit#productos", status_code=303)


@app.post("/catalogs/{catalog_id}/products/{product_id}/delete")
def delete_product(
    catalog_id: int, product_id: int,
    db: Session = Depends(get_session),
):
    product = db.get(Product, product_id)
    if product and product.catalog_id == catalog_id:
        if product.image_path:
            old = UPLOADS_DIR / product.image_path
            if old.exists():
                old.unlink(missing_ok=True)
        db.delete(product)
        db.commit()
    return RedirectResponse(f"/catalogs/{catalog_id}/edit#productos", status_code=303)


@app.post("/catalogs/{catalog_id}/products/{product_id}/move")
def move_product(
    catalog_id: int, product_id: int,
    direction: str = Form("up"),
    db: Session = Depends(get_session),
):
    catalog = _get_catalog_or_404(db, catalog_id)
    items = sorted(catalog.products, key=lambda p: p.sort_order)
    idx = next((i for i, p in enumerate(items) if p.id == product_id), -1)
    if idx < 0:
        raise HTTPException(404)
    if direction == "up" and idx > 0:
        items[idx - 1], items[idx] = items[idx], items[idx - 1]
    elif direction == "down" and idx < len(items) - 1:
        items[idx + 1], items[idx] = items[idx], items[idx + 1]
    for i, p in enumerate(items):
        p.sort_order = i
    db.commit()
    return RedirectResponse(f"/catalogs/{catalog_id}/edit#productos", status_code=303)


# ─────────────────────────────────────────────────────────────────────────
# Preview & PDF
# ─────────────────────────────────────────────────────────────────────────
@app.get("/catalogs/{catalog_id}/preview", response_class=HTMLResponse)
def preview(catalog_id: int, db: Session = Depends(get_session)):
    catalog = _get_catalog_or_404(db, catalog_id)
    return render("preview.html", catalog=catalog)


@app.get("/catalogs/{catalog_id}/pdf")
def catalog_pdf(
    catalog_id: int,
    inline: int = 0,
    db: Session = Depends(get_session),
):
    catalog = _get_catalog_or_404(db, catalog_id)
    pdf_bytes = render_pdf(catalog)
    safe_name = (catalog.name or "catalogo").replace(" ", "-").lower()
    disposition = "inline" if inline else "attachment"
    headers = {
        "Content-Disposition": f'{disposition}; filename="{safe_name}.pdf"',
    }
    return Response(pdf_bytes, media_type="application/pdf", headers=headers)
