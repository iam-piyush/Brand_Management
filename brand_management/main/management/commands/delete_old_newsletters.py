from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import Newsletter
from django.conf import settings
import os
import shutil

class Command(BaseCommand):
    help = 'Delete old newsletter PDF folders scheduled for deletion'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        expired_newsletters = Newsletter.objects.filter(schedule_delete__lte=now, pdf_generated=True)

        for newsletter in expired_newsletters:
            pdf_dir = os.path.join(settings.MEDIA_ROOT, 'newsletters', newsletter.newsletter_id)
            if os.path.exists(pdf_dir):
                shutil.rmtree(pdf_dir)
                self.stdout.write(f'Deleted: {pdf_dir}')
            
            newsletter.pdf_generated = False
            newsletter.pdf_sent = False
            newsletter.schedule_delete = None
            newsletter.save()
