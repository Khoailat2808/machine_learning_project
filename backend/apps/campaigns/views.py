"""FR-CAMP-02, 03: xem trước và xuất danh sách chiến dịch (không lưu, FR-CAMP-04 là P1)."""
from datetime import date

from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.customers.views import csv_response
from . import service


def parse(request):
    params = service.CampaignParams(data=request.data)
    if not params.is_valid():
        return None, Response({"errors": {f: " ".join(map(str, msgs)) for f, msgs in params.errors.items()}},
                              status=400)
    return params.validated_data, None


@api_view(["POST"])
def preview(request):
    params, error = parse(request)
    return error or Response(service.preview(params))


@api_view(["POST"])
def export(request):
    """Số dòng CSV = selected của preview: cùng thứ tự VaR giảm dần, cắt phần đầu."""
    params, error = parse(request)
    if error:
        return error
    qs, rows = service.plan(params)
    name = f"chien_dich_{'_'.join(params['segments'])}_{date.today():%Y%m%d}.csv"
    return csv_response(qs[:len(rows)], name, params["spend_pct"])
