import jwt
import datetime
from django.conf import settings
from ninja.security import HttpBearer
from ninja.errors import HttpError
from lms.models import User
from functools import wraps

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.datetime.utcnow(),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.datetime.utcnow(),
        "type": "refresh",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HttpError(401, "Token has expired")
    except jwt.InvalidTokenError:
        raise HttpError(401, "Invalid token")


class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HttpError(401, "Invalid token type")
        try:
            user = User.objects.get(id=payload.get("user_id"))
            return user  # request.auth will be set to this user object by Django Ninja
        except User.DoesNotExist:
            raise HttpError(401, "User not found")


# RBAC Decorators
def is_admin(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if request.auth.role != 'admin':
            raise HttpError(403, "Admin access required")
        return func(request, *args, **kwargs)
    return wrapper


def is_instructor(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if request.auth.role not in ['admin', 'instructor']:
            raise HttpError(403, "Instructor access required")
        return func(request, *args, **kwargs)
    return wrapper


def is_student(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if request.auth.role != 'student':
            raise HttpError(403, "Student access required")
        return func(request, *args, **kwargs)
    return wrapper


def check_course_owner(request, course):
    if request.auth.role == 'admin':
        return True
    if request.auth.role == 'instructor' and course.instructor_id == request.auth.id:
        return True
    raise HttpError(403, "You don't own this course")
