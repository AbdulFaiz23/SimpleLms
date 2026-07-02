from django.test import TestCase, Client
from lms.models import User, Category, Course, Enrollment, Lesson, Progress
from lms.tasks import export_course_report
from lms.mongo import log_activity
from unittest.mock import patch, MagicMock
import os
import csv

class TasksAndFeaturesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.instructor = User.objects.create_user(username="instructor", password="pw", role="instructor")
        self.student = User.objects.create_user(username="student", password="pw", role="student")
        self.category = Category.objects.create(name="Programming")
        self.course = Course.objects.create(title="Python 101", instructor=self.instructor, category=self.category)
        self.lesson = Lesson.objects.create(title="Intro", course=self.course, order=1)
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        Progress.objects.create(student=self.student, lesson=self.lesson, completed=True)

    def test_export_course_report(self):
        """Test export_course_report jalan tanpa error dan CSV berisi data benar"""
        # Bug fix 1: export_course_report returns filepath directly, not a message string
        result = export_course_report(self.course.id)
        self.assertTrue(os.path.exists(result), f"Expected CSV file at {result}")

        # Verify CSV header and content — must match tasks.py exactly
        with open(result, newline='') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            # Header harus sama persis dengan yang ditulis tasks.py
            self.assertEqual(rows[0], ['Student Username', 'Student Email', 'Enrollment Date', 'Progress (%)'])
            # username column
            self.assertEqual(rows[1][0], 'student')
            # tasks.py menggunakan f"{pct:.2f}", jadi 100% → "100.00" bukan "100.0"
            self.assertEqual(rows[1][3], '100.00')

        # Clean up
        if os.path.exists(result):
            os.remove(result)

    def test_log_activity(self):
        """Test log_activity berhasil insert ke MongoDB"""
        mock_request = MagicMock()
        mock_request.META = {'REMOTE_ADDR': '127.0.0.1'}
        mock_request.headers = {'User-Agent': 'test-agent'}

        # Bug fix 3: db adalah variabel lokal yang dikembalikan get_mongo_db(),
        # jadi kita patch get_mongo_db() itu sendiri agar return mock.
        mock_db = MagicMock()
        with patch('lms.mongo.get_mongo_db', return_value=mock_db):
            log_activity(
                user=self.student,
                action="TEST_ACTION",
                resource_type="test",
                resource_id=1,
                request=mock_request
            )

        # Verifikasi insert_one dipanggil pada collection activity_logs
        mock_db.activity_logs.insert_one.assert_called_once()
        args, kwargs = mock_db.activity_logs.insert_one.call_args
        self.assertEqual(args[0]['action'], "TEST_ACTION")
        self.assertEqual(args[0]['user_id'], self.student.id)

    def test_rate_limit(self):
        """Test rate limit: request ke-61 dalam 1 menit return 429"""
        # Bug fix 2: middleware menggunakan cache.incr() dari django-cache,
        # bukan redis_client langsung. Patch cache.incr agar return 61 (over limit).
        with patch('django.core.cache.cache.incr', return_value=61):
            response = self.client.get("/api/courses")
        self.assertEqual(response.status_code, 429)
        # Pesan di middleware: "Rate limit exceeded, try again later" (tanpa titik)
        self.assertIn("Rate limit exceeded", response.json()["detail"])
