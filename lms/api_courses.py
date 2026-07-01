from ninja import Router, Query
from ninja.errors import HttpError
from typing import Optional
from lms.models import Course, Category, User
from lms.schemas import (
    CourseCreateSchema, CourseUpdateSchema,
    CourseDetailSchema, PaginatedCoursesSchema, MessageSchema
)
from lms.auth import JWTAuth, is_instructor, is_admin, check_course_owner
from django.core.cache import cache
from lms.mongo import log_activity
from lms.tasks import export_course_report
from django.shortcuts import get_object_or_404

router = Router(tags=["Courses"])

def invalidate_course_cache(course_id=None):
    if course_id:
        cache.delete(f"course:detail:{course_id}")
    
    # Delete list caches by scanning for pattern
    import redis
    from django.conf import settings
    # We can connect directly to redis to scan, or use django-redis keys if supported
    # django-redis iter_keys
    try:
        keys = cache.iter_keys("courses:list:*")
        for key in keys:
            cache.delete(key.decode('utf-8') if isinstance(key, bytes) else key)
    except NotImplementedError:
        cache.clear() # fallback if iter_keys not supported
    except Exception:
        pass



def serialize_detail(course):
    return {
        "id": course.id,
        "title": course.title,
        "instructor": {
            "id": course.instructor.id,
            "username": course.instructor.username,
            "email": course.instructor.email,
            "role": course.instructor.role,
        },
        "category": {
            "id": course.category.id,
            "name": course.category.name,
            "parent_id": course.category.parent_id,
        },
        "lessons": [
            {"id": l.id, "title": l.title, "order": l.order}
            for l in course.lesson_set.all()
        ],
    }


@router.get("", response=PaginatedCoursesSchema)
def list_courses(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
):
    """List all courses dengan pagination dan filter."""
    cache_key = f"courses:list:{page}:{page_size}:{category_id or ''}:{search or ''}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    qs = Course.objects.for_listing()
    if category_id:
        qs = qs.filter(category_id=category_id)
    if search:
        qs = qs.filter(title__icontains=search)
    total = qs.count()
    courses = qs[(page - 1) * page_size: page * page_size]
    
    response_data = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": [
            {
                "id": c.id,
                "title": c.title,
                "instructor": {
                    "id": c.instructor.id,
                    "username": c.instructor.username,
                    "email": c.instructor.email,
                    "role": c.instructor.role,
                },
                "category": {
                    "id": c.category.id,
                    "name": c.category.name,
                    "parent_id": c.category.parent_id,
                },
                "total_lessons": c.total_lessons,
            }
            for c in courses
        ],
    }
    cache.set(cache_key, response_data, timeout=300) # 5 minutes
    return response_data


@router.get("/{course_id}", response=CourseDetailSchema)
def get_course(request, course_id: int):
    """Get detail sebuah course."""
    cache_key = f"course:detail:{course_id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
        
    try:
        course = (
            Course.objects
            .select_related("instructor", "category")
            .prefetch_related("lesson_set")
            .get(id=course_id)
        )
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
        
    response_data = serialize_detail(course)
    cache.set(cache_key, response_data, timeout=300)
    return response_data


@router.post("", response={201: CourseDetailSchema}, auth=JWTAuth())
@is_instructor
def create_course(request, payload: CourseCreateSchema):
    """Buat course baru."""
    instructor = request.auth
    try:
        category = Category.objects.get(id=payload.category_id)
    except Category.DoesNotExist:
        raise HttpError(404, "Category not found")
    course = Course.objects.create(
        title=payload.title,
        instructor=instructor,
        category=category,
    )
    course = (
        Course.objects
        .select_related("instructor", "category")
        .prefetch_related("lesson_set")
        .get(id=course.id)
    )
    
    log_activity(
        user=instructor,
        action="COURSE_CREATED",
        resource_type="course",
        resource_id=course.id,
        metadata={"title": course.title},
        request=request
    )
    invalidate_course_cache()
    
    return 201, serialize_detail(course)


@router.patch("/{course_id}", response=CourseDetailSchema, auth=JWTAuth())
def update_course(request, course_id: int, payload: CourseUpdateSchema):
    """Update course."""
    try:
        course = (
            Course.objects
            .select_related("instructor", "category")
            .prefetch_related("lesson_set")
            .get(id=course_id)
        )
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")

    check_course_owner(request, course)

    if payload.title is not None:
        course.title = payload.title
    if payload.category_id is not None:
        try:
            course.category = Category.objects.get(id=payload.category_id)
        except Category.DoesNotExist:
            raise HttpError(404, "Category not found")
    course.save()
    
    log_activity(
        user=request.auth,
        action="COURSE_UPDATED",
        resource_type="course",
        resource_id=course.id,
        metadata={"title": course.title},
        request=request
    )
    invalidate_course_cache(course.id)
    
    return serialize_detail(course)


@router.delete("/{course_id}", response=MessageSchema, auth=JWTAuth())
@is_admin
def delete_course(request, course_id: int):
    """Hapus course."""
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    title = course.title
    course.delete()
    
    log_activity(
        user=request.auth,
        action="COURSE_DELETED",
        resource_type="course",
        resource_id=course_id,
        metadata={"title": title},
        request=request
    )
    invalidate_course_cache(course_id)
    
    return {"message": f"Course '{title}' deleted successfully"}


@router.post("/{course_id}/export-report", auth=JWTAuth())
def export_report(request, course_id: int):
    """
    Triggers an async task to generate a course report.
    Accessible to admins and instructors (who own the course).
    """
    if request.auth.role not in ['admin', 'instructor']:
        return 403, {"detail": "Admin or Instructor access required"}

    course = get_object_or_404(Course, id=course_id)
    
    if request.auth.role == 'instructor' and course.instructor != request.auth:
        return 403, {"detail": "You don't own this course"}

    # Trigger async task
    task = export_course_report.delay(course.id)
    
    # Return 202 Accepted immediately
    return 202, {"task_id": task.id, "message": "Report generation started"}