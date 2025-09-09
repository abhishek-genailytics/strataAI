"""
Playground sessions API with CRUD + archive/restore + duplicate + clear operations.
Uses playground authentication with RLS via Supabase JWT.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..models.organization import Organization
from ..models.playground_session import (
    PlaygroundSessionCreate,
    PlaygroundSessionUpdate,
    PlaygroundSessionRead,
    PlaygroundSessionList,
    PlaygroundSessionArchive,
    PlaygroundSessionDuplicate,
    PlaygroundSessionClear
)
from ..services.playground_session_svc import PlaygroundSessionService
from ..errors.openai_envelope import openai_error


router = APIRouter(prefix="/playground/sessions", tags=["Playground Sessions"])


@router.post("", response_model=PlaygroundSessionRead)
async def create_session(
    data: PlaygroundSessionCreate,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Create a new playground session with server-controlled defaults."""
    
    try:
        service = PlaygroundSessionService()
        
        # Validate model format (provider/model)
        if "/" not in data.model:
            openai_error(
                400,
                "Model must be in 'provider/model' format (e.g., 'openai/gpt-4o-mini')",
                code="invalid_model_format"
            )
        
        provider_from_model = data.model.split("/")[0]
        if provider_from_model != data.provider:
            openai_error(
                400,
                f"Provider '{data.provider}' does not match model prefix '{provider_from_model}'",
                code="provider_model_mismatch"
            )
        
        if not organization:
            raise HTTPException(
                status_code=400,
                detail="Organization context required"
            )
        
        session = await service.create_session(
            user_id=current_user.id,
            organization_id=organization.id,
            data=data
        )
        
        # Add preflight warning if API key is missing
        warning = await service.get_preflight_warning(
            organization_id=organization.id,
            provider=data.provider,
            jwt_token=current_user.jwt_token
        )
        
        if warning:
            # Add warning to response metadata
            session.metadata["preflight_warning"] = warning
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        openai_error(
            500,
            f"Failed to create session: {str(e)}",
            code="session_creation_failed"
        )


@router.get("", response_model=PlaygroundSessionList)
async def list_sessions(
    archived: str = Query("false", regex="^(true|false|all)$", description="Filter by archive status"),
    limit: int = Query(20, ge=1, le=100, description="Number of sessions to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor (session ID)"),
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """List user's playground sessions with pagination."""
    
    try:
        if not organization:
            raise HTTPException(
                status_code=400,
                detail="Organization context required"
            )
        
        service = PlaygroundSessionService()
        
        return await service.list_sessions(
            user_id=current_user.id,
            organization_id=organization.id,
            archived=archived,
            limit=limit,
            cursor=cursor
        )
        
    except Exception as e:
        openai_error(
            500,
            f"Failed to list sessions: {str(e)}",
            code="session_list_failed"
        )


@router.get("/{session_id}", response_model=PlaygroundSessionRead)
async def get_session(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get a single playground session by ID."""
    
    try:
        if not organization:
            raise HTTPException(
                status_code=400,
                detail="Organization context required"
            )
        
        service = PlaygroundSessionService()
        
        session = await service.get_session(
            session_id=session_id,
            user_id=current_user.id,
            organization_id=organization.id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"message": "Session not found", "type": "invalid_request_error", "code": "session_not_found"}}
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        openai_error(
            500,
            f"Failed to get session: {str(e)}",
            code="session_get_failed"
        )


@router.put("/{session_id}", response_model=PlaygroundSessionRead)
async def update_session(
    session_id: UUID,
    data: PlaygroundSessionUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Update session title and/or metadata. Supports provider/model picker updates.
    
    Model format must be 'provider/model' (e.g., 'openai/gpt-4o-mini') for OpenAI compatibility.
    """
    
    try:
        if not organization:
            raise HTTPException(
                status_code=400,
                detail="Organization context required"
            )
        
        # Validate model format if provided
        if data.model and "/" not in data.model:
            openai_error(
                400,
                "Model must be in 'provider/model' format (e.g., 'openai/gpt-4o-mini')",
                code="invalid_model_format"
            )
        
        # Validate provider/model consistency if both provided (provider_model_mismatch)
        if data.model and data.provider:
            provider_from_model = data.model.split("/")[0]
            if provider_from_model != data.provider:
                openai_error(
                    400,
                    f"Provider '{data.provider}' does not match model prefix '{provider_from_model}'",
                    code="provider_model_mismatch"
                )
        
        service = PlaygroundSessionService()
        
        session = await service.update_session(
            session_id=session_id,
            user_id=current_user.id,
            organization_id=organization.id,
            data=data
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"message": "Session not found", "type": "invalid_request_error", "code": "session_not_found"}}
            )
        
        return session
        
    except HTTPException:
        raise
    except ValueError as e:
        openai_error(400, str(e), code="invalid_request")
    except Exception as e:
        openai_error(
            500,
            f"Failed to update session: {str(e)}",
            code="session_update_failed"
        )


@router.post("/{session_id}/archive", response_model=PlaygroundSessionArchive)
async def archive_session(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Archive a session (soft delete)."""
    
    try:
        if not organization:
            raise HTTPException(
                status_code=400,
                detail="Organization context required"
            )
        
        service = PlaygroundSessionService()
        
        result = await service.archive_session(
            session_id=session_id,
            user_id=current_user.id,
            organization_id=organization.id
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"message": "Session not found", "type": "invalid_request_error", "code": "session_not_found"}}
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        openai_error(
            500,
            f"Failed to archive session: {str(e)}",
            code="session_archive_failed"
        )


@router.post("/{session_id}/restore", response_model=PlaygroundSessionArchive)
async def restore_session(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Restore an archived session."""
    
    try:
        if not organization:
            raise HTTPException(
                status_code=400,
                detail="Organization context required"
            )
        
        service = PlaygroundSessionService()
        
        result = await service.restore_session(
            session_id=session_id,
            user_id=current_user.id,
            organization_id=organization.id
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"message": "Session not found", "type": "invalid_request_error", "code": "session_not_found"}}
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        openai_error(
            500,
            f"Failed to restore session: {str(e)}",
            code="session_restore_failed"
        )


@router.post("/{session_id}/duplicate", response_model=PlaygroundSessionDuplicate)
async def duplicate_session(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Duplicate a session with all messages (no usage records for clean analytics)."""
    
    try:
        if not organization:
            raise HTTPException(
                status_code=400,
                detail="Organization context required"
            )
        
        service = PlaygroundSessionService()
        
        result = await service.duplicate_session(
            session_id=session_id,
            user_id=current_user.id,
            organization_id=organization.id
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"message": "Session not found", "type": "invalid_request_error", "code": "session_not_found"}}
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        openai_error(
            500,
            f"Failed to duplicate session: {str(e)}",
            code="session_duplicate_failed"
        )


@router.post("/{session_id}/clear", response_model=PlaygroundSessionClear)
async def clear_session(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Clear all messages from session while keeping metadata and setup defaults."""
    
    try:
        if not organization:
            raise HTTPException(
                status_code=400,
                detail="Organization context required"
            )
        
        service = PlaygroundSessionService()
        
        result = await service.clear_session(
            session_id=session_id,
            user_id=current_user.id,
            organization_id=organization.id
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"message": "Session not found", "type": "invalid_request_error", "code": "session_not_found"}}
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        openai_error(
            500,
            f"Failed to clear session: {str(e)}",
            code="session_clear_failed"
        )
