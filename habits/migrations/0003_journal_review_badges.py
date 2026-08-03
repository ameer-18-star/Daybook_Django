import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('habits', '0002_alter_usersettings_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='JournalEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('mood', models.CharField(blank=True, choices=[
                    ('great', 'Great'), ('good', 'Good'), ('neutral', 'Neutral'),
                    ('low', 'Low'), ('rough', 'Rough'),
                ], default='', max_length=10)),
                ('text', models.TextField(blank=True, default='', max_length=8000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name='journal_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-date']},
        ),
        migrations.AlterUniqueTogether(
            name='journalentry',
            unique_together={('owner', 'date')},
        ),
        migrations.CreateModel(
            name='WeeklyReview',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('week_start', models.DateField()),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name='weekly_reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-week_start']},
        ),
        migrations.AlterUniqueTogether(
            name='weeklyreview',
            unique_together={('owner', 'week_start')},
        ),
        migrations.CreateModel(
            name='HabitReviewRating',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('effort_rating', models.PositiveSmallIntegerField()),
                ('note', models.TextField(blank=True, default='', max_length=1000)),
                ('habit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name='review_ratings', to='habits.habit')),
                ('review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name='ratings', to='habits.weeklyreview')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='habitreviewrating',
            unique_together={('review', 'habit')},
        ),
        migrations.CreateModel(
            name='UserBadge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=40)),
                ('unlocked_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                            related_name='badges', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-unlocked_at']},
        ),
        migrations.AlterUniqueTogether(
            name='userbadge',
            unique_together={('owner', 'key')},
        ),
    ]