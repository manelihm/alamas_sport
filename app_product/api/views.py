from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone

from app_product.models import Category, Subcategory, Product ,ProductImage, ProductOption, ProductMaterial ,Discount
from app_product.api.serializers import (
    CategorySerializer, SubcategorySerializer, SubcategoryDetailSerializer,
    ProductSerializer, ProductDetailSerializer,
    ProductImageSerializer, ProductOptionSerializer, ProductMaterialSerializer ,DiscountSerializer
)


@swagger_auto_schema(
    method='get',
    operation_summary="List active categories",
    operation_description="Returns all categories where status is active.",
    responses={200: CategorySerializer(many=True)}
)
@api_view(['GET'])
def category_list(request):
    categories = Category.objects.filter(is_active=True)
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
    method='get',
    operation_summary="List subcategories by category",
    operation_description="Returns all active subcategories that belong to a specific category.",
    responses={200: SubcategorySerializer(many=True)}
)
@api_view(['GET'])
def subcategory_list(request, category_id):
    subcategories = Subcategory.objects.filter(category_id=category_id, is_active=True)
    serializer = SubcategorySerializer(subcategories, many=True)
    return Response({"subcategory_list": serializer.data})


@swagger_auto_schema(
    method='post',
    operation_summary="Create a new category",
    operation_description="Creates a new category. Only accessible by admin users.",
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
    operation_description="Deletes a category permanently. Only accessible by admin users.",
    responses={204: "Category deleted successfully", 404: "Category not found"}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method='get',
    operation_summary="Get subcategory detail",
    operation_description="Returns the details of a single subcategory along with its products.",
    responses={200: SubcategoryDetailSerializer, 404: "Subcategory not found"}
)
@api_view(['GET'])
def subcategory_detail(request, pk):
    subcategory = get_object_or_404(Subcategory, pk=pk, is_active=True)
    serializer = SubcategoryDetailSerializer(subcategory)
    return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    operation_summary="Create a new subcategory",
    operation_description="Creates a new subcategory under a category. Only accessible by admin users.",
    request_body=SubcategorySerializer,
    responses={201: SubcategorySerializer, 400: "Invalid data"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def subcategory_create(request):
    serializer = SubcategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='put',
    operation_summary="Update a subcategory",
    operation_description="Updates all fields of an existing subcategory. Only accessible by admin users.",
    request_body=SubcategorySerializer,
    responses={200: SubcategorySerializer, 400: "Invalid data", 404: "Subcategory not found"}
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def subcategory_update(request, pk):
    subcategory = get_object_or_404(Subcategory, pk=pk)
    serializer = SubcategorySerializer(subcategory, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a subcategory",
    operation_description="Deletes a subcategory permanently. Only accessible by admin users.",
    responses={204: "Subcategory deleted successfully", 404: "Subcategory not found"}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def subcategory_delete(request, pk):
    subcategory = get_object_or_404(Subcategory, pk=pk)
    subcategory.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method='get',
    operation_summary="List products with filter and pagination",
    operation_description="Returns a paginated list of active products with their images. Supports filtering by category, subcategory, brand, and gender, and searching by name.",
    manual_parameters=[
        openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category id", type=openapi.TYPE_INTEGER),
        openapi.Parameter('subcategory', openapi.IN_QUERY, description="Filter by subcategory id", type=openapi.TYPE_INTEGER),
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

    subcategory = request.GET.get('subcategory')
    if subcategory:
        products = products.filter(subcategory_id=subcategory)

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
    operation_description="Returns the full details of a single product, including images, purchase options (color, size, price, stock), and materials.",
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
    operation_description="Returns other active products from the same category, excluding the given product itself. Useful for 'related products' sections.",
    responses={200: ProductSerializer(many=True)}
)
@api_view(['GET'])
def product_related(request, pk):
    product = get_object_or_404(Product, pk=pk)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)
    serializer = ProductSerializer(related_products, many=True)
    return Response({"related_products": serializer.data})


@swagger_auto_schema(
    method='post',
    operation_summary="Create a new product",
    operation_description="Creates a new product. Only accessible by admin users. Images, options, and materials are added separately after creation.",
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
    method='post',
    operation_summary="Add an option to a product",
    operation_description="Adds a new purchasable option (color + size combination) with price and stock for an existing product. Only accessible by admin users.",
    request_body=ProductOptionSerializer,
    responses={201: ProductOptionSerializer, 400: "Invalid data"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def product_option_create(request):
    serializer = ProductOptionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    operation_summary="Add a material to a product",
    operation_description="Adds a new material entry for an existing product. Only accessible by admin users.",
    request_body=ProductMaterialSerializer,
    responses={201: ProductMaterialSerializer, 400: "Invalid data"}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def product_material_create(request):
    serializer = ProductMaterialSerializer(data=request.data)
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
    method='put',
    operation_summary="Update a product option",
    operation_description="Updates an existing product option (color, size, price, stock). Only accessible by admin users.",
    request_body=ProductOptionSerializer,
    responses={200: ProductOptionSerializer, 400: "Invalid data", 404: "Option not found"}
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def product_option_update(request, pk):
    option = get_object_or_404(ProductOption, pk=pk)
    serializer = ProductOptionSerializer(option, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='put',
    operation_summary="Update a product material",
    operation_description="Updates an existing product material entry. Only accessible by admin users.",
    request_body=ProductMaterialSerializer,
    responses={200: ProductMaterialSerializer, 400: "Invalid data", 404: "Material not found"}
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def product_material_update(request, pk):
    material = get_object_or_404(ProductMaterial, pk=pk)
    serializer = ProductMaterialSerializer(material, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a product",
    operation_description="Deletes a product permanently, including its images, options, and materials (cascade delete). Only accessible by admin users.",
    responses={204: "Product deleted successfully", 404: "Product not found"}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

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

@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a product option",
    operation_description="Deletes a single product option (color/size/price/stock combination). Only accessible by admin users.",
    responses={204: "Option deleted successfully", 404: "Option not found"}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def product_option_delete(request, pk):
    option = get_object_or_404(ProductOption, pk=pk)
    option.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a product material",
    operation_description="Deletes a single product material entry. Only accessible by admin users.",
    responses={204: "Material deleted successfully", 404: "Material not found"}
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def product_material_delete(request, pk):
    material = get_object_or_404(ProductMaterial, pk=pk)
    material.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(
    method='patch',
    operation_summary="Change product status",
    operation_description="Toggles the active/inactive status of a product without changing any other field. Only accessible by admin users.",
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

@swagger_auto_schema(
    method='patch',
    operation_summary="Update stock quantity",
    operation_description="Updates the stock quantity of a specific product option (color/size combination) without changing price or other fields. Only accessible by admin users.",
    responses={200: ProductOptionSerializer, 400: "Invalid data", 404: "Option not found"}
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
    serializer = ProductOptionSerializer(option)
    return Response(serializer.data)

@swagger_auto_schema(
    method='patch',
    operation_summary="Update option prices",
    operation_description="Updates the retail and wholesale price of a specific product option without changing stock or other fields. Only accessible by admin users.",
    responses={200: ProductOptionSerializer, 400: "Invalid data", 404: "Option not found"}
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
    serializer = ProductOptionSerializer(option)
    return Response(serializer.data)




@swagger_auto_schema(
    method='get',
    operation_summary="List discounted products",
    operation_description="Returns all active products that currently have an active discount.",
    responses={200: ProductSerializer(many=True)}
)
@api_view(['GET'])
def discount_product_list(request):
    now = timezone.now()
    discounted_product_ids = Discount.objects.filter(
        status=True,
        start_at__lte=now,
        end_at__gte=now
    ).values_list('product_id', flat=True)

    products = Product.objects.filter(id__in=discounted_product_ids, is_active=True)
    serializer = ProductSerializer(products, many=True)
    return Response({"discount_products": serializer.data})


@swagger_auto_schema(
    method='post',
    operation_summary="Create a new discount",
    operation_description="Creates a new discount for a product, including type (percentage/fixed) and expiration date. Only accessible by admin users.",
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
    method='patch',
    operation_summary="Change discount status",
    operation_description="Toggles the active/inactive status of a discount without changing any other field. Only accessible by admin users.",
    responses={200: DiscountSerializer, 404: "Discount not found"}
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def discount_change_status(request, pk):
    discount = get_object_or_404(Discount, pk=pk)
    discount.status = not discount.status
    discount.save()
    serializer = DiscountSerializer(discount)
    return Response(serializer.data)