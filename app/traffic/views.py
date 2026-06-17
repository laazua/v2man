from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from django.db.models.functions import TruncDate
from .models import TrafficLog
from users.models import User
from .serializers import TrafficRecordSerializer


class TrafficRecordView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = TrafficRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(id=serializer.validated_data['user_id'])
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        log = TrafficLog.objects.create(
            user=user,
            upload_bytes=serializer.validated_data['upload_bytes'],
            download_bytes=serializer.validated_data['download_bytes'],
            node_name=serializer.validated_data.get('node_name', ''),
        )
        total = serializer.validated_data['upload_bytes'] + serializer.validated_data['download_bytes']
        user.traffic_used = (user.traffic_used or 0) + total // (1024 * 1024)
        user.save(update_fields=['traffic_used'])

        return Response({'success': True, 'id': log.id})


class TrafficStatsView(APIView):
    def get(self, request):
        logs = TrafficLog.objects.filter(user=request.user)
        daily = (
            logs.annotate(date=TruncDate('recorded_at'))
            .values('date')
            .annotate(
                upload=Sum('upload_bytes'),
                download=Sum('download_bytes'),
            )
            .order_by('-date')
        )
        total_upload = logs.aggregate(s=Sum('upload_bytes'))['s'] or 0
        total_download = logs.aggregate(s=Sum('download_bytes'))['s'] or 0
        return Response({
            'daily': [
                {
                    'date': str(d['date']),
                    'upload_mb': round(d['upload'] / (1024 * 1024), 2) if d['upload'] else 0,
                    'download_mb': round(d['download'] / (1024 * 1024), 2) if d['download'] else 0,
                }
                for d in daily
            ],
            'total_upload_mb': round(total_upload / (1024 * 1024), 2),
            'total_download_mb': round(total_download / (1024 * 1024), 2),
        })
