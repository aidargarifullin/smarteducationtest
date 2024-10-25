from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from apps.tasks.models import Task, Comment, TaskFile
from apps.tasks.views import MAX_FILE_SIZE


class JWTAuthTests(APITestCase):
    """
    Тесты для аутентификации (JWT)
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_token_obtain(self):
        response = self.client.post('/token/', {'username': 'testuser', 'password': 'testpass'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_refresh(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post('/token/refresh/', {'refresh': str(refresh)})
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_protected_route_without_token(self):
        response = self.client.get('/tasks/')
        self.assertEqual(response.status_code, 401)

    def test_protected_route_with_token(self):
        refresh = RefreshToken.for_user(self.user)
        access = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        response = self.client.get('/tasks/')
        self.assertEqual(response.status_code, 200)


class TaskTests(APITestCase):
    """
    Тесты для задач CRUD
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.assignee = User.objects.create_user(username='assignee', password='testpass')
        self.task = Task.objects.create(
            title="Test Task",
            description="Test Description",
            created_by=self.user,
            assigned_to=self.assignee
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_create_task(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post('/tasks/', {
            'title': 'New Task',
            'description': 'New Description',
            'assigned_to': self.assignee.id
        })
        self.assertEqual(response.status_code, 201)

    def test_update_task(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.put(f'/tasks/{self.task.id}/', {
            'title': 'Updated Task',
            'description': 'Updated Description',
            'assigned_to': self.assignee.id,
            'is_completed': True
        })
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task')

    def test_delete_task(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.delete(f'/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, 204)

    def test_complete_task(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.patch(f'/tasks/{self.task.id}/', {'is_completed': True})
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)


class CommentTests(APITestCase):
    """
     Тесты для комментариев CRUD
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.task = Task.objects.create(
            title="Test Task",
            description="Test Description",
            created_by=self.user
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_add_comment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post('/comments/', {
            'task_id': self.task.id,
            'content': 'This is a test comment'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.filter(task=self.task).count(), 1)

    def test_add_comment_without_authentication(self):
        response = self.client.post('/comments/', {
            'task_id': self.task.id,
            'content': 'This is a test comment'
        })
        self.assertEqual(response.status_code, 401)


class TaskPermissionTests(APITestCase):
    """
    Тесты на права доступа: редактирование задачи пользователем, которые не является автором или назначенным
    """

    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='testpass1')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass2')
        self.task = Task.objects.create(
            title="Task for User1",
            description="Description",
            created_by=self.user1
        )
        self.access_token_user1 = str(RefreshToken.for_user(self.user1).access_token)
        self.access_token_user2 = str(RefreshToken.for_user(self.user2).access_token)

    def test_update_task_by_non_creator(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token_user2}')
        response = self.client.put(f'/tasks/{self.task.id}/', {
            'title': 'Changed by User2'
        })
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_update_task_by_creator(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token_user1}')
        response = self.client.put(f'/tasks/{self.task.id}/', {
            'title': 'Changed by User1'
        })
        self.assertEqual(response.status_code, 200)


class TaskManagementIntegrationTests(APITestCase):
    """
    Юзкейс входа в систему и создания задачи с комментарием
    """

    def setUp(self):
        # Создаем двух пользователей
        self.user1 = User.objects.create_user(username='testuser1', password='testpass1')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass2')

        # Создаем JWT токены для каждого пользователя
        self.refresh_token_user1 = RefreshToken.for_user(self.user1)
        self.refresh_token_user2 = RefreshToken.for_user(self.user2)
        self.access_token_user1 = str(self.refresh_token_user1.access_token)
        self.access_token_user2 = str(self.refresh_token_user2.access_token)

    def test_task_lifecycle(self):
        """
        Этот тест проверяет весь жизненный цикл задачи: от создания до комментария.
        """
        # 1. Аутентификация: получение JWT токенов
        response = self.client.post('/token/', {'username': 'testuser1', 'password': 'testpass1'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        # 2. Создание задачи от user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token_user1}')
        response = self.client.post('/tasks/', {
            'title': 'New Task',
            'description': 'Task Description',
            'assigned_to': self.user1.id
        })
        self.assertEqual(response.status_code, 201)
        task_id = response.data['id']

        # Проверяем, что задача создалась
        task = Task.objects.get(id=task_id)
        self.assertEqual(task.title, 'New Task')
        self.assertEqual(task.created_by, self.user1)
        self.assertEqual(task.assigned_to, self.user1)

        # 3. Добавление комментария к задаче user2
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token_user2}')
        response = self.client.post('/comments/', {
            'task_id': task_id,
            'content': 'This is a test comment by user2'
        })
        self.assertEqual(response.status_code, 201)

        # Проверяем, что комментарий добавлен
        self.assertEqual(Comment.objects.filter(task=task_id).count(), 1)
        comment = Comment.objects.get(task_id=task_id)
        self.assertEqual(comment.content, 'This is a test comment by user2')
        self.assertEqual(comment.author, self.user2)

        # 4. Попытка изменения задачи user2 — должно быть запрещено
        response = self.client.put(f'/tasks/{task_id}/', {
            'title': 'Changed by user2'
        })
        self.assertEqual(response.status_code, 403)

        # 5. Обновление задачи владельцем (user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token_user1}')
        response = self.client.put(f'/tasks/{task_id}/', {
            'title': 'Updated Task by user1',
            'description': 'Updated Description',
            'assigned_to': self.user2.id
        })
        self.assertEqual(response.status_code, 200)

        # Проверяем, что задача обновлена
        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated Task by user1')

        # 6. Пометка задачи как выполненной
        response = self.client.patch(f'/tasks/{task_id}/', {'is_completed': True})
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertTrue(task.is_completed)


class TaskFileUploadTests(APITestCase):
    """
    Тесты для загрузки файлов
    """

    def setUp(self):
        # Создаем тестового пользователя и задачу
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            created_by=self.user
        )
        # jwt
        refresh_token = RefreshToken.for_user(self.user)
        self.access_token = str(refresh_token.access_token)

        self.url = f'/tasks/{self.task.id}/upload_files/'

    def test_upload_valid_file(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        # Создаем тестовый файл, размер которого меньше 5 MB
        file = SimpleUploadedFile("testfile.txt", b"file_content", content_type="text/plain")

        # Отправляем POST запрос на загрузку файла
        response = self.client.post(self.url, {'files': file}, format='multipart')

        # Проверяем, что файл был успешно загружен
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TaskFile.objects.filter(task=self.task).count(), 1)

    def test_upload_file_too_large(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        # Создаем файл, который превышает лимит в 5 MB
        large_file_content = b"a" * (MAX_FILE_SIZE + 10)  # 5 MB + 10 байт
        large_file = SimpleUploadedFile("largefile.txt", large_file_content, content_type="text/plain")

        # Отправляем POST запрос с файлом, превышающим лимит
        response = self.client.post(self.url, {'files': large_file}, format='multipart')

        # Проверяем, что сервер вернул ошибку 400 Bad Request
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertEqual(TaskFile.objects.filter(task=self.task).count(), 0)

    def test_upload_multiple_files(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        # Создаем два файла, которые меньше лимита
        file1 = SimpleUploadedFile("file1.txt", b"content1", content_type="text/plain")
        file2 = SimpleUploadedFile("file2.txt", b"content2", content_type="text/plain")

        # Отправляем POST запрос с двумя файлами
        response = self.client.post(self.url, {'files': [file1, file2]}, format='multipart')

        # Проверяем успешный ответ и наличие файлов в базе данных
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TaskFile.objects.filter(task=self.task).count(), 2)

    def test_upload_files_unauthorized(self):
        # Выходим из системы, чтобы проверить неавторизованный запрос
        self.client.logout()

        file = SimpleUploadedFile("testfile.txt", b"file_content", content_type="text/plain")
        response = self.client.post(self.url, {'files': file}, format='multipart')

        # Проверяем, что сервер возвращает ошибку 401 Unauthorized
        self.assertEqual(response.status_code, 401)
