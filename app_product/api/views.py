from rest_framework.decorators import api_view, permission_classes
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


from app_product.models import (
    Category, Product, ProductImage,
    ProductColor, ProductSize, ProductMaterial,
    ProductOption, Discount
)
from app_product.api.serializers import (
    CategorySerializer, ProductSerializer, ProductDetailSerializer,
    ProductImageSerializer, ProductColorSerializer, ProductSizeSerializer,
    ProductMaterialSerializer, ProductOptionCreateSerializer, DiscountSerializer ,DiscountCodeSerializer, DiscountCodeApplySerializer
)


# ---------- Category ----------

@swagger_auto_schema(
    method='get',
    operation_summary="List categories",
    operation_description="Returns all active categories. Use ?parent=<id> to get subcategories of a category, or ?parent=null to get only root categories.",
    manual_parameters=[
        openapi.Parameter('parent', openapi.IN_QUERY, description="Parent category id, or 'null' for root categories", type=openapi.TYPE_STRING),
    ],
    responses={200: CategorySerializer(many=True)}
)
@api_view(['GET'])
def category_list(request):
    categories = Category.objects.filter(is_active=True)
    parent = request.GET.get('parent')
    if parent == 'null':
        categories = categories.filter(parent__isnull=True)
    elif parent:
        categories = categories.filter(parent_id=parent)
    serializer = CategorySerializer(categories, many=True)
    return Response({"category_list": serializer.data})


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
    return Response(serializer.data)


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
        return Response(serializer.data, status=status.HTTP_201_CREATED)
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
        return Response(serializer.data)
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
    operation_summary="List products with filter and pagination",
    operation_description="Returns a paginated list of active products with their images.",
    manual_parameters=[
        openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category id", type=openapi.TYPE_INTEGER),
        openapi.Parameter('brand', openapi.IN_QUERY, description="Filter by brand", type=openapi.TYPE_STRING),
        openapi.Parameter('gender', openapi.IN_QUERY, description="Filter by gender", type=openapi.TYPE_STRING),
        openapi.Parameter('search', openapi.IN_QUERY, description="Search by product name", type=openapi.TYPE_STRING),
        openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
    ],
    responses={200: ProductSerializer(many=True)}
)
@api_view(['GET'])
def product_list(request):
    products = Product.objects.filter(is_active=True)

    category = request.GET.get('category')
    if category:
        products = products.filter(category_id=category)

    brand = request.GET.get('brand')
    if brand:
        products = products.filter(brand__icontains=brand)

    gender = request.GET.get('gender')
    if gender:
        products = products.filter(gender=gender)

    search = request.GET.get('search')
    if search:
        products = products.filter(name__icontains=search)

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    serializer = ProductSerializer(page_obj, many=True)
    return Response({
        "count": paginator.count,
        "total_pages": paginator.num_pages,
        "current_page": page_obj.number,
        "products": serializer.data
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
    serializer = ProductDetailSerializer(product)
    return Response(serializer.data)


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
    serializer = ProductSerializer(related_products, many=True)
    return Response({"related_products": serializer.data})


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
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
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
    serializer = ProductSerializer(product, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
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
    serializer = ProductSerializer(product)
    return Response(serializer.data)


# ---------- Product Image ----------

@swagger_auto_schema(
    method='post',
    operation_summary="Add an image to a product",
    operation_description="Uploads a new image for an existing product. Only accessible by admin users.",
    request_body=ProductImageSerializer,
    responses={201: ProductImageSerializer, 400: "Invalid data"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def product_image_create(request):
    serializer = ProductImageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='put',
    operation_summary="Update a product image",
    operation_description="Updates an existing product image. Only accessible by admin users.",
    request_body=ProductImageSerializer,
    responses={200: ProductImageSerializer, 400: "Invalid data", 404: "Image not found"}
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def product_image_update(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)
    serializer = ProductImageSerializer(image, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a product image",
    operation_description="Deletes a single product image. Only accessible by admin users.",
    responses={204: "Image deleted successfully", 404: "Image not found"}
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', operation_summary="Update a color", operation_description="Updates an existing color. Only accessible by admin users.", request_body=ProductColorSerializer, responses={200: ProductColorSerializer, 400: "Invalid data", 404: "Color not found"})
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def product_color_update(request, pk):
    color = get_object_or_404(ProductColor, pk=pk)
    serializer = ProductColorSerializer(color, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', operation_summary="Update a size", operation_description="Updates an existing size. Only accessible by admin users.", request_body=ProductSizeSerializer, responses={200: ProductSizeSerializer, 400: "Invalid data", 404: "Size not found"})
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def product_size_update(request, pk):
    size = get_object_or_404(ProductSize, pk=pk)
    serializer = ProductSizeSerializer(size, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', operation_summary="Update a material", operation_description="Updates an existing material. Only accessible by admin users.", request_body=ProductMaterialSerializer, responses={200: ProductMaterialSerializer, 400: "Invalid data", 404: "Material not found"})
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def product_material_update(request, pk):
    material = get_object_or_404(ProductMaterial, pk=pk)
    serializer = ProductMaterialSerializer(material, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
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
    if serializer.is_valid():
        try:
            serializer.save()
        except Exception:
            return Response(
                {"error": "This color, size, and material combination already exists for this product."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    serializer = ProductOptionCreateSerializer(option, data=request.data)
    if serializer.is_valid():
        try:
            serializer.save()
        except Exception:
            return Response(
                {"error": "This color, size, and material combination already exists for this product."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        return Response({"error": "stock field is required"}, status=status.HTTP_400_BAD_REQUEST)
    option.stock = stock
    option.save()
    serializer = ProductOptionCreateSerializer(option)
    return Response(serializer.data)


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
            status=status.HTTP_400_BAD_REQUEST
        )

    if retail_price is not None:
        option.retail_price = retail_price
    if wholesale_price is not None:
        option.wholesale_price = wholesale_price

    option.save()
    serializer = ProductOptionCreateSerializer(option)
    return Response(serializer.data)


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
    serializer = ProductSerializer(products, many=True)
    return Response({"discount_products": serializer.data})


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
        return Response(serializer.data, status=status.HTTP_201_CREATED)
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
        return Response(serializer.data)
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)
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
        return Response(serializer.data)
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
    return Response({"discount_codes": serializer.data})

@swagger_auto_schema(
    method='post',
    operation_summary="Apply a discount code",
    operation_description="Validates and applies a discount code to the user's cart. The code must be active, within its valid date range, and not used before. Once applied, the code is marked as used and cannot be reused. Only accessible by logged-in users.",
    manual_parameters=[
        openapi.Parameter('code', openapi.IN_QUERY, description="The discount code to apply", type=openapi.TYPE_STRING, required=True),
    ],
    responses={200: DiscountCodeApplySerializer, 400: "Invalid, expired, or already used code", 404: "Code not found"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def discount_code_apply(request):
    code_value = request.data.get('code')
    if not code_value:
        return Response({"error": "code field is required"}, status=status.HTTP_400_BAD_REQUEST)

    discount_code = get_object_or_404(DiscountCode, code=code_value)

    if discount_code.is_used:
        return Response({"error": "This code has already been used."}, status=status.HTTP_400_BAD_REQUEST)

    
    now = timezone.now()
    if not (discount_code.start_at <= now <= discount_code.end_at):
        return Response({"error": "This code is expired or not yet valid."}, status=status.HTTP_400_BAD_REQUEST)

    discount_code.is_used = True
    discount_code.used_by = request.user
    discount_code.used_at = now
    discount_code.save()

    serializer = DiscountCodeApplySerializer(discount_code)
    return Response(serializer.data)