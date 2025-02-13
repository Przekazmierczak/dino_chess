from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_django.settings')

app = Celery('chess_django')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.update(
    broker_connection_retry_on_startup=True,
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')