from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("storage", "0004_folder_folder_code"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="folder",
            name="liked_by",
            field=models.ManyToManyField(blank=True, related_name="liked_folders", to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name="FolderView",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("viewed_at", models.DateTimeField(auto_now_add=True)),
                ("folder", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="views", to="storage.folder")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="folder_views", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "unique_together": {("folder", "user")},
            },
        ),
    ]
