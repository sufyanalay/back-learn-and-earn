from rest_framework import serializers
from .models import (
    Subject, 
    AcademicQuestion, 
    QuestionAttachment,
    QuestionResponse,
    ResponseAttachment
)


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class QuestionAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAttachment
        fields = ('id', 'file', 'uploaded_at')


class ResponseAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseAttachment
        fields = ('id', 'file', 'uploaded_at')


class QuestionResponseSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    attachments = ResponseAttachmentSerializer(many=True, read_only=True)
    uploaded_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = QuestionResponse
        fields = ('id', 'question', 'user', 'user_name', 'user_role', 'content', 'created_at', 'attachments', 'uploaded_files')
        read_only_fields = ('user', 'created_at')
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    
    def get_user_role(self, obj):
        return obj.user.role
    
    def create(self, validated_data):
        uploaded_files = validated_data.pop('uploaded_files', [])
        validated_data['user'] = self.context['request'].user
        response = super().create(validated_data)
        
        for file in uploaded_files:
            ResponseAttachment.objects.create(response=response, file=file)
        
        return response


class AcademicQuestionSerializer(serializers.ModelSerializer):
    attachments = QuestionAttachmentSerializer(many=True, read_only=True)
    student_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    subject_name = serializers.SerializerMethodField()
    uploaded_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = AcademicQuestion
        fields = (
            'id', 'student', 'student_name', 'teacher', 'teacher_name',
            'subject', 'subject_name', 'title', 'content', 'status',
            'service_fee', 'created_at', 'updated_at', 'attachments',
            'uploaded_files'
        )
        read_only_fields = ('student', 'teacher', 'service_fee', 'created_at', 'updated_at')
    
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}" if obj.student else None
    
    def get_teacher_name(self, obj):
        return f"{obj.teacher.first_name} {obj.teacher.last_name}" if obj.teacher else None
    
    def get_subject_name(self, obj):
        return obj.subject.name
    
    def create(self, validated_data):
        uploaded_files = validated_data.pop('uploaded_files', [])
        validated_data['student'] = self.context['request'].user
        question = super().create(validated_data)
        
        for file in uploaded_files:
            QuestionAttachment.objects.create(question=question, file=file)
        
        return question


class AcademicQuestionDetailSerializer(AcademicQuestionSerializer):
    responses = QuestionResponseSerializer(many=True, read_only=True)
    
    class Meta(AcademicQuestionSerializer.Meta):
        fields = AcademicQuestionSerializer.Meta.fields + ('responses',)