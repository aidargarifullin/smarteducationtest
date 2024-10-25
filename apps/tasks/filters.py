from django_filters import rest_framework as filters
from .models import Task


class TaskFilter(filters.FilterSet):
    """
    Фильтрация задач по основным параметрам
    """
    is_completed = filters.BooleanFilter(field_name='is_completed')
    assigned_to = filters.CharFilter(field_name='assigned_to__username')
    deadline = filters.DateFromToRangeFilter(field_name='deadline')

    class Meta:
        model = Task
        fields = ['is_completed', 'assigned_to', 'deadline']
