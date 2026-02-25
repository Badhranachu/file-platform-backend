from django.db import migrations, models
import uuid


def fill_missing_folder_codes(apps, schema_editor):
    Folder = apps.get_model("storage", "Folder")
    existing = set(Folder.objects.exclude(folder_code__isnull=True).values_list("folder_code", flat=True))

    for folder in Folder.objects.filter(folder_code__isnull=True):
        code = None
        while code is None or code in existing:
            code = uuid.uuid4().hex[:8].upper()
        folder.folder_code = code
        folder.save(update_fields=["folder_code"])
        existing.add(code)


class Migration(migrations.Migration):
    dependencies = [
        ("storage", "0006_comments_messages"),
    ]

    operations = [
        migrations.RunPython(fill_missing_folder_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="folder",
            name="folder_code",
            field=models.CharField(max_length=12, unique=True),
        ),
    ]
