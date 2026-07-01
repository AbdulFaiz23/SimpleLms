from ninja import Router
from celery.result import AsyncResult
from lms.auth import JWTAuth

router = Router()

@router.get("/{task_id}/status", auth=JWTAuth())
def get_task_status(request, task_id: str):
    """
    Check the status of a Celery task.
    """
    res = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": res.status,
        "result": res.result if res.ready() else None
    }
