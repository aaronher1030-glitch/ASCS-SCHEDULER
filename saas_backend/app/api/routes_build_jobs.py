from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import require_roles, require_tenant_access
from app.models.entities import User
from app.schemas.build_jobs import BuildConflict, BuildJobCreateRequest, BuildJobResponse
from app.services.build_jobs import build_job_service


router = APIRouter()


def _assert_job_tenant(job_id: str, tenant_id: str) -> None:
    job_tenant = build_job_service.get_job_tenant(job_id)
    if job_tenant is None:
        raise HTTPException(status_code=404, detail="Build job not found.")
    if job_tenant != tenant_id:
        raise HTTPException(status_code=403, detail="Build job tenant mismatch.")


@router.post("/build-jobs", response_model=BuildJobResponse)
def create_build_job(
    payload: BuildJobCreateRequest,
    _: User = Depends(require_roles("admin", "scheduler", "registrar")),
    tenant_id: str = Depends(require_tenant_access),
) -> BuildJobResponse:
    if payload.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Payload tenant_id does not match authenticated tenant.")
    return build_job_service.create_job(payload)


@router.get("/build-jobs/{job_id}", response_model=BuildJobResponse)
def get_build_job(
    job_id: str,
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> BuildJobResponse:
    _assert_job_tenant(job_id, tenant_id)
    job = build_job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Build job not found.")
    return job


@router.get("/build-jobs/{job_id}/conflicts", response_model=list[BuildConflict])
def get_build_conflicts(
    job_id: str,
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> list[BuildConflict]:
    _assert_job_tenant(job_id, tenant_id)
    return build_job_service.list_conflicts(job_id)


@router.post("/build-jobs/{job_id}/publish", response_model=BuildJobResponse)
def publish_build_job(
    job_id: str,
    _: User = Depends(require_roles("admin", "scheduler")),
    tenant_id: str = Depends(require_tenant_access),
) -> BuildJobResponse:
    _assert_job_tenant(job_id, tenant_id)
    try:
        return build_job_service.publish(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/build-jobs/{job_id}/wait", response_model=BuildJobResponse)
def wait_for_build_job_update(
    job_id: str,
    since_status: str | None = Query(default=None),
    timeout_seconds: int = Query(default=20, ge=1, le=60),
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> BuildJobResponse:
    _assert_job_tenant(job_id, tenant_id)
    job = build_job_service.wait_for_update(job_id, since_status=since_status, timeout_seconds=timeout_seconds)
    if not job:
        raise HTTPException(status_code=404, detail="Build job not found.")
    return job
