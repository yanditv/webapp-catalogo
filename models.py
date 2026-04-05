from __future__ import annotations
"""Modelos ORM del webapp."""
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON, DateTime, Float, ForeignKey, Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


DEFAULT_THEME: dict[str, str] = {
    "primary": "#2E5D4A",
    "primary_dark": "#1B3B2F",
    "primary_soft": "#4A7B63",
    "sage": "#B8CBB4",
    "cream": "#F5EFE2",
    "cream_dark": "#E8DFC8",
    "accent": "#B8893A",
    "accent_warm": "#C17D4A",
    "paper": "#FDFAF3",
    "ink": "#1E2D24",
    "muted": "#7A8C80",
    "rule": "#D8D1C2",
}

DEFAULT_TIPS: list[dict[str, str]] = [
    {"title": "Usa según etiqueta",
     "body": "Respeta siempre las indicaciones de dosis y frecuencia impresas en el envase de cada producto."},
    {"title": "Fuera del alcance de niños",
     "body": "Mantén los suplementos y cremas en un lugar seguro, lejos del alcance de menores y mascotas."},
    {"title": "Conservación adecuada",
     "body": "Almacena en un lugar fresco, seco y sin exposición directa al sol para preservar la calidad."},
    {"title": "Consulta a un profesional",
     "body": "Ante cualquier condición médica, embarazo o tratamiento en curso, pide orientación antes de consumir."},
    {"title": "Precios de referencia",
     "body": "Los valores publicados pueden variar según disponibilidad y promociones vigentes."},
]


class Catalog(Base):
    __tablename__ = "catalogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    template_name: Mapped[str] = mapped_column(String(50), default="editorial")

    # Empresa
    company_name: Mapped[str] = mapped_column(String(200), default="")
    company_tagline: Mapped[str] = mapped_column(String(300), default="")
    company_description: Mapped[str] = mapped_column(Text, default="")
    company_website: Mapped[str] = mapped_column(String(200), default="")
    company_phone: Mapped[str] = mapped_column(String(50), default="")
    company_email: Mapped[str] = mapped_column(String(200), default="")
    company_country: Mapped[str] = mapped_column(String(100), default="")
    catalog_title: Mapped[str] = mapped_column(String(200), default="")
    catalog_subtitle: Mapped[str] = mapped_column(String(200), default="")
    edition: Mapped[str] = mapped_column(String(100), default="")
    category_label: Mapped[str] = mapped_column(String(100), default="Salud & Bienestar")

    # Estructuras libres
    theme: Mapped[dict[str, Any]] = mapped_column(JSON, default=lambda: dict(DEFAULT_THEME))
    socials: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    tips: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=lambda: list(DEFAULT_TIPS))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="catalog",
        cascade="all, delete-orphan",
        order_by="Product.sort_order",
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    catalog_id: Mapped[int] = mapped_column(ForeignKey("catalogs.id", ondelete="CASCADE"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    code: Mapped[str] = mapped_column(String(20), default="")
    name: Mapped[str] = mapped_column(String(200))
    tagline: Mapped[str] = mapped_column(String(400), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    price_usd: Mapped[float] = mapped_column(Float, default=0.0)
    usage: Mapped[str] = mapped_column(Text, default="")
    image_path: Mapped[str] = mapped_column(String(500), default="")  # relativo a data/uploads

    benefits: Mapped[list[str]] = mapped_column(JSON, default=list)
    ingredients: Mapped[list[str]] = mapped_column(JSON, default=list)
    presentation: Mapped[list[str]] = mapped_column(JSON, default=list)

    catalog: Mapped[Catalog] = relationship("Catalog", back_populates="products")

    @property
    def price_label(self) -> str:
        return f"${self.price_usd:,.2f}" if self.price_usd else ""
