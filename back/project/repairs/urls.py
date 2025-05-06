from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.RepairCategoryViewSet)
router.register(r'requests', views.RepairRequestViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('requests/<int:repair_id>/updates/', views.RepairUpdateCreateView.as_view(), name='repair-update-create'),
]