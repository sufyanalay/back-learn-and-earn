from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/<str:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('ratings/create/', views.UserRatingCreateView.as_view(), name='user-rating-create'),
    path('ratings/<int:pk>/update/', views.UserRatingUpdateView.as_view(), name='user-rating-update'),
    path('ratings/user/<int:user_id>/', views.UserRatingsListView.as_view(), name='user-ratings-list'),
    path('earnings/', views.EarningsDashboardView.as_view(), name='earnings-dashboard'),
]