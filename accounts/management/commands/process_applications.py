from django.core.management.base import BaseCommand

from accounts.models import Job
from accounts.services import process_job_applications

class Command(BaseCommand):
    help="process pending job applications automatically"

    def handle(self,*args,**options):
        jobs=Job.objects.filter(status=Job.Status.ACTIVE)
        for job in jobs:
            results=process_job_applications(job)
            self.stdout.write(f"{job.title}:{len(results)} application processed")
        self.stdout.write(self.style.SUCCESS("applicaation process completed"))