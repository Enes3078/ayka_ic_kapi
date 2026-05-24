from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import TeamAssociate


class Team(models.Model):
    """Üretim ekibi."""
    name = models.CharField(max_length=200, unique=True, verbose_name='Ekip Adı')
    department = models.CharField(
        max_length=100, blank=True, default='', verbose_name='Departman'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='teams',
        verbose_name='Üyeler',
    )
    associates = models.ManyToManyField(
        TeamAssociate,
        blank=True,
        related_name='teams',
        verbose_name='Saha Çalışanları',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ekip'
        verbose_name_plural = 'Ekipler'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Sistemde önceden tanımlanmış ürün (katalog) şablonu."""
    code = models.CharField(max_length=100, unique=True, verbose_name='Ürün Kodu (Örn: AY-01)')
    name = models.CharField(max_length=200, verbose_name='Model Adı')
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name='Süre (dk)')
    
    width_mm = models.PositiveIntegerField(null=True, blank=True, verbose_name='En (mm)')
    length_mm = models.PositiveIntegerField(null=True, blank=True, verbose_name='Boy (mm)')
    additional_dimensions = models.CharField(max_length=300, blank=True, default='', verbose_name='Ek Ölçüler')
    
    blade_min_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Bıçak min (mm)')
    blade_max_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Bıçak max (mm)')
    thickness_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Kalınlık (mm)')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Katalog Ürünü'
        verbose_name_plural = 'Katalog Ürünleri'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class WorkflowTemplate(models.Model):
    """Sık kullanılan iş akışı (bayrak yarışı) şablonları."""
    name = models.CharField(max_length=200, unique=True, verbose_name='Şablon Adı')
    steps = models.JSONField(default=list, blank=True, verbose_name='Şablon Adımları (TeamID listesi)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'İş Akışı Şablonu'
        verbose_name_plural = 'İş Akışı Şablonları'
        ordering = ['name']

    def __str__(self):
        return self.name


class Task(models.Model):
    """
    Üretim görevi (Kök obje).
    Her görevin en az 1 ProductLine'ı olmalıdır (serializer seviyesinde zorlanır).
    """

    class Status(models.TextChoices):
        TODO = 'todo', 'Yapılacak'
        IN_PROGRESS = 'in_progress', 'Devam Ediyor'
        DONE = 'done', 'Tamamlandı'

    class Priority(models.TextChoices):
        LOW = 'low', 'Düşük'
        MEDIUM = 'medium', 'Orta'
        HIGH = 'high', 'Yüksek'
        URGENT = 'urgent', 'Acil'

    title = models.CharField(max_length=300, verbose_name='Başlık')
    description = models.TextField(blank=True, default='', verbose_name='Açıklama')

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_tasks',
        verbose_name='Sahibi',
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='Atanan Kişi',
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='Ekip',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
        verbose_name='Durum',
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name='Öncelik',
    )

    start_date = models.DateTimeField(null=True, blank=True, verbose_name='Başlangıç')
    end_date = models.DateTimeField(null=True, blank=True, verbose_name='Bitiş')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='Son Tarih')

    planned_hours = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='Planlanan Saat'
    )
    planned_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name='Planlanan Maliyet'
    )

    # Workflow: Task seviyesinden kaldırıldı, kalem seviyesine alındı.
    # Bu alanları sildik: workflow_team_ids, current_team


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Görev'
        verbose_name_plural = 'Görevler'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"

    def clean(self):
        """Tarih sıralaması kontrolü: start < end < due."""
        errors = {}
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            errors['end_date'] = 'Bitiş tarihi başlangıçtan sonra olmalı.'
        if self.end_date and self.due_date and self.end_date >= self.due_date:
            errors['due_date'] = 'Son tarih, bitiş tarihinden sonra olmalı.'
        if self.start_date and self.due_date and self.start_date >= self.due_date:
            errors['due_date'] = 'Son tarih, başlangıç tarihinden sonra olmalı.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # planned_hours ve planned_cost boş gelirse 0'a set et
        if self.planned_hours is None:
            self.planned_hours = 0
        if self.planned_cost is None:
            self.planned_cost = 0

        # Validasyonu çalıştır
        self.full_clean()
        super().save(*args, **kwargs)


class ProductLine(models.Model):
    """
    Üretim kalemi — her görevin en az 1 kalemi olmalıdır.
    """

    class PlanningMode(models.TextChoices):
        MANUAL = 'manual', 'Manuel'
        FIXED = 'fixed', 'Sabit Süre'

    class UnitType(models.TextChoices):
        ADET = 'adet', 'Adet'
        METRE = 'metre', 'Metre'

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='product_lines',
        verbose_name='Görev',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_lines',
        verbose_name='Katalog Ürünü',
    )
    image_base64 = models.TextField(blank=True, default='', verbose_name='Kalem Görseli (Base64)')
    
    product_name = models.CharField(max_length=300, blank=True, default='', verbose_name='Ürün Adı')
    model_code = models.CharField(max_length=100, verbose_name='Model Kodu')
    variant = models.CharField(max_length=100, blank=True, default='', verbose_name='Varyant')
    dimension = models.CharField(
        max_length=100, blank=True, default='', verbose_name='Ölçü'
    )
    color = models.CharField(
        max_length=100, blank=True, default='', verbose_name='Renk'
    )
    product_color_code = models.CharField(
        max_length=50, blank=True, default='', verbose_name='Renk Kodu'
    )
    blade_depth = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, verbose_name='Bıçak Derinliği'
    )
    
    brief_intro = models.TextField(verbose_name='Kısa Açıklama (1-600 Karakter)', max_length=600, default='')
    
    unit_type = models.CharField(
        max_length=20,
        choices=UnitType.choices,
        default=UnitType.ADET,
        verbose_name='Birim Tipi'
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='Sipariş Adedi')
    qty_produced = models.PositiveIntegerField(default=0, verbose_name='Üretilen')
    
    fire_qty = models.PositiveIntegerField(default=0, verbose_name='Fire Miktarı')
    fire_reason = models.TextField(blank=True, default='', verbose_name='Fire Sebebi')
    fire_image = models.ImageField(upload_to='scrap_images/', blank=True, null=True, verbose_name='Fire Fotoğrafı')

    planning_mode = models.CharField(
        max_length=20,
        choices=PlanningMode.choices,
        default=PlanningMode.MANUAL,
        verbose_name='Planlama Modu',
    )
    unit_duration_minutes = models.PositiveIntegerField(
        default=0, verbose_name='Birim Süre (dk)'
    )
    notes = models.TextField(blank=True, default='', verbose_name='Notlar')

    # İş Akışı (Workflow - Bayrak Yarışı)
    workflow_team_ids = models.JSONField(
        default=list, blank=True, verbose_name='İş Akışı Ekipleri (Sıralı ID Listesi)'
    )
    workflow_stage_targets = models.JSONField(
        default=dict, blank=True, verbose_name='Aşama Hedefleri (TeamID: Hedef Miktar)'
    )
    active_product_index = models.IntegerField(default=0, verbose_name='Aktif Aşama İndeksi')
    stage_done = models.BooleanField(default=False, verbose_name='Üretim Tamamlandı')
    pending_approval = models.BooleanField(default=False, verbose_name='Onay Bekliyor')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Üretim Kalemi'
        verbose_name_plural = 'Üretim Kalemleri'
        ordering = ['id']

    def __str__(self):
        return f"{self.model_code} — {self.quantity} adet"

    @property
    def total_planned_minutes(self):
        """Fixed modda: süre × adet üzerinden toplam dakika."""
        if self.planning_mode == self.PlanningMode.FIXED:
            return self.unit_duration_minutes * self.quantity
        return 0

    @property
    def completion_rate(self):
        """Tamamlanma yüzdesi."""
        if self.quantity == 0:
            return 0
        return round((self.qty_produced / self.quantity) * 100, 1)

    @property
    def current_team_id(self):
        """Şu anki aşamadan sorumlu ekibin ID'si."""
        if self.workflow_team_ids and 0 <= self.active_product_index < len(self.workflow_team_ids):
            return self.workflow_team_ids[self.active_product_index]
        return None

    def get_stage_history(self, stage_index=None):
        """Verilen iş akışı aşamasının en güncel üretim kaydını döner."""
        if stage_index is None:
            stage_index = self.active_product_index
        if not self.workflow_team_ids or stage_index < 0 or stage_index >= len(self.workflow_team_ids):
            return None
        team_id = self.workflow_team_ids[stage_index]
        return self.histories.filter(team_id=team_id).order_by(
            models.F('completed_at').desc(nulls_first=True),
            '-started_at',
        ).first()

    def get_stage_input_quantity(self, stage_index=None):
        """
        Aşamaya gelen miktar.
        İlk ekip sipariş miktarını, sonraki ekipler önceki ekipten çıkan sağlam miktarı işler.
        """
        if stage_index is None:
            stage_index = self.active_product_index
        if stage_index <= 0:
            return self.quantity
        previous_history = self.get_stage_history(stage_index - 1)
        if not previous_history:
            return 0
        return max(0, previous_history.qty_produced_at_stage - previous_history.scrap_qty_at_stage)

    def get_stage_processed_quantity(self, stage_index=None):
        history = self.get_stage_history(stage_index)
        return history.qty_produced_at_stage if history else 0

    def get_stage_scrap_quantity(self, stage_index=None):
        history = self.get_stage_history(stage_index)
        return history.scrap_qty_at_stage if history else 0

    def get_stage_remaining_quantity(self, stage_index=None):
        return max(0, self.get_stage_input_quantity(stage_index) - self.get_stage_processed_quantity(stage_index))

    def get_stage_completion_rate(self, stage_index=None):
        stage_input = self.get_stage_input_quantity(stage_index)
        if stage_input <= 0:
            return 0
        return min(100, round((self.get_stage_processed_quantity(stage_index) / stage_input) * 100, 1))

    def get_final_good_quantity(self):
        """Son tamamlanan aşamadan çıkan sağlam ürün miktarı."""
        if not self.workflow_team_ids:
            return max(0, min(self.qty_produced, self.quantity))

        if self.stage_done:
            summary_index = len(self.workflow_team_ids) - 1
        else:
            summary_index = self.active_product_index
            if summary_index > 0 and not self.get_stage_history(summary_index):
                summary_index -= 1

        return max(
            0,
            min(
                self.get_stage_processed_quantity(summary_index) - self.get_stage_scrap_quantity(summary_index),
                self.quantity,
            ),
        )

    def get_total_processed_quantity(self):
        """Tüm aşamalardaki işlem kayıtlarını toplar; kapasite/verim değil faaliyet hacmidir."""
        return sum(history.qty_produced_at_stage for history in self.histories.all())

    def get_total_scrap_quantity(self):
        return sum(history.scrap_qty_at_stage for history in self.histories.all())

    def sync_totals_from_histories(self):
        """Kalem üzerindeki özet miktarları aşama kayıtlarından yeniden hesaplar."""
        histories = list(self.histories.all())
        if not histories:
            self.qty_produced = min(self.qty_produced, self.quantity)
            self.fire_qty = min(self.fire_qty, self.quantity)
            return

        total_scrap = sum(h.scrap_qty_at_stage for h in histories)
        self.qty_produced = self.get_final_good_quantity()
        self.fire_qty = min(total_scrap, self.quantity)


class ProductLineHistory(models.Model):
    """
    Her üretim kaleminin hangi ekipte ne zaman başladığını,
    ne kadar miktar ürettiğini ve ne zaman bitirdiğini (Handover) tutan log tablosu.
    Süre analizi ve darboğaz (bottleneck) tespiti için kullanılır.
    """
    product_line = models.ForeignKey(
        ProductLine,
        on_delete=models.CASCADE,
        related_name='histories',
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='production_histories',
    )
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='production_histories',
    )
    qty_produced_at_stage = models.PositiveIntegerField(default=0)
    scrap_qty_at_stage = models.PositiveIntegerField(default=0)
    
    # Günlük Çalışma Faaliyet Raporu (CNC vb.) İçin Ekstra Alanlar
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Çalışılan Saat')
    work_description = models.TextField(blank=True, default='', verbose_name='Yapılan İş Detayı')
    scrap_location = models.CharField(max_length=200, blank=True, default='', verbose_name='Fire Nerede Oluştu?')
    activity_notes = models.TextField(blank=True, default='', verbose_name='Ek Açıklamalar')

    # PVC Dilimleme Ekibi İçin Alanlar
    pvc_color = models.CharField(max_length=100, blank=True, default='', verbose_name='Renk')
    pvc_roll_size = models.CharField(max_length=100, blank=True, default='', verbose_name='Rulo Boy')
    pvc_meters = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Metre')
    pvc_cut_size = models.CharField(max_length=200, blank=True, default='', verbose_name='Kesim Ölçüsü')

    # Giben Ekibi İçin Alanlar
    giben_plate_size = models.CharField(max_length=200, blank=True, default='', verbose_name='Kullanılan Tabaka Ölçüsü')
    
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Üretim Geçmişi'
        verbose_name_plural = 'Üretim Geçmişleri'
        ordering = ['started_at']
        
    def __str__(self):
        return f"{self.product_line.model_code} - {self.team.name} ({self.started_at.date()})"


