from django.db import models
from datetime import date

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    image = models.ImageField(upload_to='faces/')

    def __str__(self):
        return self.name


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    time = models.TimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'date')