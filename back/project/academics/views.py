from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import (
    Subject, 
    AcademicQuestion, 
    QuestionAttachment,
    QuestionResponse,
    ResponseAttachment
)
from .serializers import (
    SubjectSerializer,
    AcademicQuestionSerializer,
    AcademicQuestionDetailSerializer,
    QuestionAttachmentSerializer,
    QuestionResponseSerializer
)
from users.permissions import IsTeacher


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.AllowAny]


class AcademicQuestionViewSet(viewsets.ModelViewSet):
    queryset = AcademicQuestion.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AcademicQuestionDetailSerializer
        return AcademicQuestionSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Students can only see their own questions
        if user.role == 'student':
            return AcademicQuestion.objects.filter(student=user)
        
        # Teachers can see questions assigned to them and unassigned questions
        elif user.role == 'teacher':
            return AcademicQuestion.objects.filter(teacher=user) | AcademicQuestion.objects.filter(teacher__isnull=True, status='pending')
        
        # Admins can see all questions
        return AcademicQuestion.objects.all()
    
    @action(detail=True, methods=['post'])
    def add_attachments(self, request, pk=None):
        question = self.get_object()
        
        # Ensure only the student who created the question can add attachments
        if question.student != request.user:
            return Response(
                {"error": "You don't have permission to add attachments to this question"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        files = request.FILES.getlist('files')
        attachment_instances = []
        
        for file in files:
            attachment_instance = QuestionAttachment.objects.create(
                question=question,
                file=file
            )
            attachment_instances.append(attachment_instance)
        
        serializer = QuestionAttachmentSerializer(attachment_instances, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsTeacher])
    def assign_teacher(self, request, pk=None):
        question = self.get_object()
        
        if question.teacher:
            return Response(
                {"error": "This question is already assigned to a teacher"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        question.teacher = request.user
        question.status = 'assigned'
        question.save()
        
        # Create a response to notify about assignment
        QuestionResponse.objects.create(
            question=question,
            user=request.user,
            content=f"Teacher {request.user.first_name} {request.user.last_name} has been assigned to answer this question"
        )
        
        serializer = self.get_serializer(question)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        question = self.get_object()
        status_value = request.data.get('status')
        
        if not status_value:
            return Response(
                {"error": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status transition
        valid_transitions = {
            'pending': ['assigned', 'closed'],
            'assigned': ['answered', 'closed'],
            'answered': ['closed'],
            'closed': []
        }
        
        if status_value not in valid_transitions[question.status]:
            return Response(
                {"error": f"Invalid status transition from {question.status} to {status_value}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure only teacher assigned can update status (except closing)
        if status_value != 'closed' and question.teacher != request.user:
            return Response(
                {"error": "Only the assigned teacher can update this question status"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # For closing, ensure it's either the student or assigned teacher
        if status_value == 'closed' and request.user != question.student and request.user != question.teacher:
            return Response(
                {"error": "Only the student or assigned teacher can close this question"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        question.status = status_value
        
        # Set service fee if answering the question
        if status_value == 'answered':
            service_fee = request.data.get('service_fee')
            if service_fee:
                question.service_fee = service_fee
        
        question.save()
        
        # Create status notification
        message = f"Status updated to {status_value}"
        if status_value == 'answered' and question.service_fee > 0:
            message += f" with a service fee of ${question.service_fee}"
        
        QuestionResponse.objects.create(
            question=question,
            user=request.user,
            content=message
        )
        
        serializer = self.get_serializer(question)
        return Response(serializer.data)


class QuestionResponseCreateView(generics.CreateAPIView):
    queryset = QuestionResponse.objects.all()
    serializer_class = QuestionResponseSerializer
    
    def perform_create(self, serializer):
        question = get_object_or_404(
            AcademicQuestion, 
            pk=self.kwargs.get('question_id')
        )
        
        # Ensure only the student who created the question or the assigned teacher can add responses
        if (question.student != self.request.user and 
            question.teacher != self.request.user):
            self.permission_denied(
                self.request, 
                message="You don't have permission to add responses to this question"
            )
        
        serializer.save(
            user=self.request.user,
            question=question
        )