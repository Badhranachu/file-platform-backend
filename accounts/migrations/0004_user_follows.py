from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_adminprofile_userprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="follows",
            field=models.ManyToManyField(blank=True, related_name="followers", to=settings.AUTH_USER_MODEL),
        ),
    ]