class ProductLineProductionLog(models.Model):
    """Her gün sonu üretim girişi için değişmeyen faaliyet kaydı."""
    product_line = models.ForeignKey(
        ProductLine,
        on_delete=models.CASCADE,
        related_name='production_logs',
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='production_logs',
    )
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='production_logs',
    )
    report_date = models.DateField(default=timezone.localdate)
    qty_produced = models.PositiveIntegerField(default=0)
    scrap_qty = models.PositiveIntegerField(default=0)
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    work_description = models.TextField(blank=True, default='')
    fire_reason = models.TextField(blank=True, default='')
    scrap_location = models.CharField(max_length=200, blank=True, default='')
    activity_notes = models.TextField(blank=True, default='')
    pvc_color = models.CharField(max_length=100, blank=True, default='')
    pvc_roll_size = models.CharField(max_length=100, blank=True, default='')
    pvc_meters = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pvc_cut_size = models.CharField(max_length=200, blank=True, default='')
    giben_plate_size = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Günlük Üretim Kaydı'
        verbose_name_plural = 'Günlük Üretim Kayıtları'
        ordering = ['-report_date', '-created_at']

    def __str__(self):
        return f"{self.product_line.model_code} - {self.team.name} ({self.report_date})"


import datetime

class SystemSettings(models.Model):
    """
    Sistem genelindeki ayarları (Mesai saatleri vb.) tutan singleton (tekil) tablo.
    """
    work_start_time = models.TimeField(default=datetime.time(8, 30), verbose_name='Mesai Başlangıç Saati')
    work_end_time = models.TimeField(default=datetime.time(18, 30), verbose_name='Mesai Bitiş Saati')

    # Öğle molası çalışma süresinden sayılmaz.
    lunch_break_start_time = models.TimeField(default=datetime.time(12, 30), verbose_name='Öğle Molası Başlangıç')
    lunch_break_end_time = models.TimeField(default=datetime.time(13, 30), verbose_name='Öğle Molası Bitiş')
    
    # Ekstra mesai (isteğe bağlı)
    overtime_start_time = models.TimeField(null=True, blank=True, verbose_name='Fazla Mesai Başlangıç')
    overtime_end_time = models.TimeField(null=True, blank=True, verbose_name='Fazla Mesai Bitiş')
    
    # Hafta sonu çalışma günleri (0=Pazartesi, 6=Pazar)
    # Örn: "0,1,2,3,4,5" (Pzt-Cmt çalışıyor, Pazar tatil)
    work_days = models.CharField(max_length=50, default='0,1,2,3,4,5', verbose_name='Çalışma Günleri')

    class Meta:
        verbose_name = 'Sistem Ayarı'
        verbose_name_plural = 'Sistem Ayarları'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
