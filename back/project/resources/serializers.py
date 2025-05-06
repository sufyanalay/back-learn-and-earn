from rest_framework import serializers
from .models import ResourceCategory, Resource, ResourceComment


class ResourceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceCategory
        fields = '__all__'


class ResourceCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    
    class Meta:
        model = ResourceComment
        fields = ('id', 'resource', 'user', 'user_name', 'user_role', 'content', 'created_at')
        read_only_fields = ('user', 'created_at')
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    
    def get_user_role(self, obj):
        return obj.user.role
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ResourceSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    subject_name = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Resource
        fields = (
            'id', 'title', 'description', 'resource_type', 'file', 'external_url',
            'thumbnail', 'author', 'author_name', 'category', 'category_name',
            'subject', 'subject_name', 'is_featured', 'view_count', 
            'created_at', 'updated_at', 'comment_count'
        )
        read_only_fields = ('author', 'is_featured', 'view_count', 'created_at', 'updated_at')
    
    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}"
    
    def get_category_name(self, obj):
        return obj.category.name
    
    def get_subject_name(self, obj):
        return obj.subject.name if obj.subject else None
    
    def get_comment_count(self, obj):
        return obj.comments.count()
    
    def validate(self, data):
        # Validate that either file or external_url is provided based on resource_type
        resource_type = data.get('resource_type')
        file = data.get('file')
        external_url = data.get('external_url')
        
        if resource_type in ['video', 'document', 'image'] and not file:
            raise serializers.ValidationError(f"File must be provided for {resource_type} resource type")
        
        if resource_type == 'link' and not external_url:
            raise serializers.ValidationError("External URL must be provided for link resource type")
        
        return data
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ResourceDetailSerializer(ResourceSerializer):
    comments = ResourceCommentSerializer(many=True, read_only=True)
    
    class Meta(ResourceSerializer.Meta):
        fields = ResourceSerializer.Meta.fields + ('comments',)