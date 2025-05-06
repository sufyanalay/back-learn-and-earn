from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserRating

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'role')
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'profile_image', 'bio', 'date_joined')
        read_only_fields = ('id', 'email', 'date_joined')


class UserRatingSerializer(serializers.ModelSerializer):
    rater_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserRating
        fields = ('id', 'user', 'rater', 'rater_name', 'rating', 'review', 'created_at')
        read_only_fields = ('id', 'rater', 'created_at')
    
    def get_rater_name(self, obj):
        return obj.rater.name
    
    def validate(self, data):
        # Users cannot rate themselves
        if self.context['request'].user == data['user']:
            raise serializers.ValidationError("You cannot rate yourself")
        return data
    
    def create(self, validated_data):
        validated_data['rater'] = self.context['request'].user
        return super().create(validated_data)