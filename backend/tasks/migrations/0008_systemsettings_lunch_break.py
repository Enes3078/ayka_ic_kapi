import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0007_systemsettings_alter_productlinehistory_started_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsettings',
            name='lunch_break_start_time',
            field=models.TimeField(default=datetime.time(12, 30), verbose_name='Öğle Molası Başlangıç'),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='lunch_break_end_time',
            field=models.TimeField(default=datetime.time(13, 30), verbose_name='Öğle Molası Bitiş'),
        ),
    ]
