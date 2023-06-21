
from django.contrib import admin
from django.urls import path,include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin', admin.site.urls),
    path('api-auth', include('rest_framework.urls')),
    path('api/v1',include('merchant.urls')),
    path('__debug__/', include("debug_toolbar.urls")),
    path('api/schema',SpectacularAPIView.as_view(), name = 'api-schema'),
    path('', SpectacularSwaggerView.as_view(url_name = 'api-schema'), name = 'api-docs'),
    path('api/token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
]
