# Generated migration for adding credit_score field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0003_customer_idx_customer_name_customer_idx_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='credit_score',
            field=models.PositiveIntegerField(
                default=100,
                help_text='客户信用评分（0-100，初始100，用于押金计算）',
                verbose_name='信用评分'
            ),
        ),
    ]
