from django.shortcuts import render,get_object_or_404
from .models import *
from .permissions import *
from rest_framework.exceptions import ValidationError
from .serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .status import ConnectionStatus
from django.contrib.auth.hashers import make_password

class MerchantViews(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        all_merchants = Merchant.objects.all()
        serializer = MerchantSerializer(all_merchants, many=True)
        return Response(serializer.data)

class Signup(APIView):
    permission_classes = [NotAuthenticated]
    @extend_schema(
        request=UserSerializer, # Serializer used for the request body
        responses={201: UserSerializer}, # Serializer used for the response body
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            response_data = {
                'uid': user.uid,
                'email': user.email,
                'name': user.name,
                'dob': user.dob,
                'is_merchant':user.is_merchant,
            }

            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [NotAuthenticated]
    @extend_schema(
        request=UserLoginSerializer, # Serializer used for the request body
        responses={201: UserLoginSerializer}, # Serializer used for the response body
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate( username=email, password=password)

            if user:
                refresh = RefreshToken.for_user(user)

                response_data = {
                    'uid': user.uid,
                    'email': user.email,
                    'tokens': {
                        'access_token': str(refresh.access_token),
                        'refresh_token': str(refresh),
                    }
                }

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = {
                    'error': 'Invalid credentials'
                }
                return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self,request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password =serializer.validated_data['old_password']
            if not user.check_password(old_password):
                return Response({"detail": "Invalid old password."}, status=status.HTTP_400_BAD_REQUEST)

            if serializer.validated_data['password1'] !=serializer.validated_data['password2']:
                raise ValidationError("Passwords do not match.")

            user.set_password(serializer.validated_data['password1'])
            user.save()
            return Response("Password changed successfully.", status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryListView(APIView):
    permission_classes = [AdminOrAuthenticatedUserPermission]
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationSerializerView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        all_shops = Organization.objects.all()
        serializer = OrganizationSerializer(all_shops, many=True)
        return Response(serializer.data)


class MyShopSerializerView(APIView):
    permission_classes = [IsMerchant]
    def get(self, request):
        merchant = request.user

        my_shops = Organization.objects.filter(user=merchant)

        serializer = OrganizationSerializer(my_shops, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=OrganizationSerializer,
        responses={201: OrganizationSerializer},
    )
    def post(self, request):
        merchant = request.user
        my_shops = Organization.objects.filter(user=merchant)
        my_shops.update(is_default=False)   # Deactivating all the merchant's shops

        serializer = OrganizationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            shop = serializer.save()
            shop.is_default = True  # Activating the newly created shop
            shop.save()
            org_user = OrganizationUser.objects.create(user=request.user,organization=shop,role=UserRole.OWNER)
            return Response(serializer.data, status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class MyActiveShopSerializerView(APIView):
    permission_classes = [IsOrganizationUser]
    def get(self, request, shop_slug):
        merchant = request.user
        my_shops = Organization.objects.filter(user=merchant)
        my_shops.update(is_default=False)   # Deactivating all the merchant's shops
        shop = Organization.objects.get(slug=shop_slug)
        shop.is_default=True    #activating my specific shop
        serializer = MyShopDetailSerializer(shop)
        return Response(serializer.data)



class ConnectionRequestCreateView(APIView):
    permission_classes = [IsAdminOrOwner]
    @extend_schema(
        request=OrganizationSerializer, # Serializer used for the request body
        responses={201: OrganizationSerializer}, # Serializer used for the response body
    )

    def get(self, request, shop_slug):

        sender_shop = get_object_or_404(Organization, slug=shop_slug)
        sender_shop.is_default=True
        sender_shop.save()
        query = ShopConnection.objects.filter(sender_shop=sender_shop) #.values_list('receiver_shop', flat=True)

        serializer = ConnectionRequestSerializer(query, many=True)
        return Response(serializer.data)

    def post(self, request, shop_slug):
        serializer = ConnectionRequestSerializer(data=request.data)
        if serializer.is_valid():
            receiver_shop_uid = serializer.validated_data.get('receiver_shop_uid')
            sender_shop = get_object_or_404(Organization, slug=shop_slug)
            # status = serializer.validated_data.get('status')
            receiver_shop = Organization.objects.get(uid=receiver_shop_uid)
            if sender_shop.category==receiver_shop.category:
                connection = ShopConnection.objects.create(
                    sender_shop=sender_shop,
                    receiver_shop=receiver_shop,
                    status=ConnectionStatus.PENDING
                )

                res = ConnectionRequestSerializer(connection)
                return Response(res.data, status=status.HTTP_201_CREATED)
            else:
                raise ValidationError('You are not in the same category.')

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrganizationUserView(APIView):
    permission_classes = [IsOrganizationUser,IsOwner]
    def get(self,request,shop_slug):
        active = Organization.objects.get(slug=shop_slug)
        print('---------------',active)
        all_user = OrganizationUser.objects.filter(organization=active)

        print('---------------',all_user)
        serializer = OrganizationUserSerializer(all_user,many = True)
        return Response(serializer.data, status.HTTP_200_OK)

    def post(self,request,shop_slug):
        active = Organization.objects.get(slug=shop_slug)
        print('---------------',active)
        serializer = OrganizationUserSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            role =serializer.validated_data['role']
            try:
                user = Merchant.objects.get(email=email)
                org_user = OrganizationUser.objects.create(user=user,organization=active,role=role)

            except:
                if role==UserRole.OWNER:
                    user = Merchant.objects.create(
                        email = email,
                        name = "Set Your name",
                        dob='2000-01-01',
                        is_merchant = True
                    )
                else:
                    user = Merchant.objects.create(
                        email = email,
                        name = "Set Your name",
                        dob='2000-01-01',
                        is_merchant = False
                    )
                user.password =make_password("Repliq2023")
                user.save()
                org_user = OrganizationUser.objects.create(user=user,organization=active,role=role)

            serializer = OrganizationUserSerializer(org_user)
            return Response(serializer.data,status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrgUserDetail(APIView):
    permission_classes = [IsOrganizationUser]
    def get(self,request,shop_slug,user_uid):
        org = Organization.objects.get(slug= shop_slug)
        user = OrganizationUser.objects.get(uid=user_uid)
        detail = OrganizationUserSerializer(user)
        return Response(detail.data,status.HTTP_200_OK)

    def delete(self, requset,shop_slug,user_uid):
        user = get_object_or_404(OrganizationUser,uid=user_uid)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EditUserView(APIView):
    def get(self,request):
        email = request.user.email
        # print('-------------------',email)
        me = Merchant.objects.get(email=email)
        print('---------------------------------',me)
        serializer = EditUserSerializer(me)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self,request):
        email = request.user.email
        me = Merchant.objects.get(email=email)
        serializer = EditUserSerializer(me, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConnectionReceivedView(APIView):
    permission_classes = [IsAdminOrOwner]
    @extend_schema(
        request=ConnectionResponseSerializer, # Serializer used for the request body
        responses={201: ConnectionResponseSerializer}, # Serializer used for the response body
    )

    def get(self, request, shop_slug):

        receiver_shop = get_object_or_404(Organization, slug=shop_slug)
        receiver_shop.is_default=True
        receiver_shop.save()
        query = ShopConnection.objects.filter(receiver_shop=receiver_shop) #.values_list('receiver_shop', flat=True)

        serializer = ConnectionResponseSerializer(query, many=True)
        return Response(serializer.data)


class ConnectionResponseView(APIView):
    permission_classes = [IsAdminOrOwner]
    @extend_schema(
        request=ConnectionResponseSerializer, # Serializer used for the request body
        responses={201: ConnectionResponseSerializer}, # Serializer used for the response body
    )

    def get(self, request, shop_slug, shopconnection_uid):

        receiver_shop = get_object_or_404(Organization, slug=shop_slug)
        receiver_shop.is_default=True
        receiver_shop.save()
        query = ShopConnection.objects.filter(uid=shopconnection_uid) #.values_list('receiver_shop', flat=True)

        serializer = ConnectionResponseSerializer(query, many=True)
        return Response(serializer.data)

    def patch(self, request, shop_slug, shopconnection_uid):
        receiver_shop = get_object_or_404(Organization, slug=shop_slug)
        receiver_shop.is_default = True
        receiver_shop.save()

        shop_connection = get_object_or_404(ShopConnection, uid=shopconnection_uid, receiver_shop=receiver_shop)

        serializer = ConnectionResponseSerializer(shop_connection, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('status') == ConnectionStatus.APPROVED:
            # shop_connection.update()
            sender_shop = shop_connection.sender_shop

            ShopConnection.objects.create(sender_shop=receiver_shop, receiver_shop=sender_shop, status=ConnectionStatus.APPROVED)

        elif serializer.validated_data.get('status') == ConnectionStatus.DECLINED:
            shop_connection.delete()
        serializer.save()

        return Response(serializer.data)

class MyProductView(APIView):
    permission_classes = [OwnerOrAdminPermission]
    def get(self, request, shop_slug):
        active_shop = Organization.objects.get(slug=shop_slug)
        active_shop.is_default = True
        active_shop.save()

        my_products = Product.objects.filter(organization=active_shop)
        serializer = ProductSerializer(my_products, many=True)
        return Response(serializer.data)

    def post(self,request, shop_slug):
        # merchant = request.user.merchant
        all_shop = Organization.objects.all().update(is_default=False)
        print(all_shop)
        active_shop = Organization.objects.get(slug=shop_slug)
        active_shop.is_default = True
        active_shop.save()
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            shop = get_object_or_404(Organization, is_default=True)

            product = serializer.save(organization=shop)
            product_serializer = ProductSerializer(product)
            return Response(product_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SameCategoryShop(APIView):
    permission_classes = [IsAdminOrOwner]
    def get(self,request,shop_slug):
        current_shop = get_object_or_404(Organization, slug=shop_slug)
        same_category_shops = Organization.objects.filter(category=current_shop.category)

        res = OrganizationSerializer(same_category_shops, many=True)
        return Response(res.data,status.HTTP_200_OK)

class ConnectedShops(APIView):
    permission_classes = [IsAdminOrOwner]
    def get(self, request, shop_slug):
        active_shop = get_object_or_404(Organization, slug=shop_slug)
        sender_shops = active_shop.sent_connections.filter(status=ConnectionStatus.APPROVED).values_list('receiver_shop', flat=True)
        connected_shops = Organization.objects.filter(pk__in=sender_shops)
        serializer = OrganizationSerializer(connected_shops, many=True)
        return Response(serializer.data)


class BuyProducts(APIView):
    permission_classes = [IsAdminOrOwner]
    def get(self, request, shop_slug):
        # user = request.user
        active_shop = get_object_or_404(Organization, slug=shop_slug)
        sender_shops = active_shop.sent_connections.filter(status=ConnectionStatus.APPROVED).values_list('receiver_shop', flat=True)
        connected_shops = Organization.objects.filter(pk__in=sender_shops)
        products = Product.objects.filter(organization__in=connected_shops)
        serializer = ProductSerializer(products,many=True)
        return Response(serializer.data)

    def post(self, request, shop_slug):
        active_shop = get_object_or_404(Organization, slug=shop_slug)
        # print('---------------active shop----',active_shop.id)

        sender_shops = active_shop.sent_connections.filter(status=ConnectionStatus.APPROVED).values_list('receiver_shop', flat=True)
        connected_shops = Organization.objects.filter(pk__in=sender_shops)
        user = request.user
        # print('----------user----------',user)
        product_serializer = BuyProductSerializer(data=request.data)
        if product_serializer.is_valid():
            product_uid = product_serializer.validated_data['uid']
            product = Product.objects.get(uid=product_uid)
            price = product.price
            quantity = product_serializer.validated_data['quantity']
            total_price = 0
            product = get_object_or_404(Product, uid=product_uid, organization__in=connected_shops)
            # net_price = product.price*quantity
            try:
                cart = Cart.objects.get(organization=active_shop)
            except:
                cart = Cart.objects.create(organization=active_shop,total_price=0)
            cart_items = cart.cartitem_set.filter(organization=active_shop)

            for item in cart_items:
                total_price+=item.net_price
            cart.total_price = total_price
            cart.save()
            net_price = quantity*price
            cart_item,_ = CartItem.objects.get_or_create(cart=cart,organization=active_shop, product=product,quantity=quantity,net_price = net_price)


            cart_item.quantity = quantity
            cart_item.save()

            return Response(product_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartItems(APIView):
    permission_classes = [IsOrganizationUser]
    def get(self, request, shop_slug):
        active_shop = get_object_or_404(Organization, slug=shop_slug)
        total_price = 0
        try:
            cart = Cart.objects.prefetch_related("cartitem_set").get(organization=active_shop)
        except:
            raise ValidationError('No cart for you')
        cart_items = cart.cartitem_set.filter(organization=active_shop)

        for item in cart.cartitem_set.filter():
            print(item)
            total_price+=item.net_price
        cart.total_price=total_price
        cart.save()
        serializer = CartSerializer(cart)

        return Response(serializer.data)


class OrderItems(APIView):
    permission_classes = [IsAdminOrOwner]
    def get(self, request, shop_slug):
        active_shop = get_object_or_404(Organization, slug=shop_slug)
        total_price = 0
        order = Order.objects.prefetch_related("orderitem_set").filter(organization=active_shop)
        # order_items = order.orderitem_set.filter(shop=active_shop,user=request.user)
        cart = Cart.objects.get(organization=active_shop)
        total_price = cart.total_price

        order.total_price=total_price
        # order.save()
        cart.delete()
        serializer = OrderSerializer(order, many=True)

        return Response(serializer.data)



class OrderView(APIView):
    permission_classes = [IsAdminOrOwner]

    def post(self, request, shop_slug):
        shop = get_object_or_404(Organization, slug=shop_slug)
        try:
            cart = Cart.objects.get(organization=shop)
        except:
            raise ValidationError("You didn't add any products in your Cart")
        total_price = cart.total_price
        # print('----------------------',total_price)

        cart_items = CartItem.objects.filter(organization=shop)
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            delivery_address = serializer.validated_data['delivery_address']
            payment_method = serializer.validated_data['payment_method']
            status = OrderStatus.ON_PROCESSING

            # Create the order
            order = Order.objects.create(organization=shop, delivery_address=delivery_address, payment_method=payment_method,status=status,total_price=total_price)

            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    net_price= cart_item.net_price
                )


            cart_items.delete()

            return Response(serializer.data)
        return Response(serializer.errors)

