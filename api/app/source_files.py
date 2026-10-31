"""Safe public URLs for source papers stored in the paper archive."""

from urllib.parse import quote, urlparse
import re


def source_pdf_url(source_file: str | None, pdf_url: str | None = None) -> str | None:
    """Return an app URL only for a known source archive path.

    ``pdf_url`` is reserved for explicitly curated URLs. Bank ``source_file``
    values are relative paths under ``Old_Questions/`` and are mirrored under
    ``/papers/source`` by scripts/sync-source-pdfs.sh.
    """
    if pdf_url:
        parsed = urlparse(pdf_url)
        if (parsed.scheme in {"https", "http"} and parsed.netloc) or (
            not parsed.scheme and not parsed.netloc and pdf_url.startswith("/papers/")
        ):
            return pdf_url

    if not source_file:
        return None
    path = source_file.replace("\\", "/").strip()
    if path.startswith("pdfs/"):
        path = path[5:]
    parts = path.split("/")
    if (
        not path.startswith("Old_Questions/")
        or not path.lower().endswith(".pdf")
        or any(part in {"", ".", ".."} for part in parts)
    ):
        return None
    return "/papers/source/" + "/".join(quote(part, safe="-_.()") for part in parts)


def figure_image_url(figure_image: str | None) -> str | None:
    """Expose only content-addressed page renders from the synced bank archive."""
    if not figure_image:
        return None
    match = re.fullmatch(r"images/page-renders/([0-9a-f]{20,64}\.png)", figure_image)
    if not match:
        return None
    return "/papers/figures/" + quote(match.group(1), safe=".-_")
