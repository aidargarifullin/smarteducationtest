from rest_framework import permissions


class IsOwnerOrAssignee(permissions.BasePermission):
    """
    Ограничение на изменение задачи только ее автором или назнченным
    """
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or obj.assigned_to == request.user
