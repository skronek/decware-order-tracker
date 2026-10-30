from django.db import migrations, models


def fill_range_start(apps, schema_editor):
    # Stored estimates get a real early date at the next recompute; until then the range
    # starts at the best guess, as it did before
    OrderEstimate = apps.get_model('orders', 'OrderEstimate')
    OrderEstimate.objects.update(range_start_date=models.F('estimated_date'))


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_delete_statusmetrics'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderestimate',
            name='range_start_date',
            field=models.DateField(null=True),
        ),
        migrations.RunPython(fill_range_start, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='orderestimate',
            name='range_start_date',
            field=models.DateField(help_text='Earlier end of the likely range'),
        ),
        migrations.AlterField(
            model_name='orderestimate',
            name='estimated_date',
            field=models.DateField(help_text='Most likely date the order passes QC (the best guess)'),
        ),
    ]
