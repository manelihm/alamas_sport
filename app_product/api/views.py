from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated
from app_product.models import DiscountCode
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes,
)
from django.db.models import Q


from decimal import Decimal, InvalidOperation
from django.db import IntegrityError ,transaction


from app_product.models import (
    Category, Product, ProductImage,
    ProductColor, ProductSize, ProductMaterial,
    ProductOption, Discount
)
from app_product.api.serializers import (
    CategorySerializer, ProductSerializer, ProductDetailSerializer,
    ProductColorSerializer, ProductSizeSerializer,
    ProductMaterialSerializer, ProductOptionCreateSerializer, DiscountSerializer ,DiscountCodeSerializer, DiscountCodeApplySerializer ,ProductImageReadSerializer,
    ProductImageUploadSerializer,CategoryTreeSerializer
)


# ---------- Category ----------

@swagger_auto_schema(
    method='get',
    operation_summary="List categories with nested subcategories",
    operation_description=(
        "Returns root categories with all nested subcategories. "
        "Omit parent or use ?parent=null to get the complete tree "
        "starting from root categories. "
        "Pass ?parent=<id> to get that category's direct children "
        "with all their nested descendants."
    ),
    manual_parameters=[
        openapi.Parameter(
            'parent',
            openapi.IN_QUERY,
            description=(
                "Optional parent category ID. "
                "Omit it or use 'null' for root categories and their trees."
            ),
            type=openapi.TYPE_STRING,
            required=False,
        ),
    ],
    responses={200: CategoryTreeSerializer(many=True)}
)
@api_view(['GET'])
def category_list(request):
    parent_id = request.query_params.get('parent')

    if parent_id is None or parent_id == 'null':
        categories = Category.objects.filter(
            parent__isnull=True,
            is_active=True
        ).order_by('id')

    else:
        if not parent_id.isdigit():
            return Response(
                {'error': 'parent must be a valid category ID.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        parent_category = get_object_or_404(
            Category,
            pk=int(parent_id),
            is_active=True
        )

        categories = Category.objects.filter(
            parent=parent_category,
            is_active=True
        ).order_by('id')

    serializer = CategoryTreeSerializer(
        categories,
        many=True
    )

    return Response({
        "data": serializer.data,
        "message": "Category tree retrieved successfully"
    })
@swagger_auto_schema(
    method='get',
    operation_summary="Get category detail",
    operation_description="Returns the details of a single category by its id.",
    responses={200: CategorySerializer, 404: "Category not found"}
)
@api_view(['GET'])
def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk, is_active=True)
    serializer = CategorySerializer(category)
    return Response({"data": serializer.data, "message": "Category retrieved successfully"})


