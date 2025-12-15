# Generated migration for adding vehicle_value field

from django.db import migrations, models
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0002_add_seats_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicle',
            name='vehicle_value',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('100000.00'),
                help_text='车辆估值（用于押金计算）',
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal('10000.00'))],
                verbose_name='车辆价值'
            ),
        ),
    ]
