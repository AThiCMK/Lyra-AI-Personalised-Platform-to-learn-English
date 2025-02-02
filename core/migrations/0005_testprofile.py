# Generated by Django 5.1.3 on 2025-01-01 15:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_remove_sentence_test_type_sentence_level'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('audio_files', models.JSONField(default=dict)),
                ('results', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sentences', models.ManyToManyField(to='core.sentence')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.studentprofile')),
                ('test_progress', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.testprogress')),
            ],
        ),
    ]
