"""Supabase Storage integration for generated PDF files.
Falls back safely to local storage or dummy path if Supabase is unconfigured or in tests.
"""
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)


def upload_invoice_pdf(invoice, pdf_bytes: bytes) -> str:
    """Uploads the invoice PDF bytes to Supabase storage bucket.
    
    Returns the storage path (e.g., 'invoices/2026/INV-2026-00001.pdf').
    """
    supabase_url = getattr(settings, "SUPABASE_URL", os.environ.get("SUPABASE_URL"))
    supabase_key = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
    bucket_name = getattr(settings, "SUPABASE_INVOICE_BUCKET", os.environ.get("SUPABASE_INVOICE_BUCKET", "invoices"))

    file_name = f"{invoice.issue_date.year}/{invoice.invoice_number}.pdf"

    if not supabase_url or not supabase_key:
        logger.warning(
            "Supabase credentials not configured. Skipping remote upload for invoice %s",
            invoice.invoice_number
        )
        return f"local/{file_name}"

    try:
        from supabase import create_client
        supabase = create_client(supabase_url, supabase_key)
        
        # Upload binary directly
        supabase.storage.from_(bucket_name).upload(
            file_name,
            pdf_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        return f"{bucket_name}/{file_name}"
    except Exception as exc:
        logger.error("Failed to upload invoice %s to Supabase storage: %s", invoice.invoice_number, exc)
        raise

