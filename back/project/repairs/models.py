from django.db import models
from django.conf import settings


class RepairCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class RepairRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='repair_requests'
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        related_name='repair_assignments',
        null=True, 
        blank=True
    )
    category = models.ForeignKey(
        RepairCategory, 
        on_delete=models.CASCADE, 
        related_name='repair_requests'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    device_make = models.CharField(max_length=100)
    device_model = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.student.email}"


class RepairImage(models.Model):
    repair_request = models.ForeignKey(
        RepairRequest, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='repair_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.repair_request.title}"


class RepairUpdate(models.Model):
    repair_request = models.ForeignKey(
        RepairRequest, 
        on_delete=models.CASCADE, 
        related_name='updates'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Update on {self.repair_request.title} by {self.user.email}"