from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Özel kullanıcı modeli. Roller: admin, manager, worker.
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        MANAGER = 'manager', 'Manager'
        WORKER = 'worker', 'Worker'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.WORKER,
        verbose_name='Rol',
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Departman',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Kullanıcı'
        verbose_name_plural = 'Kullanıcılar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_manager_role(self):
        return self.role == self.Role.MANAGER


class TeamAssociate(models.Model):
    """
    Hesapsız çalışan — giriş yapamaz ama ekip ataması yapılabilir.
    Saha kayıtları için kullanılır.
    """
    full_name = models.CharField(max_length=200, verbose_name='Ad Soyad')
    department = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Departman',
    )
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Saha Çalışanı'
        verbose_name_plural = 'Saha Çalışanları'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name
