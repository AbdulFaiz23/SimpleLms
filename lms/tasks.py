from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import csv
import os
import time

@shared_task(bind=True, max_retries=3)
def send_enrollment_email(self, student_email, course_title):
    try:
        send_mail(
            subject=f"Enrollment Confirmation: {course_title}",
            message=f"Hello!\n\nYou have successfully enrolled in '{course_title}'. Happy learning!",
            from_email="noreply@simplelms.com",
            recipient_list=[student_email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)

@shared_task(bind=True, max_retries=3)
def generate_certificate(self, student_name, course_title):
    try:
        cert_dir = os.path.join(settings.BASE_DIR, 'media', 'certificates')
        os.makedirs(cert_dir, exist_ok=True)
        
        filename = f"{student_name.replace(' ', '_')}_{course_title.replace(' ', '_')}_certificate.txt"
        filepath = os.path.join(cert_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(f"CERTIFICATE OF COMPLETION\n\n")
            f.write(f"This is to certify that {student_name}\n")
            f.write(f"has successfully completed the course:\n")
            f.write(f"{course_title}\n")
            
        return filepath
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)

@shared_task
def update_course_statistics():
    from lms.models import Course, Enrollment
    from django.core.cache import cache
    
    courses = Course.objects.all()
    for course in courses:
        enrollment_count = Enrollment.objects.filter(course=course).count()
        # Save to Redis instead of PostgreSQL to avoid schema changes
        cache_key = f"course:stats:enrollments:{course.id}"
        cache.set(cache_key, enrollment_count, timeout=3600)

@shared_task(bind=True)
def export_course_report(self, course_id):
    from lms.models import Course, Enrollment, Progress
    
    try:
        course = Course.objects.get(id=course_id)
        enrollments = Enrollment.objects.filter(course=course).select_related('student')
        
        report_dir = os.path.join(settings.BASE_DIR, 'media', 'reports')
        os.makedirs(report_dir, exist_ok=True)
        
        filename = f"course_{course_id}_report_{int(time.time())}.csv"
        filepath = os.path.join(report_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Student Username', 'Student Email', 'Enrollment Date', 'Progress (%)'])
            
            total_lessons = course.lesson_set.count()
            
            for enrollment in enrollments:
                completed_lessons = Progress.objects.filter(
                    student=enrollment.student, 
                    lesson__course=enrollment.course, 
                    completed=True
                ).count()
                
                if total_lessons > 0:
                    pct = (completed_lessons / total_lessons) * 100
                else:
                    pct = 0.0
                
                writer.writerow([
                    enrollment.student.username,
                    enrollment.student.email,
                    enrollment.enrolled_at.strftime("%Y-%m-%d %H:%M:%S"),
                    f"{pct:.2f}"
                ])
                
        return filepath
    except Exception as exc:
        # We don't retry export, we just log it or fail
        raise exc
