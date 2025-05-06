from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.ResourceCategoryViewSet)
router.register(r'resources', views.ResourceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('resources/<int:resource_id>/comments/', views.ResourceCommentListView.as_view(), name='resource-comment-list'),
    path('resources/<int:resource_id>/comments/create/', views.ResourceCommentCreateView.as_view(), name='resource-comment-create'),
]