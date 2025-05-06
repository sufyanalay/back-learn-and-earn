from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import ResourceCategory, Resource, ResourceComment
from .serializers import ResourceCategorySerializer, ResourceSerializer, ResourceDetailSerializer, ResourceCommentSerializer
from users.permissions import IsTeacher, IsTechnician


class ResourceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResourceCategory.objects.all()
    serializer_class = ResourceCategorySerializer
    permission_classes = [permissions.AllowAny]


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category__name', 'subject__name']
    ordering_fields = ['created_at', 'view_count', 'title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ResourceDetailSerializer
        return ResourceSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), (IsTeacher() | IsTechnician())]
        return [permissions.AllowAny()]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Increment view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_resources = Resource.objects.filter(is_featured=True)
        serializer = self.get_serializer(featured_resources, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_subject(self, request):
        subject_id = request.query_params.get('subject_id')
        if not subject_id:
            return Response(
                {"error": "subject_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resources = Resource.objects.filter(subject_id=subject_id)
        serializer = self.get_serializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response(
                {"error": "category_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resources = Resource.objects.filter(category_id=category_id)
        serializer = self.get_serializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_resources(self, request):
        resources = Resource.objects.filter(author=request.user)
        serializer = self.get_serializer(resources, many=True)
        return Response(serializer.data)


class ResourceCommentCreateView(generics.CreateAPIView):
    queryset = ResourceComment.objects.all()
    serializer_class = ResourceCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        resource = get_object_or_404(
            Resource, 
            pk=self.kwargs.get('resource_id')
        )
        
        serializer.save(
            user=self.request.user,
            resource=resource
        )


class ResourceCommentListView(generics.ListAPIView):
    serializer_class = ResourceCommentSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return ResourceComment.objects.filter(
            resource_id=self.kwargs.get('resource_id')
        )