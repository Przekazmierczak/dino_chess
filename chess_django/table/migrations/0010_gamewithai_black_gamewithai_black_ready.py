# Generated by Django 4.2.10 on 2024-08-07 19:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('table', '0009_gamewithai'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamewithai',
            name='black',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='black_ai_games', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='gamewithai',
            name='black_ready',
            field=models.BooleanField(default=False),
        ),
    ]
