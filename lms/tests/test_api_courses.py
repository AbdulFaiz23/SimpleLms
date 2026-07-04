from django.test import TestCase, Client
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.core.cache import cache
from lms.models import User, Category, Course
import json
from unittest.mock import patch

class CoursesAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.instructor = User.objects.create_user(username="instructor", password="pw", role="instructor")
        self.student = User.objects.create_user(username="student", password="pw", role="student")
        
        # Get tokens
        resp = self.client.post("/api/auth/login", json.dumps({"username": "instructor", "password": "pw"}), content_type="application/json")
        self.instructor_token = resp.json()["access_token"]
        
        resp = self.client.post("/api/auth/login", json.dumps({"username": "student", "password": "pw"}), content_type="application/json")
        self.student_token = resp.json()["access_token"]
        
        self.category = Category.objects.create(name="Programming")
        self.course = Course.objects.create(title="Python 101", instructor=self.instructor, category=self.category)
        
        cache.clear()

    def test_list_courses(self):
        """Test GET /api/courses return list dengan benar"""
        response = self.client.get("/api/courses")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 1)
        self.assertEqual(response.json()["results"][0]["title"], "Python 101")

    def test_get_course_detail(self):
        """Test GET /api/courses/{id} return detail dengan benar"""
        response = self.client.get(f"/api/courses/{self.course.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Python 101")

    @patch('lms.api_courses.log_activity')
    def test_create_course_instructor(self, mock_log):
        """Test create course oleh instructor berhasil"""
        data = {
            "title": "New Course",
            "category_id": self.category.id
        }
        response = self.client.post("/api/courses", json.dumps(data), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.instructor_token}")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["title"], "New Course")

    @patch('lms.api_courses.log_activity')
    def test_create_course_student_rejected(self, mock_log):
        """Test create course oleh student ditolak (403)"""
        data = {
            "title": "Student Course",
            "category_id": self.category.id
        }
        response = self.client.post("/api/courses", json.dumps(data), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        self.assertEqual(response.status_code, 403)

    def test_course_caching(self):
        """Test cache: request kedua tidak query ulang ke DB"""
        # First request
        with CaptureQueriesContext(connection) as ctx1:
            response1 = self.client.get(f"/api/courses/{self.course.id}")
        
        self.assertEqual(response1.status_code, 200)
        queries1 = len(ctx1.captured_queries)
        self.assertGreater(queries1, 0)
        
        # Second request (should hit cache)
        with CaptureQueriesContext(connection) as ctx2:
            response2 = self.client.get(f"/api/courses/{self.course.id}")
            
        self.assertEqual(response2.status_code, 200)
        queries2 = len(ctx2.captured_queries)
        self.assertEqual(queries2, 0)  # No DB queries should be made if cache is hit
