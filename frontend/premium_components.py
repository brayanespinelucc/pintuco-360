"""Premium presentation components for COLORLINK.

All components are passive, escape untrusted record data, and render only data
returned by the existing role-authorized APIs. They never make requests or write
session state. Original tables and native forms remain available in the app.
"""
from __future__ import annotations

from html import escape
from typing import Mapping, Sequence

import streamlit as st


def _safe(value: object) -> str:
    return escape(str(value) if value is not None else "", quote=True)


def record_gallery(
    items: Sequence[Mapping[str, object]],
    *,
    title_key: str,
    subtitle_key: str | None = None,
    badge_key: str | None = None,
    detail_keys: Sequence[tuple[str, str]] = (),
    max_items: int = 9,
    heading: str | None = None,
) -> None:
    """Responsive summary cards; no invented counts, statuses, or interactions."""
    if not items:
        return
    cards = []
    for item in items[:max(1, min(max_items, 24))]:
        name = str(item.get(title_key) or "Sin título")
        subtitle = item.get(subtitle_key, "") if subtitle_key else ""
        badge = item.get(badge_key, "") if badge_key else ""
        meta = "".join(
            '<span class="cl-record-meta"><small>' + _safe(label) + '</small>'
            '<strong>' + _safe(item.get(field, "—")) + '</strong></span>'
            for label, field in detail_keys
        )
        cards.append(
            '<article class="cl-record-card">'
            '<div class="cl-record-top">'
            '<span class="cl-record-monogram" aria-hidden="true">'
            + _safe(name.strip()[:1].upper() or "•") + '</span>'
            + ('<span class="cl-record-badge">' + _safe(badge) + '</span>' if badge else '')
            + '</div><h3>' + _safe(name) + '</h3>'
            + ('<p class="cl-record-description">' + _safe(subtitle) + '</p>' if subtitle else '')
            + ('<div class="cl-record-footer">' + meta + '</div>' if meta else '')
            + '</article>'
        )
    intro = (
        '<div class="cl-record-gallery-heading"><strong>' + _safe(heading) + '</strong>'
        '<span>' + str(len(items)) + ' registros</span></div>'
        if heading else ''
    )
    overflow = len(items) > max_items
    st.html(
        '<section aria-label="' + _safe(heading or 'Registros disponibles') + '">'
        + intro + '<div class="cl-record-grid">' + "".join(cards) + '</div>'
        + ('<p class="cl-record-more">Mostrando los primeros '
           + str(max_items) + ' registros. Consulta la tabla completa para ver todos.</p>'
           if overflow else '')
        + '</section>'
    )


def step_intro(index: str, headline: str, description: str) -> None:
    """Visual section preface without changing the actual process state."""
    st.html(
        '<header class="cl-step-intro">'
        '<span class="cl-step-number" aria-hidden="true">' + _safe(index) + '</span>'
        '<div><h3>' + _safe(headline) + '</h3><p>' + _safe(description)
        + '</p></div></header>'
    )
