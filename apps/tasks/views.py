from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from apps.tasks.permissions import IsOwnerOrAssignee
from .models import Task, Comment, TaskFile
from .serializers import TaskSerializer, TaskCreateUpdateSerializer, CommentSerializer


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


class TaskViewSet(viewsets.ModelViewSet):
    """

    """
    queryset = Task.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssignee]
    filter_backends = [DjangoFilterBackend]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TaskCreateUpdateSerializer
        return TaskSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_files(self, request, pk=None):
        task = self.get_object()
        files = request.FILES.getlist('files')
        for file in files:
            if file.size > MAX_FILE_SIZE:
                return Response(
                    {'error': f'File "{file.name}" exceeds the maximum allowed size of 5 MB.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            TaskFile.objects.create(task=task, file=file)
        return Response({'status': 'files uploaded'}, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        queryset = super().get_queryset().order_by('deadline')  # Сортировка по дедлайну
        return queryset


class CommentViewSet(viewsets.ModelViewSet):
    """

    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        task = Task.objects.get(id=self.request.data.get('task_id'))
        serializer.save(author=self.request.user, task=task)
