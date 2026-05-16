from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template


def render_to_pdf(template_name: str, context: dict, filename: str = 'document.pdf') -> HttpResponse:
    from xhtml2pdf import pisa
    template = get_template(template_name)
    html = template.render(context)
    buffer = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('utf-8')), buffer, encoding='utf-8')
    if pdf.err:
        return HttpResponse('Erreur de génération PDF.', status=500)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
