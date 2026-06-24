"""Views for traffic recording and statistics."""

import logging
import math

from django.db.models import Sum
from django.db.models.functions import TruncDate
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User

from .models import TrafficLog
from .serializers import TrafficRecordSerializer

logger = logging.getLogger("business")

MB = 1024 * 1024


class TrafficRecordView(APIView):
    """Admin-only endpoint for recording user traffic data."""

    permission_classes = [permissions.IsAdminUser]

    def post(self, request: Request) -> Response:
        """Record traffic data and update usage counter."""
        serializer = TrafficRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(id=serializer.validated_data["user_id"])
        except User.DoesNotExist:
            return Response(
                {"error": "用户不存在"},
                status=status.HTTP_404_NOT_FOUND,
            )

        log = TrafficLog.objects.create(
            user=user,
            upload_bytes=serializer.validated_data["upload_bytes"],
            download_bytes=serializer.validated_data["download_bytes"],
            node_name=serializer.validated_data.get("node_name", ""),
        )
        total = (
            serializer.validated_data["upload_bytes"]
            + serializer.validated_data["download_bytes"]
        )
        user.traffic_used = (user.traffic_used or 0) + max(
            1, math.ceil(total / MB)
        )
        user.save(update_fields=["traffic_used"])

        logger.info(
            "管理员录入流量: user_id=%s upload=%s download=%s node=%s",
            user.id,
            serializer.validated_data["upload_bytes"],
            serializer.validated_data["download_bytes"],
            serializer.validated_data.get("node_name", ""),
        )
        return Response({"success": True, "id": log.id})


class TrafficStatsView(APIView):
    """User-facing endpoint for viewing personal traffic statistics."""

    def get(self, request: Request) -> Response:
        """Return daily and total traffic breakdown for the user."""
        logs = TrafficLog.objects.filter(user=request.user)
        daily = (
            logs.annotate(date=TruncDate("recorded_at"))
            .values("date")
            .annotate(
                upload=Sum("upload_bytes"),
                download=Sum("download_bytes"),
            )
            .order_by("-date")
        )
        totals = logs.aggregate(
            total_upload=Sum("upload_bytes"),
            total_download=Sum("download_bytes"),
        )
        total_upload = totals["total_upload"] or 0
        total_download = totals["total_download"] or 0
        return Response(
            {
                "daily": [
                    {
                        "date": str(d["date"]),
                        "upload_mb": (
                            round(d["upload"] / MB, 2) if d["upload"] else 0
                        ),
                        "download_mb": (
                            round(d["download"] / MB, 2)
                            if d["download"]
                            else 0
                        ),
                    }
                    for d in daily
                ],
                "total_upload_mb": round(total_upload / MB, 2),
                "total_download_mb": round(total_download / MB, 2),
            }
        )
