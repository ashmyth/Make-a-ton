"""Generates printable and downloadable PDF documents for Invoices.
Uses xhtml2pdf if installed; otherwise generates a clean standard PDF 1.4 document.
"""
from io import BytesIO
from decimal import Decimal
from django.conf import settings
from django.template.loader import render_to_string


def _build_minimal_pdf_bytes(invoice, company_name: str) -> bytes:
    """Generates standard compliant PDF 1.4 binary data without external C-libraries."""
    # Collect invoice details
    inv_num = invoice.invoice_number
    cust_name = invoice.customer_name or getattr(invoice.customer, "display_name", "Valued Customer")
    cust_email = invoice.customer_email or getattr(invoice.customer, "email", "")
    issue_date = str(invoice.issue_date)
    due_date = str(invoice.due_date)
    curr = invoice.currency
    subtotal = f"{curr} {invoice.subtotal}"
    tax = f"{curr} {invoice.tax_total}"
    total = f"{curr} {invoice.total}"
    balance = f"{curr} {invoice.balance_due}"

    lines_text = []
    lines_text.append(f"INVOICE: {inv_num}")
    lines_text.append(f"ISSUER: {company_name}")
    lines_text.append(f"DATE: {issue_date}    DUE: {due_date}")
    lines_text.append(f"BILL TO: {cust_name} ({cust_email})")
    lines_text.append("-" * 55)
    lines_text.append("ITEMS:")

    for line in invoice.lines.all():
        desc = line.description[:35]
        qty = f"{line.quantity}x"
        price = f"{curr} {line.unit_price}"
        ltotal = f"{curr} {line.line_total}"
        lines_text.append(f"  * {desc:<35} {qty:>6} {price:>12} {ltotal:>12}")

    lines_text.append("-" * 55)
    lines_text.append(f"SUBTOTAL: {subtotal}")
    lines_text.append(f"TAX TOTAL: {tax}")
    lines_text.append(f"TOTAL AMOUNT: {total}")
    lines_text.append(f"BALANCE DUE: {balance}")
    lines_text.append(f"STATUS: {invoice.status.upper()}")

    # Construct PDF Stream
    content_stream = ["BT", "/F1 12 Tf", "50 750 Td", "16 TL"]
    for l in lines_text:
        # Escape parenthesis
        safe_line = l.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content_stream.append(f"({safe_line}) '")
    content_stream.append("ET")
    stream_data = "\n".join(content_stream).encode("latin1", "replace")

    stream_len = len(stream_data)

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets = []

    # Obj 1: Catalog
    offsets.append(len(pdf))
    pdf.extend(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    # Obj 2: Pages
    offsets.append(len(pdf))
    pdf.extend(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

    # Obj 3: Page
    offsets.append(len(pdf))
    pdf.extend(
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> "
        b"/Contents 5 0 R >>\nendobj\n"
    )

    # Obj 4: Font
    offsets.append(len(pdf))
    pdf.extend(b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n")

    # Obj 5: Stream
    offsets.append(len(pdf))
    pdf.extend(f"5 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("latin1"))
    pdf.extend(stream_data)
    pdf.extend(b"\nendstream\nendobj\n")

    # xref
    xref_offset = len(pdf)
    pdf.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for off in offsets:
        pdf.extend(f"{off:010d} 00000 n \n".encode("latin1"))

    # trailer
    pdf.extend(
        f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1")
    )

    return bytes(pdf)


def render_invoice_pdf(invoice) -> bytes:
    """Renders the given Invoice model instance to PDF bytes."""
    company_name = getattr(settings, "BILLING_COMPANY_NAME", "Brightloop")

    try:
        from xhtml2pdf import pisa
        html_content = render_to_string(
            "billing/invoice_pdf.html",
            {
                "invoice": invoice,
                "company_name": company_name,
            },
        )
        result_stream = BytesIO()
        pdf = pisa.CreatePDF(html_content, dest=result_stream)
        if not pdf.err:
            return result_stream.getvalue()
    except (ImportError, Exception):
        pass

    # High-reliability fallback
    return _build_minimal_pdf_bytes(invoice, company_name)

