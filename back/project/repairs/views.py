from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import RepairCategory, RepairRequest, RepairImage, RepairUpdate
from .serializers import (
    RepairCategorySerializer, 
    RepairRequestSerializer, 
    RepairRequestDetailSerializer,
    RepairImageSerializer,
    RepairUpdateSerializer
)
from users.permissions import IsTechnician


class RepairCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RepairCategory.objects.all()
    serializer_class = RepairCategorySerializer
    permission_classes = [permissions.AllowAny]


class RepairRequestViewSet(viewsets.ModelViewSet):
    queryset = RepairRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RepairRequestDetailSerializer
        return RepairRequestSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Students can only see their own repair requests
        if user.role == 'student':
            return RepairRequest.objects.filter(student=user)
        
        # Technicians can see repairs assigned to them and unassigned requests
        elif user.role == 'technician':
            return RepairRequest.objects.filter(technician=user) | RepairRequest.objects.filter(technician__isnull=True, status='pending')
        
        # Admins can see all repair requests
        return RepairRequest.objects.all()
    
    @action(detail=True, methods=['post'])
    def add_images(self, request, pk=None):
        repair_request = self.get_object()
        
        # Ensure only the student who created the request can add images
        if repair_request.student != request.user:
            return Response(
                {"error": "You don't have permission to add images to this repair request"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        images = request.FILES.getlist('images')
        image_instances = []
        
        for image in images:
            image_instance = RepairImage.objects.create(
                repair_request=repair_request,
                image=image
            )
            image_instances.append(image_instance)
        
        serializer = RepairImageSerializer(image_instances, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsTechnician])
    def assign_technician(self, request, pk=None):
        repair_request = self.get_object()
        
        if repair_request.technician:
            return Response(
                {"error": "This repair request is already assigned to a technician"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        repair_request.technician = request.user
        repair_request.status = 'assigned'
        repair_request.save()
        
        # Create an update to notify about assignment
        RepairUpdate.objects.create(
            repair_request=repair_request,
            user=request.user,
            message=f"Technician {request.user.first_name} {request.user.last_name} has been assigned to this repair request"
        )
        
        serializer = self.get_serializer(repair_request)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        repair_request = self.get_object()
        status_value = request.data.get('status')
        
        if not status_value:
            return Response(
                {"error": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status transition
        valid_transitions = {
            'pending': ['assigned', 'cancelled'],
            'assigned': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': []
        }
        
        if status_value not in valid_transitions[repair_request.status]:
            return Response(
                {"error": f"Invalid status transition from {repair_request.status} to {status_value}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure only technician assigned can update status (except cancellation)
        if status_value != 'cancelled' and repair_request.technician != request.user:
            return Response(
                {"error": "Only the assigned technician can update this repair request status"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # For cancellation, ensure it's either the student or assigned technician
        if status_value == 'cancelled' and request.user != repair_request.student and request.user != repair_request.technician:
            return Response(
                {"error": "Only the student or assigned technician can cancel this repair request"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        repair_request.status = status_value
        
        # Set service fee if completing the repair
        if status_value == 'completed':
            service_fee = request.data.get('service_fee')
            if service_fee:
                repair_request.service_fee = service_fee
        
        repair_request.save()
        
        # Create status update
        message = f"Status updated to {status_value}"
        if status_value == 'completed' and repair_request.service_fee > 0:
            message += f" with a service fee of ${repair_request.service_fee}"
        
        RepairUpdate.objects.create(
            repair_request=repair_request,
            user=request.user,
            message=message
        )
        
        serializer = self.get_serializer(repair_request)
        return Response(serializer.data)


class RepairUpdateCreateView(generics.CreateAPIView):
    queryset = RepairUpdate.objects.all()
    serializer_class = RepairUpdateSerializer
    
    def perform_create(self, serializer):
        repair_request = get_object_or_404(
            RepairRequest, 
            pk=self.kwargs.get('repair_id')
        )
        
        # Ensure only the student who created the request or the assigned technician can add updates
        if (repair_request.student != self.request.user and 
            repair_request.technician != self.request.user):
            self.permission_denied(
                self.request, 
                message="You don't have permission to add updates to this repair request"
            )
        
        serializer.save(
            user=self.request.user,
            repair_request=repair_request
        )