from django.db.models import Sum, F, ExpressionWrapper, fields
from django.utils import timezone
from tasks.models import ProductLine, ProductLineHistory


class ReportingService:
    """
    Üretim Verimliliği, Fire Oranı ve Süre Analizi (Darboğaz) formüllerini hesaplar.
    """

    @staticmethod
    def calculate_efficiency(product_lines):
        """
        Efficiency = (Actual Qty / Target Qty) * 100
        Sadece quantity > 0 olan kalemleri dikkate alır.
        """
        total_qty = 0
        total_produced = 0
        for pl in product_lines:
            total_qty += pl.quantity
            total_produced += pl.get_final_good_quantity()

        if total_qty == 0:
            return 0.0
        return round((total_produced / total_qty) * 100, 2)

    @staticmethod
    def calculate_scrap_rate(product_lines):
        """
        ScrapRate = (Scrap Qty / (Actual Qty + Scrap Qty)) * 100
        """
        total_produced = 0
        total_scrap = 0
        for pl in product_lines:
            total_produced += pl.get_final_good_quantity()
            total_scrap += pl.get_total_scrap_quantity()

        denominator = total_produced + total_scrap
        if denominator == 0:
            return 0.0
        return round((total_scrap / denominator) * 100, 2)

    @staticmethod
    def get_bottleneck_analysis(start_date=None, end_date=None):
        """
        Her istasyon (Team) için ortalama (completed_at - started_at) hesaplar.
        Darboğazları (en çok vakit harcanan ekipleri) tespit eder.
        """
        qs = ProductLineHistory.objects.filter(completed_at__isnull=False)
        if start_date:
            qs = qs.filter(started_at__gte=start_date)
        if end_date:
            qs = qs.filter(completed_at__lte=end_date)

        # SQL seviyesinde diff hesapla (PostgreSQL/SQLite destekli)
        duration_expr = ExpressionWrapper(
            F('completed_at') - F('started_at'),
            output_field=fields.DurationField()
        )
        
        histories = qs.annotate(duration=duration_expr).values(
            'team__name', 'duration'
        )

        team_stats = {}
        for h in histories:
            t_name = h['team__name']
            if t_name not in team_stats:
                team_stats[t_name] = {'total_seconds': 0, 'count': 0}
            
            # duration objesi datetime.timedelta'dır
            if h['duration']:
                team_stats[t_name]['total_seconds'] += h['duration'].total_seconds()
                team_stats[t_name]['count'] += 1

        results = []
        for team, stats in team_stats.items():
            avg_sec = stats['total_seconds'] / stats['count'] if stats['count'] > 0 else 0
            results.append({
                'team': team,
                'avg_minutes': round(avg_sec / 60, 2),
                'job_count': stats['count']
            })

        # En yavaştan en hızlıya sırala (Darboğaz üstte)
        results.sort(key=lambda x: x['avg_minutes'], reverse=True)
        return results

    @staticmethod
    def get_dashboard_summary():
        """Tüm üretim sisteminin genel özetini döner."""
        active_lines = ProductLine.objects.filter(stage_done=False)
        completed_lines = ProductLine.objects.filter(stage_done=True)

        return {
            'efficiency': ReportingService.calculate_efficiency(completed_lines),
            'scrap_rate': ReportingService.calculate_scrap_rate(completed_lines),
            'bottlenecks': ReportingService.get_bottleneck_analysis()[:5], # Top 5 darboğaz
            'active_jobs': active_lines.count(),
            'completed_jobs': completed_lines.count(),
        }
