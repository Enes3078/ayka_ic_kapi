from django.core.management.base import BaseCommand
from tasks.models import Team

FIXED_TEAMS = [
    'CNC',
    'Giben',
    'Kanat-1',
    'Kanat-2',
    'Kasa-Pervaz',
    'Kenar Bantlama',
    'Kenar Ebatlama',
    'Laminasyon',
    'Paketleme',
    'PVC Dilimleme',
    'Sevkiyat',
    'Vakum'
]

class Command(BaseCommand):
    help = 'Sistemdeki sabit 12 üretim ekibini (departmanını) oluşturur.'

    def handle(self, *args, **kwargs):
        created_count = 0
        for team_name in FIXED_TEAMS:
            team, created = Team.objects.get_or_create(
                name=team_name,
                defaults={'department': 'Üretim'}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Oluşturuldu: {team_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Zaten mevcut: {team_name}'))
                
        self.stdout.write(self.style.SUCCESS(f'İşlem tamamlandı. Toplam {created_count} yeni ekip eklendi.'))
