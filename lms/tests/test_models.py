from django.test import TestCase
from django.db.utils import IntegrityError
from lms.models import User, Category, Course, Lesson, Enrollment, Progress

class ModelTests(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(username="instructor", password="pw", role="instructor")
        self.student = User.objects.create_user(username="student", password="pw", role="student")
        self.category = Category.objects.create(name="Programming")
        self.course = Course.objects.create(title="Python 101", instructor=self.instructor, category=self.category)
        
        self.lesson1 = Lesson.objects.create(title="Intro", course=self.course, order=1)
        self.lesson2 = Lesson.objects.create(title="Variables", course=self.course, order=2)
        
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        
    def test_course_lesson_set_count(self):
        """Test relasi Course.lesson_set menghitung jumlah lesson dengan benar"""
        self.assertEqual(self.course.lesson_set.count(), 2)

    def test_enrollment_unique_constraint(self):
        """Test Enrollment tidak bisa duplikat (unique constraint student+course)"""
        with self.assertRaises(IntegrityError):
            Enrollment.objects.create(student=self.student, course=self.course)

    def test_progress_completed_toggle(self):
        """Test Progress.completed toggle works"""
        progress, created = Progress.objects.get_or_create(student=self.student, lesson=self.lesson1)
        self.assertFalse(progress.completed)
        
        # Toggle
        progress.completed = True
        progress.save()
        
        progress.refresh_from_db()
        self.assertTrue(progress.completed)

    def test_course_completion_percentage(self):
        """Test logic persentase completion (mensimulasikan logic di API)"""
        # Create progress for lesson1
        Progress.objects.create(student=self.student, lesson=self.lesson1, completed=True)
        
        total_lessons = Lesson.objects.filter(course=self.course).count()
        completed_lessons = Progress.objects.filter(student=self.student, lesson__course=self.course, completed=True).count()
        
        pct = round((completed_lessons / total_lessons * 100) if total_lessons > 0 else 0, 1)
        self.assertEqual(pct, 50.0)
