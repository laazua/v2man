from rest_framework import generics, permissions
from .models import Node
from .serializers import NodeSerializer


class NodeListView(generics.ListAPIView):
    queryset = Node.objects.filter(is_active=True)
    serializer_class = NodeSerializer
    permission_classes = [permissions.AllowAny]
