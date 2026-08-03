from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from tasks.models import Task


class Command(BaseCommand):
    help = (
        "One-time upgrade helper: assigns any tasks created before multi-user "
        "support (owner is NULL) to the given username, so they don't vanish "
        "from view after upgrading. Safe to run more than once."
    )

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to assign orphaned tasks to')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(
                f"No user named '{username}'. Create one first with "
                f"'python manage.py createsuperuser' or 'python manage.py "
                f"createsuperuser --username {username}'."
            )

        orphaned = Task.objects.filter(owner__isnull=True)
        count = orphaned.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No orphaned tasks found — nothing to do.'))
            return

        orphaned.update(owner=user)
        self.stdout.write(self.style.SUCCESS(
            f'Assigned {count} pre-existing task(s) to "{username}".'
        ))