@swagger_auto_schema(
    method='post',
    operation_summary="Create a new category",
    operation_description="Creates a new category. Pass a 'parent' id to create it as a subcategory. Only accessible by admin users.",
    request_body=CategorySerializer,
    responses={201: CategorySerializer, 400: "Invalid data"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def category_create(request):
    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Category created successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='put',
    operation_summary="Update a category",
    operation_description="Updates all fields of an existing category. Only accessible by admin users.",
    request_body=CategorySerializer,
    responses={200: CategorySerializer, 400: "Invalid data", 404: "Category not found"}
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    serializer = CategorySerializer(category, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Category updated successfully"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a category",
    operation_description="Deletes a category. Only accessible by admin users. If any subcategory or product still references this category, deletion will be blocked.",
    responses={204: "Category deleted successfully", 404: "Category not found"}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Product ----------
@swagger_auto_schema(
    method='get',
    operation_summary="List products with pagination",
    operation_description=(
        "Returns active products with optional category, "
        "brand, and gender filters. 10 products per page."
    ),
    manual_parameters=[
        openapi.Parameter(
            'category', openapi.IN_QUERY,
            description="Filter by category ID",
            type=openapi.TYPE_INTEGER,
        ),
        openapi.Parameter(
            'brand', openapi.IN_QUERY,
            description="Filter by brand",
            type=openapi.TYPE_STRING,
        ),
        openapi.Parameter(
            'gender', openapi.IN_QUERY,
            description="Filter by gender",
            type=openapi.TYPE_STRING,
        ),
        openapi.Parameter(
            'page', openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
        ),
    ],
    responses={200: ProductSerializer(many=True)}
)
@api_view(['GET'])
def product_list(request):
    products = Product.objects.filter(
        is_active=True
    ).order_by('id')

    category = request.query_params.get('category')
    if category:
        products = products.filter(category_id=category)

    brand = request.query_params.get('brand')
    if brand:
        products = products.filter(brand__icontains=brand)

    gender = request.query_params.get('gender')
    if gender:
        products = products.filter(gender__iexact=gender)

    paginator = Paginator(products, 10)
    page_number = request.query_params.get('page', 1)
    page_obj = paginator.get_page(page_number)

    serializer = ProductSerializer(
    page_obj.object_list,
    many=True,
    context={'request': request}
)
    return Response({
        "count": paginator.count,
        "total_pages": paginator.num_pages,
        "current_page": page_obj.number,
        "data": serializer.data,
        "message": "Product list retrieved successfully",
    })

@swagger_auto_schema(
    method='post',
    operation_summary="Advanced product search",
    operation_description=(
        "Search products by name, category, brand, gender, "
        "color, size, material, wholesale or retail price range, "
        "and active discount. Results are paginated."
    ),
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING),
            'category': openapi.Schema(type=openapi.TYPE_INTEGER),
            'brand': openapi.Schema(type=openapi.TYPE_STRING),
            'gender': openapi.Schema(type=openapi.TYPE_STRING),
            'color': openapi.Schema(type=openapi.TYPE_INTEGER),
            'size': openapi.Schema(type=openapi.TYPE_INTEGER),
            'material': openapi.Schema(type=openapi.TYPE_INTEGER),
            'price_type': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['wholesale', 'retail'],
                default='wholesale',
            ),
            'min_price': openapi.Schema(type=openapi.TYPE_NUMBER),
            'max_price': openapi.Schema(type=openapi.TYPE_NUMBER),
            'has_discount': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'page': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                default=1,
            ),
        },
    ),
)
@api_view(['POST'])
def product_search(request):
    data = request.data

    products = Product.objects.filter(is_active=True)

   
    # Basic filters
    name = data.get('name')
    if name:
        products = products.filter(
            Q(name__icontains=name) | Q(brand__icontains=name)
        )
    category = data.get('category')
    if category is not None:
        products = products.filter(category_id=category)

    brand = data.get('brand')
    if brand:
        products = products.filter(brand__icontains=brand)

    gender = data.get('gender')
    if gender:
        products = products.filter(gender__iexact=gender)

    # Product option filters
    options = ProductOption.objects.filter(
        is_active=True,
        product__is_active=True,
    )

    color = data.get('color')
    if color is not None:
        options = options.filter(color_id=color)

    size = data.get('size')
    if size is not None:
        options = options.filter(size_id=size)

    material = data.get('material')
    if material is not None:
        options = options.filter(material_id=material)

    # Price range
    min_price = data.get('min_price')
    max_price = data.get('max_price')
    price_type = data.get('price_type', 'wholesale')

    if price_type not in ('wholesale', 'retail'):
        return Response(
            {
                'error': (
                    'price_type must be wholesale or retail.'
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if min_price is not None or max_price is not None:
        try:
            min_value = (
                Decimal(str(min_price))
                if min_price is not None else None
            )
            max_value = (
                Decimal(str(max_price))
                if max_price is not None else None
            )

            if (
                min_value is not None and min_value < 0
            ) or (
                max_value is not None and max_value < 0
            ):
                raise ValueError

            if (
                min_value is not None
                and max_value is not None
                and min_value > max_value
            ):
                return Response(
                    {
                        'error': (
                            'min_price cannot exceed max_price.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except (InvalidOperation, ValueError, TypeError):
            return Response(
                {'error': 'Enter valid non-negative prices.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        price_field = (
            'wholesale_price'
            if price_type == 'wholesale'
            else 'retail_price'
        )

        if min_value is not None:
            options = options.filter(
                **{f'{price_field}__gte': min_value}
            )

        if max_value is not None:
            options = options.filter(
                **{f'{price_field}__lte': max_value}
            )

    # Discount filter
    has_discount = data.get('has_discount')

    if has_discount is not None:
        if not isinstance(has_discount, bool):
            return Response(
                {'error': 'has_discount must be true or false.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()

        discounted_ids = Discount.objects.filter(
            start_at__lte=now,
            end_at__gte=now,
        ).values_list('product_id', flat=True)

        if has_discount:
            options = options.filter(id__in=discounted_ids)
        else:
            options = options.exclude(id__in=discounted_ids)

    # Only restrict products when option filters were requested
    option_filters = (
        'color',
        'size',
        'material',
        'min_price',
        'max_price',
        'has_discount',
    )

    if any(data.get(field) is not None for field in option_filters):
        products = products.filter(
            id__in=options.values('product_id')
        )
# ===== Categories of matched products =====
    search_term = data.get('name') or data.get('brand')
    categories_data = []

    if search_term:
        matched_category_ids = (
            products
            .filter(category__isnull=False)
            .values_list('category_id', flat=True)
            .distinct()
        )

        categories_qs = (
            Category.objects
            .filter(
                id__in=matched_category_ids,
                is_active=True,
            )
            .order_by('name')
        )

        categories_data = CategorySerializer(
            categories_qs,
            many=True,
            context={'request': request},
        ).data
 # ===== End categories =====




    # Pagination
    products = products.order_by('id').distinct()

    paginator = Paginator(products, 10)
    page_number = data.get('page', 1)
    page_obj = paginator.get_page(page_number)

    serializer = ProductSerializer(
        page_obj.object_list,
        many=True,
        context={'request': request}
)
    return Response({
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'data': serializer.data,
        'categories': categories_data,
        "message": "Products retrieved successfully",
    })
    
@swagger_auto_schema(
    method='get',
    operation_summary="Get product detail",
    operation_description="Returns full details of a product including images and options (each option has its own color, size, material, price, stock, and active discount if any).",
    responses={200: ProductDetailSerializer, 404: "Product not found"}
)
@api_view(['GET'])
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    serializer = ProductDetailSerializer(
    product,
    context={'request': request}
)
    return Response({"data": serializer.data, "message": "Product retrieved successfully"})

@swagger_auto_schema(
    method='get',
    operation_summary="Get related products",
    operation_description="Returns other active products from the same category, excluding the product itself.",
    responses={200: ProductSerializer(many=True)}
)
@api_view(['GET'])
def product_related(request, pk):
    product = get_object_or_404(Product, pk=pk)
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id)
    serializer = ProductSerializer(
        related_products,
        many=True,
        context={'request': request}
)
    return Response({"data": serializer.data, "message": "Related products retrieved successfully"})


@swagger_auto_schema(
    method='post',
    operation_summary="Create a new product",
    operation_description="Creates a new product. Images and options are added separately after creation. Only accessible by admin users.",
    request_body=ProductSerializer,
    responses={201: ProductSerializer, 400: "Invalid data"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def product_create(request):
    serializer = ProductSerializer(
        data=request.data,
        context={'request': request}
)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Product created successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='put',
    operation_summary="Update a product",
    operation_description="Updates the main information of an existing product. Only accessible by admin users.",
    request_body=ProductSerializer,
    responses={200: ProductSerializer, 400: "Invalid data", 404: "Product not found"}
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    serializer = ProductSerializer(
        product,
        data=request.data,
        context={'request': request}
)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Product updated successfully"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a product",
    operation_description="Deletes a product and its images and options (cascade delete). Only accessible by admin users.",
    responses={204: "Product deleted successfully", 404: "Product not found"}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method='patch',
    operation_summary="Change product status",
    operation_description="Toggles the active/inactive status of a product. Only accessible by admin users.",
    responses={200: ProductSerializer, 404: "Product not found"}
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def product_change_status(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save()
    serializer = ProductSerializer(
        product,
        context={'request': request}
)
    return Response({"data": serializer.data, "message": "Product status updated successfully"})


# ---------- Product Image ----------

@swagger_auto_schema(
    method='post',
    operation_summary="Add an image to a product option",
    operation_description=(
        "Uploads an image for an existing ProductOption. "
        "The product field must contain a ProductOption ID."
    ),
    consumes=['multipart/form-data'],
    request_body=ProductImageUploadSerializer,
    responses={
        201: ProductImageReadSerializer,
        400: "Invalid data",
    },
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser])
def product_image_create(request):
    serializer = ProductImageUploadSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        image = serializer.save()

        output = ProductImageReadSerializer(
            image,
            context={'request': request}
        )

        return Response(
        {"data": output.data, "message": "Product image created successfully"},
        status=status.HTTP_201_CREATED
        )
       

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

@swagger_auto_schema(
    method='put',
    operation_summary="Update a product option image",
    consumes=['multipart/form-data'],
    request_body=ProductImageUploadSerializer,
    responses={
        200: ProductImageReadSerializer,
        400: "Invalid data",
        404: "Image not found",
    },
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser])
def product_image_update(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)

    serializer = ProductImageUploadSerializer(
        image,
        data=request.data,
        partial=True,
        context={'request': request}
    )

    if serializer.is_valid():
        image = serializer.save()

        output = ProductImageReadSerializer(
            image,
            context={'request': request}
        )

        return Response({"data": output.data, "message": "Product image updated successfully"})

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )
@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a product image",
    responses={
        204: "Image deleted successfully",
        404: "Image not found",
    },
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def product_image_delete(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)
    image.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)

# ---------- Product Color ----------

@swagger_auto_schema(method='post', operation_summary="Create a color", operation_description="Creates a new reusable color. Only accessible by admin users.", request_body=ProductColorSerializer, responses={201: ProductColorSerializer, 400: "Invalid data"})
@api_view(['POST'])
@permission_classes([IsAdminUser])
def product_color_create(request):
    serializer = ProductColorSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Product color created successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', operation_summary="Update a color", operation_description="Updates an existing color. Only accessible by admin users.", request_body=ProductColorSerializer, responses={200: ProductColorSerializer, 400: "Invalid data", 404: "Color not found"})
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def product_color_update(request, pk):
    color = get_object_or_404(ProductColor, pk=pk)
    serializer = ProductColorSerializer(color, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Product color updated successfully"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='delete', operation_summary="Delete a color", operation_description="Deletes a color. Only accessible by admin users. Deletion is blocked if any option still uses this color.", responses={204: "Color deleted successfully", 404: "Color not found"})
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def product_color_delete(request, pk):
    color = get_object_or_404(ProductColor, pk=pk)
    color.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Product Size ----------

@swagger_auto_schema(method='post', operation_summary="Create a size", operation_description="Creates a new reusable size. Only accessible by admin users.", request_body=ProductSizeSerializer, responses={201: ProductSizeSerializer, 400: "Invalid data"})
@api_view(['POST'])
@permission_classes([IsAdminUser])
def product_size_create(request):
    serializer = ProductSizeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Product size created successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', operation_summary="Update a size", operation_description="Updates an existing size. Only accessible by admin users.", request_body=ProductSizeSerializer, responses={200: ProductSizeSerializer, 400: "Invalid data", 404: "Size not found"})
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def product_size_update(request, pk):
    size = get_object_or_404(ProductSize, pk=pk)
    serializer = ProductSizeSerializer(size, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Product size updated successfully"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='delete', operation_summary="Delete a size", operation_description="Deletes a size. Only accessible by admin users. Deletion is blocked if any option still uses this size.", responses={204: "Size deleted successfully", 404: "Size not found"})
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def product_size_delete(request, pk):
    size = get_object_or_404(ProductSize, pk=pk)
    size.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Product Material ----------

@swagger_auto_schema(method='post', operation_summary="Create a material", operation_description="Creates a new reusable material. Only accessible by admin users.", request_body=ProductMaterialSerializer, responses={201: ProductMaterialSerializer, 400: "Invalid data"})
@api_view(['POST'])
@permission_classes([IsAdminUser])
def product_material_create(request):
    serializer = ProductMaterialSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Product material created successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', operation_summary="Update a material", operation_description="Updates an existing material. Only accessible by admin users.", request_body=ProductMaterialSerializer, responses={200: ProductMaterialSerializer, 400: "Invalid data", 404: "Material not found"})
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def product_material_update(request, pk):
    material = get_object_or_404(ProductMaterial, pk=pk)
    serializer = ProductMaterialSerializer(material, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Product material updated successfully"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='delete', operation_summary="Delete a material", operation_description="Deletes a material. Only accessible by admin users. Deletion is blocked if any option still uses this material.", responses={204: "Material deleted successfully", 404: "Material not found"})
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def product_material_delete(request, pk):
    material = get_object_or_404(ProductMaterial, pk=pk)
    material.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Product Option ----------

@swagger_auto_schema(
    method='post',
    operation_summary="Add an option to a product",
    operation_description="Adds a purchasable option (a specific color, size, and material combination) with price and stock. Each combination must be unique per product.",
    request_body=ProductOptionCreateSerializer,
    responses={201: ProductOptionCreateSerializer, 400: "Invalid data or duplicate combination"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def product_option_create(request):
    serializer = ProductOptionCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            serializer.save()
    except IntegrityError:
        return Response(
            {"error": "This color, size, and material combination already exists for this product."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"data": serializer.data, "message": "Product option created successfully"}, status=status.HTTP_201_CREATED)
    
@swagger_auto_schema(
    method='put',
    operation_summary="Update a product option",
    operation_description="Updates an existing product option. Only accessible by admin users.",
    request_body=ProductOptionCreateSerializer,
    responses={200: ProductOptionCreateSerializer, 400: "Invalid data", 404: "Option not found"}
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def product_option_update(request, pk):
    option = get_object_or_404(ProductOption, pk=pk)
    serializer = ProductOptionCreateSerializer(
        option,
        data=request.data,
        partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            serializer.save()
    except IntegrityError:
        return Response(
            {"error": "This color, size, and material combination already exists for this product."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"data": serializer.data, "message": "Product option updated successfully"})

@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a product option",
    operation_description="Deletes a single product option. Only accessible by admin users.",
    responses={204: "Option deleted successfully", 404: "Option not found"}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def product_option_delete(request, pk):
    option = get_object_or_404(ProductOption, pk=pk)
    option.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method='patch',
    operation_summary="Update stock quantity",
    operation_description="Updates only the stock quantity of a specific option. Only accessible by admin users.",
    responses={200: ProductOptionCreateSerializer, 400: "Invalid data", 404: "Option not found"}
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def product_option_update_stock(request, pk):
    option = get_object_or_404(ProductOption, pk=pk)
    stock = request.data.get('stock')

    if stock is None:
        return Response(
            {"error": "stock field is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        stock = int(stock)
    except (TypeError, ValueError):
        return Response(
            {"error": "stock must be an integer."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if stock < 0:
        return Response(
            {"error": "stock cannot be negative."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    option.stock = stock
    option.save(update_fields=['stock'])
    serializer = ProductOptionCreateSerializer(option)
    return Response({"data": serializer.data, "message": "Product option stock updated successfully"})

@swagger_auto_schema(
    method='patch',
    operation_summary="Update option prices",
    operation_description="Updates the retail and/or wholesale price of a specific option. Only accessible by admin users.",
    responses={200: ProductOptionCreateSerializer, 400: "Invalid data", 404: "Option not found"}
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def product_option_update_price(request, pk):
    option = get_object_or_404(ProductOption, pk=pk)
    retail_price = request.data.get('retail_price')
    wholesale_price = request.data.get('wholesale_price')

    if retail_price is None and wholesale_price is None:
        return Response(
            {"error": "at least one of retail_price or wholesale_price is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if retail_price is not None:
        try:
            retail_price = Decimal(str(retail_price))
        except (InvalidOperation, TypeError, ValueError):
            return Response(
                {"error": "retail_price must be a valid number."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if retail_price < 0:
            return Response(
                {"error": "retail_price cannot be negative."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        option.retail_price = retail_price

    if wholesale_price is not None:
        try:
            wholesale_price = Decimal(str(wholesale_price))
        except (InvalidOperation, TypeError, ValueError):
            return Response(
                {"error": "wholesale_price must be a valid number."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if wholesale_price < 0:
            return Response(
                {"error": "wholesale_price cannot be negative."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        option.wholesale_price = wholesale_price

    option.save(update_fields=['retail_price', 'wholesale_price'])
    serializer = ProductOptionCreateSerializer(option)
    return Response({"data": serializer.data, "message": "Product option prices updated successfully"})

# ---------- Discount ----------

@swagger_auto_schema(
    method='get',
    operation_summary="List discounted products",
    operation_description="Returns active products that have at least one option with a currently active discount.",
    responses={200: ProductSerializer(many=True)}
)
@api_view(['GET'])
def discount_product_list(request):
    now = timezone.now()
    products = Product.objects.filter(
        is_active=True,
        options__discounts__start_at__lte=now,
        options__discounts__end_at__gte=now
    ).distinct()
    serializer = ProductSerializer(
        products,
        many=True,
        context={'request': request}
)
    return Response({"data": serializer.data, "message": "Discount product list retrieved successfully"})


@swagger_auto_schema(
    method='post',
    operation_summary="Create a new discount",
    operation_description="Creates a new discount for a specific product option, including type (percentage/fixed) and expiration date. Only accessible by admin users.",
    request_body=DiscountSerializer,
    responses={201: DiscountSerializer, 400: "Invalid data"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def discount_create(request):
    serializer = DiscountSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Discount created successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='put',
    operation_summary="Update a discount",
    operation_description="Updates all fields of an existing discount. Only accessible by admin users.",
    request_body=DiscountSerializer,
    responses={200: DiscountSerializer, 400: "Invalid data", 404: "Discount not found"}
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def discount_update(request, pk):
    discount = get_object_or_404(Discount, pk=pk)
    serializer = DiscountSerializer(discount, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Discount updated successfully"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a discount",
    operation_description="Deletes a discount permanently. Only accessible by admin users.",
    responses={204: "Discount deleted successfully", 404: "Discount not found"}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def discount_delete(request, pk):
    discount = get_object_or_404(Discount, pk=pk)
    discount.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method='post',
    operation_summary="Create a discount code",
    operation_description="Creates a new single-use discount code for the whole cart. Only accessible by admin users.",
    request_body=DiscountCodeSerializer,
    responses={201: DiscountCodeSerializer, 400: "Invalid data"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def discount_code_create(request):
    serializer = DiscountCodeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Discount code created successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='put',
    operation_summary="Update a discount code",
    operation_description="Updates an existing discount code. Only accessible by admin users.",
    request_body=DiscountCodeSerializer,
    responses={200: DiscountCodeSerializer, 400: "Invalid data", 404: "Code not found"}
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def discount_code_update(request, pk):
    code = get_object_or_404(DiscountCode, pk=pk)
    serializer = DiscountCodeSerializer(code, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"data": serializer.data, "message": "Discount code updated successfully"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a discount code",
    operation_description="Deletes a discount code permanently. Only accessible by admin users.",
    responses={204: "Code deleted successfully", 404: "Code not found"}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def discount_code_delete(request, pk):
    code = get_object_or_404(DiscountCode, pk=pk)
    code.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(
    method='get',
    operation_summary="List discount codes",
    operation_description="Returns all discount codes. Only accessible by admin users.",
    responses={200: DiscountCodeSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def discount_code_list(request):
    codes = DiscountCode.objects.all()
    serializer = DiscountCodeSerializer(codes, many=True)
    return Response({"data": serializer.data, "message": "Discount code list retrieved successfully"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def discount_code_apply(request):
    
    code_value = request.data.get('code')
    if not code_value:
        return Response({"error": "code field is required"}, status=status.HTTP_400_BAD_REQUEST)

    now = timezone.now()

    with transaction.atomic():
        discount_code = DiscountCode.objects.select_for_update().filter(code=code_value).first()

        if not discount_code:
            return Response({"error": "Discount code not found."}, status=status.HTTP_404_NOT_FOUND)

        if discount_code.is_used:
            return Response({"error": "This code has already been used."}, status=status.HTTP_400_BAD_REQUEST)

        if not (discount_code.start_at <= now <= discount_code.end_at):
            return Response({"error": "This code is expired or not yet valid."}, status=status.HTTP_400_BAD_REQUEST)

        discount_code.is_used = True
        discount_code.used_by = request.user
        discount_code.used_at = now
        discount_code.save(update_fields=['is_used', 'used_by', 'used_at'])

    serializer = DiscountCodeApplySerializer(discount_code)
    return Response({"data": serializer.data, "message": "Discount code applied successfully"})