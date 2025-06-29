from django.db import models

# Create your models here.
class Task(models.Model):
    task_id = models.CharField(max_length=128, primary_key=True)
    task_name = models.CharField(max_length=128)
    task_type = models.CharField(max_length=128)
    task_related_id = models.CharField(max_length=128)
    task_config = models.JSONField()
    task_status = models.CharField(max_length=128)
    task_metadata = models.JSONField()
    task_progress = models.CharField(max_length=128)
    task_progress_msg = models.TextField()
    
    class Meta:
        db_table = 'tasks'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'