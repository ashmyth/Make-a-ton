"""Generates printable and downloadable PDF documents for Invoices using xhtml2pdf.
"""
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string
from xhtml2pdf import pisa


def render_invoice_pdf(invoice) -> bytes:
    """Renders the given Invoice model instance to PDF bytes."""
    company_name = getattr(settings, "BILLING_COMPANY_NAME", "Brightloop")
    
    html_content = render_to_string(
        "billing/invoice_pdf.html",
        {
            "invoice": invoice,
            "company_name": company_name,
        },
    )

    result_stream = BytesIO()
    pdf = pisa.CreatePDF(html_content, dest=result_stream)
    
    if pdf.err:
        raise RuntimeError(f"xhtml2pdf error rendering invoice {invoice.invoice_number}: {pdf.err}")

    return result_stream.getvalue()

