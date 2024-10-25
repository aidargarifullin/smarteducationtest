# Тестовое задание для Smarteducation

## Система управления задачами

Код реализован на стеке **Django + DRF**.

### Инструкции по запуску

1. Создать виртуальное окружение.
2. Установить все пакеты из файла `requirements.txt`.
3. Запустить миграции.

Для удобства тестирования добавлена **миграция с предзаполненными пользователями и задачами**.

### Запуск тестов

```bash
python manage.py test
```

В качестве СУБД использовался **sqlite** для простоты тестирования.

### Описание реализации

Система представляет собой приложение с двумя модулями: **Tasks** для задач, комментариев и работы с файлами и **Users** для регистрации пользователей в системе.
Все манипуляции с данными осуществляются через **API** встроенного механизма **DRF**. 

### Задачи /tasks/

В блоке задач реализован CRUD функционал и дополнительно добавлены проверки на возможность редактирования только автором задачи или пользователем, на которого она назначена.

### Комментарии /comments/

Реализован CRUD функционал. Рекомендуется расширить модель ссылкой на родителя, для возможностей отвечать на комментарии в задаче

### Файлы /tasks/{id}/upload_files/

Был реализован функционал прикрепления нескольких файлов к задаче. Дополнительно добавлена проверка  на максимальный размер файла 5Мб

### Юзеры /signup/

Был реализован функционал регистрации новых пользователей

### Аутентификация /token/

Для аутентификации использовался протокол JWT

### Фильтрация и сортировка

В задачи добавлена сортировка по умолчанию по дедлайну и фильтрация с использованием библиотеки **django filter**, которая позволяет гибко реализовать фильтрацию записей совместно с DRF

### API /swagger/ 

Для удобства работы с **API** в приложении добавлена библиотека **drf-yasg**. 

### Тесты

Реализовано **18 тестов**, которые покрывают все основные функции системы: аутентификация, создание записей, работа с файлами и регистрация пользователей. Дополнительно добавлен интеграционный тест с юскейсом входа в систему и добавления задач

### Тестирование через swagger

Для тестирования задач из интерфейса свагера, необходимо сначала вызвать метод **/token/** для получения ключа, скопировать его в блок аутентификации сверху в виде **Bearer <token>**. После этого все **API** станут доступны.
