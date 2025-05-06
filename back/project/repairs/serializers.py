from rest_framework import serializers
from .models import RepairCategory, RepairRequest, RepairImage, RepairUpdate


class RepairCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairCategory
        fields = '__all__'


class RepairImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairImage
        fields = ('id', 'image', 'uploaded_at')


class RepairUpdateSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    
    class Meta:
        model = RepairUpdate
        fields = ('id', 'repair_request', 'user', 'user_name', 'user_role', 'message', 'created_at')
        read_only_fields = ('user', 'created_at')
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    
    def get_user_role(self, obj):
        return obj.user.role
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RepairRequestSerializer(serializers.ModelSerializer):
    images = RepairImageSerializer(many=True, read_only=True)
    student_name = serializers.SerializerMethodField()
    technician_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = RepairRequest
        fields = (
            'id', 'student', 'student_name', 'technician', 'technician_name',
            'category', 'category_name', 'title', 'description', 'device_make',
            'device_model', 'status', 'service_fee', 'created_at', 'updated_at',
            'images', 'uploaded_images'
        )
        read_only_fields = ('student', 'technician', 'service_fee', 'created_at', 'updated_at')
    
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}" if obj.student else None
    
    def get_technician_name(self, obj):
        return f"{obj.technician.first_name} {obj.technician.last_name}" if obj.technician else None
    
    def get_category_name(self, obj):
        return obj.category.name
    
    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        validated_data['student'] = self.context['request'].user
        repair_request = super().create(validated_data)
        
        for image in uploaded_images:
            RepairImage.objects.create(repair_request=repair_request, image=image)
        
        return repair_request


class RepairRequestDetailSerializer(RepairRequestSerializer):
    updates = RepairUpdateSerializer(many=True, read_only=True)
    
    class Meta(RepairRequestSerializer.Meta):
        fields = RepairRequestSerializer.Meta.fields + ('updates',)