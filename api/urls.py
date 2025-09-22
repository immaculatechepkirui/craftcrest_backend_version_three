from django.urls import path, include
from django.conf import settings

from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, LoginView, ForgotPasswordView,OTPVerificationView, PasswordResetView,AdminListUsersView, 
    UserViewSet, ArtisanPortfolioViewSet, UserProfileView,NearbyArtisansView, UserViewSet,OrderViewSet, RatingViewSet,
    OrderStatusViewSet, CustomDesignRequestViewSet,ShoppingCartViewSet,InventoryViewSet,ItemViewSet,PaymentViewSet, daraja_callback,
    STKPushView,
    B2CPaymentView,

)
from django.conf.urls.static import static


router = DefaultRouter()

router.register(r'carts', ShoppingCartViewSet, basename='cart')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'items', ItemViewSet, basename='item')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'trackings', OrderStatusViewSet, basename='orderstatus')
router.register(r'custom-requests', CustomDesignRequestViewSet, basename='customdesignrequest')
router.register(r'users', UserViewSet)
router.register(r'portfolio', ArtisanPortfolioViewSet, basename='portfolio')
router.register(r'payments', PaymentViewSet, basename='payments')



urlpatterns = [
    path('', include(router.urls)),
    path('daraja/stk-push/', STKPushView.as_view(), name='daraja-stk-push'),
    path('daraja/callback/', daraja_callback, name='daraja-callback'),
    path('daraja/b2c-payment/', B2CPaymentView.as_view(), name='daraja-b2c-payment'),
    path('nearby-artisans/', NearbyArtisansView.as_view(), name='nearby-artisans'), 
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-otp/', OTPVerificationView.as_view(), name='verify-otp'),
    path('reset-password/', PasswordResetView.as_view(), name='reset-password'),
    path('admin/users/', AdminListUsersView.as_view(), name='admin-list-users'),
    path('profile/',UserProfileView.as_view(), name = 'user-profile')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


