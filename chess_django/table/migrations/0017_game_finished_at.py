# Generated by Django 5.0.2 on 2025-02-18 21:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('table', '0016_game_black_draw_game_white_draw'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='finished_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
