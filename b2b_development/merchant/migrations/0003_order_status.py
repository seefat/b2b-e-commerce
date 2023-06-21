# Generated by Django 4.2.1 on 2023-06-18 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('merchant', '0002_remove_orderitem_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('ON PROCESSING', 'On Processing'), ('COMPLETED', 'Completed')], default=1, max_length=20),
            preserve_default=False,
        ),
    ]
