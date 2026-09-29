from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('app_product', '0001_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='productoption',
            constraint=models.UniqueConstraint(
                fields=('product', 'color', 'size', 'material'),
                name='unique_product_option',
            ),
        ),
    ]
