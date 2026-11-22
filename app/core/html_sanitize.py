"""Sanitize rich HTML (CKEditor) to mitigate XSS / HTML injection before storage."""
from __future__ import annotations

import bleach

ALLOWED_TAGS = [
    "a", "abbr", "b", "blockquote", "br", "caption", "code", "col", "colgroup",
    "div", "em", "figcaption", "figure", "h1", "h2", "h3", "h4", "h5", "h6",
    "hr", "i", "img", "li", "ol", "p", "pre", "span", "strong", "sub", "sup",
    "table", "tbody", "td", "tfoot", "th", "thead", "tr", "u", "ul",
]

ALLOWED_ATTRIBUTES = {
    "*": ["class", "id"],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
    "col": ["span"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto", "tel"]


def sanitize_html(content: str | None) -> str:
    if not content:
        return ""
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
