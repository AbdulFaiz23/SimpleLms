from django.core.management.base import BaseCommand
from lms.models import User, Category, Course, Lesson, Enrollment, Progress
import random

class Command(BaseCommand):
    help = 'Seed database with demo data (1 admin, 2 instructors, 4 students, courses, enrollments, and progress)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting demo data seed...")
        
        # 1. Create Users
        password = "password123"
        admin, _ = User.objects.get_or_create(username="admin_demo", defaults={"email": "admin@demo.com", "role": "admin"})
        admin.set_password(password)
        admin.save()
        
        instructors = []
        for i in range(1, 3):
            inst, _ = User.objects.get_or_create(username=f"instructor_{i}", defaults={"email": f"inst{i}@demo.com", "role": "instructor"})
            inst.set_password(password)
            inst.save()
            instructors.append(inst)
            
        students = []
        for i in range(1, 5):
            student, _ = User.objects.get_or_create(username=f"student_{i}", defaults={"email": f"student{i}@demo.com", "role": "student"})
            student.set_password(password)
            student.save()
            students.append(student)

        self.stdout.write("Users created.")
            
        # 2. Categories
        cat_programming, _ = Category.objects.get_or_create(name="Programming")
        cat_design, _ = Category.objects.get_or_create(name="Design")
        
        # 3. Courses & Lessons
        courses_data = [
            {"title": "Python for Beginners", "inst": instructors[0], "cat": cat_programming, "lessons": ["Setup", "Variables", "Loops", "Functions", "OOP"]},
            {"title": "Advanced Django", "inst": instructors[0], "cat": cat_programming, "lessons": ["ORM", "Middleware", "Celery", "Testing"]},
            {"title": "UI/UX Principles", "inst": instructors[1], "cat": cat_design, "lessons": ["Color Theory", "Typography", "Figma Basics", "Prototyping"]},
            {"title": "React Native Masterclass", "inst": instructors[1], "cat": cat_programming, "lessons": ["Components", "Hooks", "Navigation", "State Management"]}
        ]
        
        created_courses = []
        for data in courses_data:
            course, _ = Course.objects.get_or_create(
                title=data["title"], 
                defaults={"instructor": data["inst"], "category": data["cat"]}
            )
            created_courses.append(course)
            
            # Lessons
            for idx, lesson_title in enumerate(data["lessons"], start=1):
                Lesson.objects.get_or_create(title=lesson_title, course=course, defaults={"order": idx})

        self.stdout.write("Courses and Lessons created.")
                
        # 4. Enrollments & Progress
        # Let's enroll students in some courses and mark progress
        for student in students:
            # Randomly enroll in 2-3 courses
            enrolled_courses = random.sample(created_courses, k=random.randint(2, 3))
            for course in enrolled_courses:
                enrollment, _ = Enrollment.objects.get_or_create(student=student, course=course)
                
                # Mark random progress
                lessons = list(course.lesson_set.all())
                
                # Selesaikan sebagian atau seluruh lesson (untuk ngasih variasi data ke analytics)
                num_completed = random.randint(1, len(lessons))
                for i in range(num_completed):
                    # Kita juga harus manggil update_learning_analytics & log_activity biar datanya masuk Mongo?
                    # Since this is a management command and we bypass API, we might want to manually insert to Mongo
                    # But for simple seeding, let's just create DB records. Or manually call API methods if we want Mongo data.
                    # We will simulate Mongo data manually so the reports look good.
                    progress, _ = Progress.objects.get_or_create(student=student, lesson=lessons[i])
                    progress.completed = True
                    progress.save()
                    
                # Helper untuk masukin dummy analytics jika dibutuhkan. 
                # (Di project ini update_learning_analytics dipanggil di mark_progress API)
                from lms.mongo import update_learning_analytics
                update_learning_analytics(student.id, course.id, len(lessons), num_completed)

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
        self.stdout.write("Test Credentials (Password for all: password123)")
        self.stdout.write("- Admin: admin_demo")
        self.stdout.write("- Instructors: instructor_1, instructor_2")
        self.stdout.write("- Students: student_1, student_2, student_3, student_4")
