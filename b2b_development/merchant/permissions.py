from rest_framework.permissions import BasePermission
from .models import Organization, OrganizationUser
from .status import UserRole

class IsOrganizationUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        shop_slug = view.kwargs.get('shop_slug')  # Assumes the URL parameter is named 'shop_id'
        print(shop_slug)
        try:
            shop = Organization.objects.get(slug=shop_slug)
        except Organization.DoesNotExist:
            return False
        org_user = OrganizationUser.objects.filter(organization=shop).values_list('user',flat=True)
        user = request.user.pk
        return user in org_user

class IsMerchant(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

 # Chreturn eck if the logged-in merchant is associated with the shop
        merchant = request.user.is_merchant
        print(merchant)
        return merchant


class IsAdminOrOwner(BasePermission):
    def has_permission(self, request, view):
        shop_slug = view.kwargs.get('shop_slug')
        shop = Organization.objects.get(slug=shop_slug)
        if not request.user.is_authenticated:
            return False
        user = request.user
        role = OrganizationUser.objects.get(user=user, organization=shop).role
        # role = org.role
        # print(role)
        return role==UserRole.OWNER or role==UserRole.ADMIN

class AdminOrAuthenticatedUserPermission(BasePermission):
    def has_permission(self, request, view):
        # Allow GET requests for authenticated users
        if request.method == 'GET' and request.user.is_authenticated:
            return True

        # Allow all methods for administrators
        if request.user.is_superuser:
            return True

        return False

class OwnerOrAdminPermission(BasePermission):
    def has_permission(self, request, view):
        shop_slug = view.kwargs.get('shop_slug')
        shop = Organization.objects.get(slug=shop_slug)
        if not request.user.is_authenticated:
            return False
        user = request.user
        role = OrganizationUser.objects.get(user=user, organization=shop).role
        if request.method == 'GET' and (role==UserRole.ADMIN or role==UserRole.STAFF):
            return True

        # Allow all methods for administrators
        if role==UserRole.OWNER:
            return True

        return False

class IsOwner(BasePermission):
    def has_permission(self, request, view):
        shop_slug = view.kwargs.get('shop_slug')
        shop = Organization.objects.get(slug=shop_slug)

        if not request.user.is_authenticated:
            return False

        user = request.user
        role = OrganizationUser.objects.get(user=user, organization=shop).role
        return role==UserRole.OWNER

# class AdminOrAuthenticatedUserPermission(BasePermission):
#     def has_permission(self, request, view):
#         shop_slug = view.kwargs.get('shop_slug')
#         shop = Organization.objects.get(slug=shop_slug)

#         if not request.user.is_authenticated:
#             return False

#         user = request.user
#         role = OrganizationUser.objects.get(user=user, organization=shop).role
#         # Allow GET requests for authenticated users
#         if request.method == 'GET' and role=UserRole.OWNER:
#             return True

#         # Allow all methods for administrators
#         if request.user.is_superuser:
#             return True

#         return False

class NotAuthenticated(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return True
