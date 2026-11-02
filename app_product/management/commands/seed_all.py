from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app_auth.models import User
from app_product.models import (
    Category,
    Product,
    ProductColor,
    ProductSize,
    ProductMaterial,
    ProductOption,
    Discount,
    DiscountCode,
)
from app_users.models import (
    Address,
    Favorite,
    ProductFeedback,
    ProductRequest,
)
from app_home.models import (
    HomeContent,
    TrendingProduct,
    CompanyInformation,
    CompanyInformationContent,
)


class Command(BaseCommand):
    help = "Create complete sample data for Alamas Sport"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting seed process..."))

        self.users = self.create_users()
        self.categories = self.create_categories()
        self.colors = self.create_colors()
        self.sizes = self.create_sizes()
        self.materials = self.create_materials()

        self.products = self.create_products()
        self.options = self.create_product_options()

        self.discounts = self.create_discounts()
        self.create_discount_codes()

        self.create_user_data()
        self.create_home_content()
        self.create_trending_products()
        self.create_company_information()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            "Seed data created successfully!"
        ))
        self.stdout.write(f"Users: {User.objects.count()}")
        self.stdout.write(f"Categories: {Category.objects.count()}")
        self.stdout.write(f"Products: {Product.objects.count()}")
        self.stdout.write(f"Product options: {ProductOption.objects.count()}")
        self.stdout.write(f"Discounts: {Discount.objects.count()}")
        self.stdout.write(f"Discount codes: {DiscountCode.objects.count()}")
        self.stdout.write(f"Home content: {HomeContent.objects.count()}")
        self.stdout.write(
            f"Trending products: {TrendingProduct.objects.count()}"
        )

    # -------------------------------------------------
    # USERS
    # -------------------------------------------------

    def create_users(self):
        self.stdout.write("Creating users...")

        users = []

        user_data = [
            {
                "phone_number": "09111111111",
                "username": "seed_admin",
                "first_name": "مدیر",
                "last_name": "آزمایشی",
                "role": "admin",
                "is_staff": True,
                "password": "Admin12345",
            },
            {
                "phone_number": "09111111112",
                "username": "seed_user_1",
                "first_name": "علی",
                "last_name": "احمدی",
                "role": "user",
                "is_staff": False,
                "password": "User12345",
            },
            {
                "phone_number": "09111111113",
                "username": "seed_user_2",
                "first_name": "سارا",
                "last_name": "محمدی",
                "role": "user",
                "is_staff": False,
                "password": "User12345",
            },
            {
                "phone_number": "09111111114",
                "username": "seed_user_3",
                "first_name": "رضا",
                "last_name": "کریمی",
                "role": "user",
                "is_staff": False,
                "password": "User12345",
            },
            {
                "phone_number": "09111111115",
                "username": "seed_user_4",
                "first_name": "ندا",
                "last_name": "حسینی",
                "role": "user",
                "is_staff": False,
                "password": "User12345",
            },
        ]

        for data in user_data:
            password = data.pop("password")

            user, created = User.objects.get_or_create(
                phone_number=data["phone_number"],
                defaults={
                    **data,
                    "is_phone_verified": True,
                    "is_active": True,
                    "status": "active",
                },
            )

            if created:
                user.set_password(password)
                user.save()

            users.append(user)

        self.stdout.write(self.style.SUCCESS(
            f"Created/found {len(users)} seed users."
        ))
        return users

    # -------------------------------------------------
    # CATEGORIES
    # -------------------------------------------------

    def create_categories(self):
        self.stdout.write("Creating categories...")

        category_data = {
            "پوشاک ورزشی": [
                "تی شرت ورزشی",
                "شلوار ورزشی",
                "لباس ورزشی زنانه",
            ],
            "کفش ورزشی": [
                "کفش دویدن",
                "کفش تمرین",
                "کفش پیاده روی",
            ],
            "لوازم ورزشی": [
                "دستکش ورزشی",
                "کیف ورزشی",
                "لوازم بدنسازی",
            ],
        }

        categories = []

        for parent_name, children in category_data.items():
            parent, _ = Category.objects.get_or_create(
                name=parent_name,
                parent=None,
                defaults={
                    "description": f"دسته بندی {parent_name}",
                    "is_active": True,
                },
            )

            parent.is_active = True
            parent.save()
            categories.append(parent)

            for child_name in children:
                child, _ = Category.objects.get_or_create(
                    name=child_name,
                    parent=parent,
                    defaults={
                        "description": f"محصولات دسته {child_name}",
                        "is_active": True,
                    },
                )

                child.is_active = True
                child.save()
                categories.append(child)

        return categories

    # -------------------------------------------------
    # PRODUCT ATTRIBUTES
    # -------------------------------------------------

    def create_colors(self):
        self.stdout.write("Creating colors...")

        color_data = [
            ("مشکی", "#000000"),
            ("سفید", "#FFFFFF"),
            ("قرمز", "#FF0000"),
            ("آبی", "#0000FF"),
            ("سبز", "#008000"),
            ("طوسی", "#808080"),
        ]

        colors = []

        for name, code in color_data:
            color, _ = ProductColor.objects.get_or_create(
                name=name,
                defaults={"color_code": code},
            )
            colors.append(color)

        return colors

    def create_sizes(self):
        self.stdout.write("Creating sizes...")

        sizes = []

        for name in ["S", "M", "L", "XL", "XXL"]:
            size, _ = ProductSize.objects.get_or_create(name=name)
            sizes.append(size)

        return sizes

    def create_materials(self):
        self.stdout.write("Creating materials...")

        material_data = [
            ("پلی استر", "پارچه مناسب لباس ورزشی"),
            ("نخ پنبه", "پارچه نرم و راحت"),
            ("اسپندکس", "پارچه کشسان و انعطاف پذیر"),
            ("مش", "پارچه توری و دارای تهویه"),
        ]

        materials = []

        for name, description in material_data:
            material, _ = ProductMaterial.objects.get_or_create(
                name=name,
                defaults={"description": description},
            )
            materials.append(material)

        return materials

    # -------------------------------------------------
    # PRODUCTS
    # -------------------------------------------------

    def create_products(self):
        self.stdout.write("Creating products...")

        product_data = [
            {
                "name": "تی شرت ورزشی مردانه",
                "category": "تی شرت ورزشی",
                "brand": "Alamas",
                "gender": "men",
            },
            {
                "name": "شلوار ورزشی مردانه",
                "category": "شلوار ورزشی",
                "brand": "Alamas",
                "gender": "men",
            },
            {
                "name": "لباس ورزشی زنانه",
                "category": "لباس ورزشی زنانه",
                "brand": "Sport Pro",
                "gender": "women",
            },
            {
                "name": "کفش مخصوص دویدن",
                "category": "کفش دویدن",
                "brand": "RunX",
                "gender": "unisex",
            },
            {
                "name": "کفش تمرین حرفه ای",
                "category": "کفش تمرین",
                "brand": "Sport Pro",
                "gender": "unisex",
            },
            {
                "name": "دستکش بدنسازی",
                "category": "دستکش ورزشی",
                "brand": "GymX",
                "gender": "unisex",
            },
            {
                "name": "کیف ورزشی",
                "category": "کیف ورزشی",
                "brand": "Alamas",
                "gender": "unisex",
            },
            {
                "name": "لباس تمرین زنانه",
                "category": "لباس ورزشی زنانه",
                "brand": "FitStyle",
                "gender": "women",
            },
            {
                "name": "تی شرت تمرین",
                "category": "تی شرت ورزشی",
                "brand": "FitStyle",
                "gender": "unisex",
            },
            {
                "name": "شلوار ورزشی زنانه",
                "category": "شلوار ورزشی",
                "brand": "Sport Pro",
                "gender": "women",
            },
        ]

        products = []

        for data in product_data:
            category = next(
                (
                    item for item in self.categories
                    if item.name == data["category"]
                ),
                None,
            )

            product, _ = Product.objects.get_or_create(
                name=data["name"],
                defaults={
                    "category": category,
                    "description": (
                        f"{data['name']} با کیفیت مناسب "
                        "برای تمرین و فعالیت ورزشی."
                    ),
                    "brand": data["brand"],
                    "gender": data["gender"],
                    "is_active": True,
                },
            )

            product.category = category
            product.is_active = True
            product.save()

            products.append(product)

        return products

    # -------------------------------------------------
    # PRODUCT OPTIONS
    # -------------------------------------------------

    def create_product_options(self):
        self.stdout.write("Creating product options...")

        options = []

        for index, product in enumerate(self.products):
            color = self.colors[index % len(self.colors)]
            material = self.materials[index % len(self.materials)]

            for size_index in [1, 2]:
                size = self.sizes[size_index]

                option, _ = ProductOption.objects.get_or_create(
                    product=product,
                    color=color,
                    size=size,
                    material=material,
                    defaults={
                        "retail_price": 850000 + (index * 50000),
                        "wholesale_price": 700000 + (index * 40000),
                        "wholesale_min_quantity": 5,
                        "stock": 20 + index,
                        "is_active": True,
                    },
                )

                options.append(option)

        return options

    # -------------------------------------------------
    # DISCOUNTS
    # -------------------------------------------------

    def create_discounts(self):
        self.stdout.write("Creating discounts...")

        discounts = []
        now = timezone.now()

        for index, option in enumerate(self.options):
            discount, created = Discount.objects.get_or_create(
                product=option,
                defaults={
                    "type": "percentage",
                    "value": 10 + (index % 3) * 5,
                    "start_at": now - timedelta(days=1),
                    "end_at": now + timedelta(days=30),
                },
            )

            if not created:
                discount.type = "percentage"
                discount.value = 10 + (index % 3) * 5
                discount.start_at = now - timedelta(days=1)
                discount.end_at = now + timedelta(days=30)
                discount.save()

            discounts.append(discount)

        return discounts

    # -------------------------------------------------
    # DISCOUNT CODES
    # -------------------------------------------------

    def create_discount_codes(self):
        self.stdout.write("Creating discount codes...")

        now = timezone.now()

        codes = [
            ("ALAMAS10", "percentage", 10),
            ("ALAMAS15", "percentage", 15),
            ("WELCOME100", "fixed", 100000),
        ]

        for index, (code, discount_type, value) in enumerate(codes):
            assigned_user = self.users[(index + 1) % len(self.users)]

            DiscountCode.objects.update_or_create(
                code=code,
                defaults={
                    "assigned_to": assigned_user,
                    "type": discount_type,
                    "value": value,
                    "is_used": False,
                    "used_by": None,
                    "used_at": None,
                    "start_at": now - timedelta(days=1),
                    "end_at": now + timedelta(days=30),
                },
            )

    # -------------------------------------------------
    # USER DATA
    # -------------------------------------------------

    def create_user_data(self):
        self.stdout.write("Creating user data...")

        for index, user in enumerate(self.users[1:]):
            # Address
            has_default_address = Address.objects.filter(
                user=user,
                is_default=True,
            ).exists()

            Address.objects.get_or_create(
                user=user,
                city="تهران",
                address=f"خیابان نمونه، پلاک {index + 10}",
                postal_code=f"123456789{index}",
                defaults={
                    "province": "تهران",
                    "is_default": not has_default_address,
                },
            )

            # Favorite
            product = self.products[index % len(self.products)]

            Favorite.objects.get_or_create(
                user=user,
                product=product,
            )

            # Product feedback
            feedback_product = self.products[
                (index + 1) % len(self.products)
            ]

            ProductFeedback.objects.get_or_create(
                user=user,
                product=feedback_product,
                defaults={
                    "content": "کیفیت محصول خوب بود و از خریدم راضی هستم.",
                    "rating": 5,
                    "status": (
                        "APPROVED" if index % 2 == 0 else "PENDING"
                    ),
                },
            )

            # Product request
            ProductRequest.objects.get_or_create(
                user=user,
                title=f"درخواست محصول آزمایشی {index + 1}",
                defaults={
                    "description": (
                        "لطفاً این محصول را به فروشگاه اضافه کنید."
                    ),
                    "status": "PENDING",
                    "admin_note": "",
                },
            )

    # -------------------------------------------------
    # HOME CONTENT
    # -------------------------------------------------

    def create_home_content(self):
        self.stdout.write("Creating home content...")

        # Trending section
        HomeContent.objects.get_or_create(
            type="trending",
            title="محصولات پرفروش و محبوب",
            defaults={
                "sort_order": 1,
                "is_active": True,
            },
        )

        # Category sections
        category_names = [
            "پوشاک ورزشی",
            "کفش ورزشی",
            "لوازم ورزشی",
        ]

        for index, name in enumerate(category_names):
            category = next(
                (
                    item for item in self.categories
                    if item.name == name and item.parent is None
                ),
                None,
            )

            HomeContent.objects.get_or_create(
                type="category",
                title=f"دسته بندی {name}",
                defaults={
                    "sort_order": index + 2,
                    "is_active": True,
                    "category": category,
                },
            )

        # Discount sections
        for index, discount in enumerate(self.discounts[:3]):
            HomeContent.objects.get_or_create(
                type="discount",
                title=f"پیشنهاد ویژه {index + 1}",
                defaults={
                    "sort_order": index + 5,
                    "is_active": True,
                    "discount": discount,
                },
            )

        # Company information section
        HomeContent.objects.get_or_create(
            type="company_info",
            title="درباره فروشگاه",
            defaults={
                "sort_order": 10,
                "is_active": True,
            },
        )

        # No banner section is created because Banner requires an image.

    # -------------------------------------------------
    # TRENDING PRODUCTS
    # -------------------------------------------------

    def create_trending_products(self):
        self.stdout.write("Creating trending products...")

        trending_section = HomeContent.objects.filter(
            type="trending",
            title="محصولات پرفروش و محبوب",
        ).first()

        for index, product in enumerate(self.products[:8]):
            TrendingProduct.objects.get_or_create(
                product=product,
                home_content=trending_section,
                defaults={
                    "sort_order": index + 1,
                    "is_active": True,
                },
            )

    # -------------------------------------------------
    # COMPANY INFORMATION
    # -------------------------------------------------

    def create_company_information(self):
        self.stdout.write("Creating company information...")

        home_section = HomeContent.objects.filter(
            type="company_info",
            title="درباره فروشگاه",
        ).first()

        company, _ = CompanyInformation.objects.get_or_create(
            title="فروشگاه ورزشی آلاماس",
            defaults={
                "description": (
                    "آلاماس فروشگاه تخصصی پوشاک و تجهیزات ورزشی "
                    "با هدف ارائه محصولات باکیفیت است."
                ),
                "is_active": True,
                "home_content": home_section,
            },
        )

        company.description = (
            "آلاماس فروشگاه تخصصی پوشاک و تجهیزات ورزشی "
            "با هدف ارائه محصولات باکیفیت است."
        )
        company.is_active = True
        company.home_content = home_section
        company.save()

        contents = [
            (
                "درباره ما",
                "آلاماس ارائه دهنده محصولات متنوع ورزشی است.",
            ),
            (
                "هدف ما",
                "ارائه محصولات باکیفیت و تجربه خرید مناسب.",
            ),
            (
                "خدمات مشتریان",
                "پشتیبانی و پاسخگویی به مشتریان در تمام مراحل خرید.",
            ),
        ]

        for index, (title, value) in enumerate(contents):
            CompanyInformationContent.objects.get_or_create(
                company_information=company,
                title=title,
                defaults={
                    "value": value,
                    "sort_order": index + 1,
                },
            )
