from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework import serializers
from merchant.models import *
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

class MerchantSerializer(serializers.Serializer):
    uid = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(max_length=50)
    name = serializers.CharField(max_length=50)
    dob = serializers.DateField()
    is_merchant = serializers.BooleanField(default=True)

    def create(self, validated_data):
        return Merchant.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.name = validated_data.get('name', instance.name)
        instance.dob = validated_data.get('dob', instance.dob)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.is_staff = validated_data.get('is_staff', instance.is_staff)
        instance.save()
        return instance


class UserSerializer(serializers.Serializer):
    uid = serializers.UUIDField(read_only=True)
    email = serializers.EmailField()
    name = serializers.CharField()
    is_merchant = serializers.BooleanField()
    dob = serializers.DateField()
    password1 = serializers.CharField()
    password2 = serializers.CharField()
    extra_kwargs = {'password':{'write_only':True,'min_length':5}}
    is_active = serializers.BooleanField(default=True)
    is_staff = serializers.BooleanField(default=False)
    def create(self, validated_data):
        if validated_data['password1'] != validated_data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        user = User.objects.create_user(
            email=validated_data['email'],
            name = validated_data['name'],
            is_merchant = validated_data['is_merchant'],
            dob = validated_data['dob'],
            password=validated_data['password1'],
        )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    password1 = serializers.CharField()
    password2 = serializers.CharField()
    # def update(self, instance, validated_data):
    #     return 1

class EditUserSerializer(serializers.Serializer):
    email = serializers.EmailField(read_only=True)
    name = serializers.CharField()
    dob = serializers.DateField()
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.dob = validated_data.get('dob', instance.dob)
        instance.save()
        return instance


class UserLoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField()
    extra_kwargs = {'password':{'write_only':True,'min_length':5}}
    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        user = authenticate(username=email, password=password)

        if user:
            return user
        else:
            raise serializers.ValidationError('Invalid credentials')


class CategorySerializer(serializers.Serializer):
    uid = serializers.UUIDField(read_only=True)
    title = serializers.CharField()
    slug = serializers.SlugField(read_only=True)

    def create(self, validated_data):
        return Category.objects.create(**validated_data)

class OrganizationSerializer(serializers.Serializer):
    uid = serializers.UUIDField(read_only = True)
    name = serializers.CharField()
    slug = serializers.SlugField(read_only=True)
    merchant = serializers.CharField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    address = serializers.CharField()
    description = serializers.CharField()
    active = serializers.BooleanField(default=False)
    def create(self, validated_data):
        category_id = validated_data.pop('category_id')
        user=validated_data.pop('user')
        mechant=Merchant.objects.get(email=user.email)
        category = Category.objects.get(id=category_id)
        organization = Organization.objects.create(category=category, merchant=mechant,**validated_data)
        return organization


class OrganizationSerializer(serializers.Serializer):
    uid = serializers.UUIDField(read_only = True)
    name = serializers.CharField()
    slug = serializers.SlugField(read_only=True)
    merchant = serializers.CharField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    category = CategorySerializer(read_only=True)
    category_uid = serializers.UUIDField(write_only=True)
    address = serializers.CharField()
    description = serializers.CharField()
    is_default = serializers.BooleanField(default=False)
    def create(self, validated_data):
        category_uid = validated_data.pop('category_uid')
        user=validated_data.pop('user')
        mechant=Merchant.objects.get(email=user.email)
        category = Category.objects.get(uid=category_uid)
        organization = Organization.objects.create(category=category, user=mechant,**validated_data)
        return organization
        # return Merchant.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.address = validated_data.get('address', instance.address)
        instance.save()
        return instance

class MyShopSerializer(OrganizationSerializer):
    def create(self, validated_data):
        category_id = validated_data.pop('category_id')
        user=validated_data.pop('user')
        mechant=Merchant.objects.get(user=user)
        category = Category.objects.get(id=category_id)
        shop = Organization.objects.create(category=category, merchant=mechant,**validated_data)
        return shop
        # return Merchant.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.address = validated_data.get('address', instance.address)
        instance.save()
        return instance

class MyShopDetailSerializer(serializers.Serializer):
    uid = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    slug = serializers.SlugField(read_only=True)
    user = MerchantSerializer()
    category = CategorySerializer()
    address = serializers.CharField()
    description = serializers.CharField()
    is_default = serializers.BooleanField(default=False)

class OrganizationUserSerializer(serializers.Serializer):
    uid = serializers.UUIDField(read_only = True)
    user = MerchantSerializer(read_only=True)
    email = serializers.EmailField(write_only=True)
    role = serializers.CharField()
    def create(self, validated_data):
        return OrganizationUser.objects.create(**validated_data)
    # organization =OrganizationSerializer()


class ConnectionRequestSerializer(serializers.Serializer):
    uid = serializers.UUIDField(read_only=True)
    receiver_shop_uid = serializers.UUIDField(write_only=True)
    receiver_shop = OrganizationSerializer(read_only=True)
    slug = serializers.SlugField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)

    def create(self, validated_data):
        receiver_shop_uid = validated_data.get('receiver_shop_uid')
        sender_shop_data = Organization.objects.get(active=True)
        status = validated_data.get('status')
        sender_shop = Organization.objects.get(id=sender_shop_data['id'])
        receiver_shop = Organization.objects.get(uid=receiver_shop_uid)

        return ShopConnection.objects.create(sender_shop=sender_shop, receiver_shop=receiver_shop, status=status)

    def update(self, instance, validated_data):
        status = validated_data.get('status')
        instance.status = status
        instance.save()
        return instance


class ConnectionResponseSerializer(serializers.Serializer):
    uid = serializers.UUIDField(read_only=True)
    sender_shop = OrganizationSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    status = serializers.CharField()

    def update(self, instance, validated_data):
        status = validated_data.get('status')
        instance.status = status
        instance.save()
        return instance


class ProductSerializer(serializers.Serializer):
    uid = serializers.UUIDField(read_only=True)
    title = serializers.CharField()
    price = serializers.DecimalField(max_digits=8, decimal_places=2)
    quantity = serializers.IntegerField()
    slug = serializers.SlugField(read_only=True)
    shop = OrganizationSerializer(read_only=True)
    def create(self, validated_data):
        return Product.objects.create(**validated_data)


class BuyProductSerializer(serializers.Serializer):
    uid = serializers.UUIDField()
    title = serializers.CharField(read_only=True)
    price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    quantity = serializers.IntegerField()
    def create(self, validated_data):
        return CartItem.objects.create(**validated_data)

class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()
    net_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    class Meta:
        model = CartItem
        fields = ['product', 'quantity','net_price']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True,read_only=True,source='cartitem_set')
    total_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    class Meta:
        model = Cart
        fields = ['items', 'total_price']


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()
    net_price = serializers.DecimalField(max_digits=8, decimal_places=2,read_only=True)
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity','net_price']

class OrderSerializer(serializers.Serializer):
    shop = serializers.CharField(source='organization.name', read_only=True)
    # orderitem_set = OrderItemSerializer(many=True, read_only=True)
    items = OrderItemSerializer(source = 'orderitem_set',many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=8, decimal_places=2,read_only=True)
    delivery_address = serializers.CharField(max_length=150)
    payment_method = serializers.ChoiceField(choices=PaymentOption.choices)
    status = serializers.ChoiceField(choices=OrderStatus.choices , read_only = True)

    def create(self, validated_data):
        return Order.objects.create(**validated_data)

