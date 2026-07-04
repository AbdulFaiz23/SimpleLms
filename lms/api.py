from ninja import NinjaAPI
from lms.api_auth import router as auth_router
from lms.api_courses import router as courses_router
from lms.api_enrollments import router as enrollments_router
from lms.api_reports import router as reports_router
from lms.api_tasks import router as tasks_router

api = NinjaAPI(
    title="Simple LMS API",
    version="1.0.0",
    description="REST API untuk Simple LMS menggunakan Django Ninja",
    docs_url="/docs",
)

api.add_router("/auth", auth_router, tags=["Authentication"])
api.add_router("/courses", courses_router, tags=["Courses"])
api.add_router("/enrollments", enrollments_router, tags=["Enrollments"])
api.add_router("/reports", reports_router, tags=["Reports"])
api.add_router("/tasks", tasks_router, tags=["Tasks"])