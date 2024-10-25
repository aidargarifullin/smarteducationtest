from rest_framework import serializers
from .models import Task, Comment, TaskFile
from django.contrib.auth.models import User


class CommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для комментариев
    """
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at']


class TaskFileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для файлов задач
    """

    class Meta:
        model = TaskFile
        fields = ['id', 'file', 'uploaded_at']


class TaskSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получениия задач
    """
    created_by = serializers.ReadOnlyField(source='created_by.username')
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), allow_null=True)
    comments = CommentSerializer(many=True, read_only=True)
    files = TaskFileSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'created_by', 'assigned_to', 'is_completed', 'created_at',
                  'updated_at', 'comments', 'files']


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и редактирования задач
    """
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'assigned_to', 'is_completed']
