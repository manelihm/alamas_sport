from django.core.management.base import BaseCommand
from faker import Faker

from app_auth.models import User
from app_product.models import (
    Category, Product, ProductColor, ProductSize,
    ProductMaterial, ProductOption
)

fake = Faker()


class Command(BaseCommand):
    help = 'Creates fake sample data for users and products'

    def handle(self, *args, **options):
        self.create_users()
        colors = self.create_colors()
        sizes = self.create_sizes()
        materials = self.create_materials()
        categories = self.create_categories()
        self.create_products(categories, colors, sizes, materials)

        self.stdout.write(self.style.SUCCESS('All fake data created successfully!'))

    def create_users(self):
        self.stdout.write('Creating users...')

        # One super admin (only if none exists yet)
        if not User.objects.filter(role='super_admin').exists():
            User.objects.create_superuser(
                phone_number='09100000001',
                password='SuperAdmin123',
                username='superadmin',
                first_name='Super',
                last_name='Admin',
            )

        # A few regular admins
        for i in range(2):
            phone = f'0910000001{i}'
            if not User.objects.filter(phone_number=phone).exists():
                user = User.objects.create_user(
                    phone_number=phone,
                    password='Admin12345',
                    username=f'admin{i}',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    role='admin',
                    is_staff=True,
                    is_phone_verified=True,
                )

        # Regular users
        used_phones = set(User.objects.values_list('phone_number', flat=True))
        created = 0
        attempts = 0
        while created < 20 and attempts < 100:
            attempts += 1
            phone = '09' + fake.numerify('#########')
            if phone in used_phones:
                continue
            used_phones.add(phone)
            User.objects.create_user(
                phone_number=phone,
                password='User12345',
                username=fake.unique.user_name(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                gender=fake.random_element(['male', 'female']),
                role='user',
                is_phone_verified=True,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'  -> {User.objects.count()} total users now in database.'))

    def create_colors(self):
        self.stdout.write('Creating colors...')
        colors = []
        for _ in range(6):
            color = ProductColor.objects.create(
                name=fake.color_name(),
                color_code=fake.hex_color()
            )
            colors.append(color)
        return colors

    def create_sizes(self):
        self.stdout.write('Creating sizes...')
        sizes = []
        for size_name in ['S', 'M', 'L', 'XL', 'XXL']:
            size, _ = ProductSize.objects.get_or_create(name=size_name)
            sizes.append(size)
        return sizes

    def create_materials(self):
        self.stdout.write('Creating materials...')
        materials = []
        for _ in range(4):
            material = ProductMaterial.objects.create(
                name=fake.word().capitalize(),
                description=fake.sentence(),
              
            )
            materials.append(material)
        return materials

    def create_categories(self):
        self.stdout.write('Creating categories...')
        all_categories = []

        root_categories = []
        for _ in range(4):
            category = Category.objects.create(
                parent=None,
                name=fake.word().capitalize(),
                description=fake.sentence(),
                is_active=True
            )
            root_categories.append(category)
            all_categories.append(category)

        for parent in root_categories:
            for _ in range(3):
                sub = Category.objects.create(
                    parent=parent,
                    name=fake.word().capitalize(),
                    description=fake.sentence(),
                    is_active=True
                )
                all_categories.append(sub)

        return all_categories

    def create_products(self, categories, colors, sizes, materials):
        self.stdout.write('Creating products and options...')
        for _ in range(15):
            product = Product.objects.create(
                category=fake.random_element(categories),
                name=fake.word().capitalize() + ' ' + fake.word().capitalize(),
                description=fake.paragraph(),
                brand=fake.company(),
                gender=fake.random_element(['men', 'women', 'unisex']),
                is_active=True
            )

            for _ in range(fake.random_int(2, 4)):
                ProductOption.objects.get_or_create(
                    product=product,
                    color=fake.random_element(colors),
                    size=fake.random_element(sizes),
                    material=fake.random_element(materials),
                    defaults={
                        'retail_price': fake.random_int(100000, 3000000),
                        'wholesale_price': fake.random_int(80000, 2500000),
                        'wholesale_min_quantity': fake.random_int(5, 20),
                        'stock': fake.random_int(0, 100),
                        'is_active': True,
                    }
                )
