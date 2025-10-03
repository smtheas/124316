from django.db import models

# Пользователи
class Users(models.Model):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("admin", "Administrator"),
    ]
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    date_joined = models.DateTimeField(auto_now_add=True)

# Темы из базы
class Topic(models.Model):
    WORK_TYPES = [
        ("research", "Research"),
        ("startup", "Startup"),
        ("development", "Development"),
    ]

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    author = models.CharField(max_length=255)
    subject_area = models.CharField(max_length=100)
    work_type = models.CharField(max_length=20, choices=WORK_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

# Шаблоны генерации
class Template(models.Model):
    id = models.AutoField(primary_key=True)
    text = models.CharField(max_length=255)
    work_type = models.CharField(max_length=20, choices=Topic.WORK_TYPES)

# Ключевые слова
class Keyword(models.Model):
    id = models.AutoField(primary_key=True)
    word = models.CharField(max_length=100)
    subject_area = models.CharField(max_length=100)

# Сгенерированные темы
class GeneratedTopic(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    work_type = models.CharField(max_length=20, choices=Topic.WORK_TYPES)
    subject_area = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

# Избранное
class Favorite(models.Model):
    id = models.AutoField(primary_key=True)
    if_source = models.IntegerField()
    title = models.CharField(max_length=255)
    work_type = models.CharField(max_length=20, choices=Topic.WORK_TYPES)
    subject_area = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
