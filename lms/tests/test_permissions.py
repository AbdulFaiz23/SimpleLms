from django.test import TestCase, Client
from lms.models import User, Category, Course
import json
from unittest.mock import patch

class PermissionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username="admin", password="pw", role="admin")
        self.instructor1 = User.objects.create_user(username="instructor1", password="pw", role="instructor")
        self.instructor2 = User.objects.create_user(username="instructor2", password="pw", role="instructor")
        self.student = User.objects.create_user(username="student", password="pw", role="student")
        
        # Get tokens
        self.admin_token = self.client.post("/api/auth/login", json.dumps({"username": "admin", "password": "pw"}), content_type="application/json").json()["token"]
        self.instructor1_token = self.client.post("/api/auth/login", json.dumps({"username": "instructor1", "password": "pw"}), content_type="application/json").json()["token"]
        self.instructor2_token = self.client.post("/api/auth/login", json.dumps({"username": "instructor2", "password": "pw"}), content_type="application/json").json()["token"]
        self.student_token = self.client.post("/api/auth/login", json.dumps({"username": "student", "password": "pw"}), content_type="application/json").json()["token"]
        
        self.category = Category.objects.create(name="Programming")
        self.course1 = Course.objects.create(title="Course 1", instructor=self.instructor1, category=self.category)

    @patch('lms.api_courses.log_activity')
    @patch('lms.api_courses.invalidate_course_cache')
    def test_admin_access_admin_only_endpoint(self, mock_cache, mock_log):
        """Test admin bisa akses endpoint admin-only (DELETE course)"""
        response = self.client.delete(f"/api/courses/{self.course1.id}", HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        self.assertEqual(response.status_code, 200)

    @patch('lms.api_courses.log_activity')
    @patch('lms.api_courses.invalidate_course_cache')
    def test_instructor_update_own_course(self, mock_cache, mock_log):
        """Test instructor bisa update course miliknya sendiri"""
        data = {"title": "Updated Course"}
        response = self.client.patch(f"/api/courses/{self.course1.id}", json.dumps(data), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.instructor1_token}")
        self.assertEqual(response.status_code, 200)

    def test_instructor_update_other_course(self):
        """Test instructor tidak bisa update course milik instructor lain"""
        data = {"title": "Hacked Course"}
        response = self.client.patch(f"/api/courses/{self.course1.id}", json.dumps(data), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.instructor2_token}")
        self.assertEqual(response.status_code, 403)

    def test_student_rejected_from_instructor_admin_endpoints(self):
        """Test student ditolak dari endpoint instructor/admin-only"""
        data = {"title": "Student Try"}
        # Create course (instructor)
        response1 = self.client.post("/api/courses", json.dumps(data), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        self.assertEqual(response1.status_code, 403)
        # Delete course (admin)
        response2 = self.client.delete(f"/api/courses/{self.course1.id}", HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        self.assertEqual(response2.status_code, 403)

    def test_anonymous_rejected(self):
        """Test anonymous user ditolak dari semua endpoint yang butuh auth"""
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)
        
        response2 = self.client.post("/api/courses", json.dumps({"title": "X"}), content_type="application/json")
        self.assertEqual(response2.status_code, 401)
