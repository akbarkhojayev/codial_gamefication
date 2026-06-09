# Generated migration for QueryLog model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='QueryLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField()),
                ('query_type', models.CharField(
                    choices=[
                        ('students', 'Talabalar'),
                        ('mentors', 'Mentorlar'),
                        ('courses', 'Kurslar'),
                        ('groups', 'Guruhlar'),
                        ('books', 'Kitoblar'),
                        ('points', 'Balllar'),
                        ('search', 'Qidiruv'),
                        ('all', 'Barcha'),
                    ],
                    max_length=50
                )),
                ('result_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='query_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
