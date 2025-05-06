from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, UserDetailSerializer, UserRatingSerializer
from .models import UserRating
from .permissions import IsUserOrReadOnly, IsRater

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsUserOrReadOnly]
    
    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()


class UserRatingCreateView(generics.CreateAPIView):
    queryset = UserRating.objects.all()
    serializer_class = UserRatingSerializer
    
    def perform_create(self, serializer):
        serializer.save(rater=self.request.user)


class UserRatingUpdateView(generics.UpdateAPIView):
    queryset = UserRating.objects.all()
    serializer_class = UserRatingSerializer
    permission_classes = [IsRater]


class UserRatingsListView(generics.ListAPIView):
    serializer_class = UserRatingSerializer
    
    def get_queryset(self):
        return UserRating.objects.filter(user_id=self.kwargs['user_id'])


class EarningsDashboardView(APIView):
    def get(self, request):
        user = request.user
        
        if user.role not in ['teacher', 'technician']:
            return Response(
                {"error": "Only teachers and technicians can access earnings dashboard"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # For technicians, calculate earnings from repair services
        if user.role == 'technician':
            from repairs.models import RepairRequest
            completed_repairs = RepairRequest.objects.filter(
                technician=user, 
                status='completed'
            )
            
            earnings = sum(repair.service_fee for repair in completed_repairs)
            completed_services = completed_repairs.count()
        
        # For teachers, calculate earnings from academic services
        elif user.role == 'teacher':
            from academics.models import AcademicQuestion
            completed_questions = AcademicQuestion.objects.filter(
                teacher=user, 
                status='answered'
            )
            
            earnings = sum(question.service_fee for question in completed_questions)
            completed_services = completed_questions.count()
        
        return Response({
            'total_earnings': earnings,
            'completed_services': completed_services
        })