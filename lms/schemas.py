from ninja import Schema
from pydantic import field_validator
from typing import Optional, List
from datetime import datetime


class CategorySchema(Schema):
    id: int
    name: str
    parent_id: Optional[int] = None


class UserOutSchema(Schema):
    id: int
    username: str
    email: str
    role: str


class RegisterSchema(Schema):
    username: str
    email: str
    password: str
    role: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ['student', 'instructor']:
            raise ValueError("Role must be 'student' or 'instructor'")
        return v


class LoginSchema(Schema):
    username: str
    password: str


class TokenSchema(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshSchema(Schema):
    refresh_token: str


class UserProfileSchema(Schema):
    id: int
    username: str
    email: str
    role: str


class UserUpdateSchema(Schema):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class LessonOutSchema(Schema):
    id: int
    title: str
    order: int


class CourseCreateSchema(Schema):
    title: str
    category_id: int


class CourseUpdateSchema(Schema):
    title: Optional[str] = None
    category_id: Optional[int] = None


class CourseListSchema(Schema):
    id: int
    title: str
    instructor: UserOutSchema
    category: CategorySchema
    total_lessons: int


class CourseDetailSchema(Schema):
    id: int
    title: str
    instructor: UserOutSchema
    category: CategorySchema
    lessons: List[LessonOutSchema]


class PaginatedCoursesSchema(Schema):
    total: int
    page: int
    page_size: int
    results: List[CourseListSchema]


class EnrollSchema(Schema):
    course_id: int


class ProgressUpdateSchema(Schema):
    lesson_id: int
    completed: bool = True


class ProgressOutSchema(Schema):
    lesson_id: int
    lesson_title: str
    completed: bool


class EnrolledCourseSchema(Schema):
    enrollment_id: int
    course: CourseListSchema
    enrolled_at: datetime
    progress: List[ProgressOutSchema]


class MessageSchema(Schema):
    message: str

class LessonCreateSchema(Schema):
    title: str
    order: int

class LessonOutSchema(Schema):
    id: int
    title: str
    order: int
