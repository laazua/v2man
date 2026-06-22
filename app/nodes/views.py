from rest_framework import generics, permissions
from .models import Node
from .serializers import NodePublicSerializer


class NodeListView(generics.ListAPIView):
    queryset = Node.objects.filter(is_active=True)
    serializer_class = NodePublicSerializer
    permission_classes = [permissions.AllowAny]
