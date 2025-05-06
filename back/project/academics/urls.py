from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'subjects', views.SubjectViewSet)
router.register(r'questions', views.AcademicQuestionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('questions/<int:question_id>/responses/', views.QuestionResponseCreateView.as_view(), name='question-response-create'),
]