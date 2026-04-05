from __future__ import annotations
"""Carga el catálogo inicial 'Salud & Bienestar' a partir de app/products.py."""
import shutil
import sys
import uuid
from pathlib import Path

# Permitir importar el parser existente en ../app
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "app"))

import products as legacy_products  # noqa: E402
import config as legacy_config  # noqa: E402

from db import init_db, SessionLocal, UPLOADS_DIR  # noqa: E402
from models import Catalog, Product, DEFAULT_THEME, DEFAULT_TIPS  # noqa: E402


CATALOG_NAME = "Salud & Bienestar 2026"


def seed() -> None:
    init_db()
    db = SessionLocal()

    existing = db.query(Catalog).filter(Catalog.name == CATALOG_NAME).first()
    if existing:
        print(f"⚠ Ya existe un catálogo '{CATALOG_NAME}' (id={existing.id}). Abortando.")
        return

    company = legacy_config.COMPANY
    socials = [
        {"label": s.label, "handle": s.handle, "url": s.url}
        for s in legacy_config.SOCIALS
    ]

    catalog = Catalog(
        name=CATALOG_NAME,
        template_name="editorial",
        company_name=company.name,
        company_tagline=company.tagline,
        company_description=company.description,
        company_website=company.website,
        company_phone=company.phone,
        company_email=company.email,
        company_country=company.country,
        catalog_title=company.catalog_title,
        catalog_subtitle=company.catalog_subtitle,
        edition=company.edition,
        category_label="Salud & Bienestar",
        theme=dict(DEFAULT_THEME),
        socials=socials,
        tips=list(DEFAULT_TIPS),
    )
    db.add(catalog)
    db.flush()

    loaded = legacy_products.load_products()
    print(f"  → {len(loaded)} productos parseados")

    for idx, p in enumerate(loaded):
        image_rel = ""
        if p.image_path and p.image_path.exists():
            ext = p.image_path.suffix.lower() or ".jpg"
            rel = f"catalog_{catalog.id}/{uuid.uuid4().hex}{ext}"
            dst_abs = UPLOADS_DIR / rel
            dst_abs.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p.image_path, dst_abs)
            image_rel = rel

        db.add(Product(
            catalog_id=catalog.id,
            sort_order=idx,
            code=p.code,
            name=p.name,
            tagline=p.tagline,
            description=p.description,
            price_usd=p.price_usd,
            usage=p.usage,
            image_path=image_rel,
            benefits=list(p.benefits),
            ingredients=list(p.ingredients),
            presentation=list(p.presentation),
        ))
        print(f"    ✔ {p.name}")

    db.commit()
    print(f"✔ Catálogo sembrado (id={catalog.id})")


if __name__ == "__main__":
    seed()
