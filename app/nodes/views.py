"""Views for the nodes app."""

from rest_framework import generics, permissions

from .models import Node
from .serializers import NodePublicSerializer


class NodeListView(generics.ListAPIView):
    """Public API endpoint listing active nodes."""

    queryset = Node.objects.filter(is_active=True)
    serializer_class = NodePublicSerializer
    permission_classes = [permissions.AllowAny]
