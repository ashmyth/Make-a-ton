from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

from .services import build_workbook


@staff_member_required
def download_register(request):
    """Always-fresh workbook straight from DB."""
    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp["Content-Disposition"] = 'attachment; filename="purchase_register.xlsx"'
    build_workbook().save(resp)
    return resp
