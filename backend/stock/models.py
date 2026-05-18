from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid


class StockItem(models.Model):
    """
    MDF Stok Kartı.
    SKU otomatik oluşturulur. min_threshold altına düşünce uyarı verilir.
    """

    class Unit(models.TextChoices):
        ADET = 'adet', 'Adet'
        M2 = 'm2', 'm²'
        KG = 'kg', 'Kilogram'

    sku = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name='Stok Kodu (SKU)',
    )
    name = models.CharField(max_length=300, verbose_name='Ürün Adı')
    description = models.TextField(blank=True, default='', verbose_name='Açıklama')
    unit = models.CharField(
        max_length=10,
        choices=Unit.choices,
        default=Unit.ADET,
        verbose_name='Birim',
    )
    current_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Mevcut Miktar',
    )
    min_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Minimum Eşik',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Stok Kalemi'
        verbose_name_plural = 'Stok Kalemleri'
        ordering = ['name']

    def __str__(self):
        return f"[{self.sku}] {self.name}"

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self._generate_sku()
        super().save(*args, **kwargs)

    def _generate_sku(self):
        prefix = 'MDF'
        short_uuid = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{short_uuid}"

    @property
    def is_critical(self):
        """Stok minimum eşiğin altında mı?"""
        return self.current_quantity <= self.min_threshold

    @property
    def stock_status(self):
        if self.current_quantity <= 0:
            return 'out_of_stock'
        if self.is_critical:
            return 'critical'
        return 'normal'


class StockTransaction(models.Model):
    """
    Stok Hareketi — giriş veya çıkış.
    Çıkış işlemlerinde select_for_update() ile race condition koruması sağlanır.
    """

    class TransactionType(models.TextChoices):
        ENTRY = 'entry', 'Giriş'
        EXIT = 'exit', 'Çıkış'

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Stok Kalemi',
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        verbose_name='İşlem Tipi',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Miktar',
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_transactions',
        verbose_name='İşlemi Yapan',
    )
    notes = models.TextField(blank=True, default='', verbose_name='Notlar')
    usage_location = models.CharField(
        max_length=200, blank=True, default='', verbose_name='Kullanım Yeri'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Stok Hareketi'
        verbose_name_plural = 'Stok Hareketleri'
        ordering = ['-created_at']

    def __str__(self):
        arrow = '📥' if self.transaction_type == 'entry' else '📤'
        return f"{arrow} {self.stock_item.name} — {self.quantity}"

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'Miktar 0\'dan büyük olmalıdır.'})

    @classmethod
    def create_entry(cls, stock_item_id, quantity, user, notes='', usage_location=''):
        """Stok girişi — miktarı artırır."""
        with transaction.atomic():
            item = StockItem.objects.select_for_update().get(id=stock_item_id)
            tx = cls.objects.create(
                stock_item=item,
                transaction_type=cls.TransactionType.ENTRY,
                quantity=quantity,
                performed_by=user,
                notes=notes,
                usage_location=usage_location,
            )
            item.current_quantity += quantity
            item.save(update_fields=['current_quantity', 'updated_at'])
            return tx

    @classmethod
    def create_exit(cls, stock_item_id, quantity, user, notes='', usage_location=''):
        """
        Stok çıkışı — select_for_update() ile kilitleyerek race condition engeller.
        Yetersiz stokta ValidationError fırlatır.
        """
        with transaction.atomic():
            item = StockItem.objects.select_for_update().get(id=stock_item_id)
            if item.current_quantity < quantity:
                raise ValidationError(
                    f'Yetersiz stok. Mevcut: {item.current_quantity}, '
                    f'İstenen: {quantity}'
                )
            tx = cls.objects.create(
                stock_item=item,
                transaction_type=cls.TransactionType.EXIT,
                quantity=quantity,
                performed_by=user,
                notes=notes,
                usage_location=usage_location,
            )
            item.current_quantity -= quantity
            item.save(update_fields=['current_quantity', 'updated_at'])
            return tx

