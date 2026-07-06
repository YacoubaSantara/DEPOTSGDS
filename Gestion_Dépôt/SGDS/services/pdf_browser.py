"""
Rendu PDF fidèle au navigateur (Playwright + Chromium headless), pour les
documents dont la mise en page CSS moderne (grid, polices web) n'est pas
correctement interprétée par xhtml2pdf — actuellement les bordereaux de
mouvement (templates/mouvements/bordereau_*.html + static/css/bordereau.css).

Principe : on rend le HTML normalement via Django (render_to_string), on lui
injecte une balise <base> vers une origine fictive, puis on intercepte les
requêtes vers cette origine pour servir les fichiers statiques depuis le
disque (SGDS.templatetags `{% static %}`). Les polices Google Fonts (URLs
absolues) sont laissées passer vers le vrai réseau. Le PDF est ensuite généré
en média "print" (comportement par défaut de Page.pdf()), ce qui déclenche
naturellement les règles @media print déjà présentes dans bordereau.css
(masque la toolbar, force les couleurs de fond).
"""
import mimetypes

_FAKE_ORIGIN = "https://sgds.local"


def render_to_pdf_via_browser(template_name: str, context: dict, *, landscape: bool = False) -> bytes:
    from django.template.loader import render_to_string
    from django.contrib.staticfiles import finders
    from playwright.sync_api import sync_playwright

    html = render_to_string(template_name, context)
    html = html.replace("<head>", f'<head><base href="{_FAKE_ORIGIN}/">', 1)

    def _handle_static(route):
        url = route.request.url
        rel_path = url.split("/static/", 1)[-1] if "/static/" in url else None
        found = finders.find(rel_path) if rel_path else None
        if found:
            content_type, _ = mimetypes.guess_type(found)
            with open(found, "rb") as f:
                route.fulfill(status=200, body=f.read(), content_type=content_type or "application/octet-stream")
        else:
            route.continue_()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.route(f"{_FAKE_ORIGIN}/static/**", _handle_static)
            page.set_content(html, wait_until="networkidle")
            pdf_bytes = page.pdf(format="A4", landscape=landscape, print_background=True)
        finally:
            browser.close()

    return pdf_bytes
