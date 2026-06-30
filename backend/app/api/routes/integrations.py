from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError, PolicyError
from app.models.company import Company
from app.models.platform_account import PlatformAccount
from app.schemas.integration import BlueskyConnectRequest, BlueskyStatusRead
from app.schemas.platform_account import PlatformAccountRead
from app.services.bluesky_service import BlueskyService

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])


@router.get("/bluesky/status", response_model=BlueskyStatusRead)
def bluesky_status(
    company_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
) -> BlueskyStatusRead:
    if not company_id:
        return BlueskyStatusRead(configured=False, connected=False)
    account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.company_id == company_id,
            PlatformAccount.platform == "bluesky",
            PlatformAccount.status == "connected",
        )
        .order_by(PlatformAccount.created_at.desc())
        .first()
    )
    return BlueskyStatusRead(
        configured=bool(account),
        connected=bool(account),
        handle=account.platform_username if account else None,
        account_id=account.id if account else None,
    )


@router.post("/bluesky/connect", response_model=PlatformAccountRead)
def connect_bluesky(payload: BlueskyConnectRequest, db: Session = Depends(get_db)) -> PlatformAccount:
    company = db.get(Company, payload.company_id)
    if not company:
        raise NotFoundError("Company not found.")
    handle = payload.handle.strip().lstrip("@")
    app_password = payload.app_password.get_secret_value()
    try:
        session = BlueskyService().create_session(identifier=handle, app_password=app_password)
    except Exception as exc:
        raise PolicyError(f"Bluesky authentication failed: {str(exc)[:240]}") from exc

    account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.company_id == payload.company_id,
            PlatformAccount.platform == "bluesky",
        )
        .one_or_none()
    )
    if not account:
        account = PlatformAccount(
            company_id=payload.company_id,
            platform="bluesky",
            account_label=f"@{session.handle}",
            platform_user_id=session.did,
            platform_username=session.handle,
            auth_type="ephemeral_app_password",
            secret_ref="ephemeral:user-supplied",
            status="connected",
            daily_send_limit=5,
        )
        db.add(account)
    else:
        account.account_label = f"@{session.handle}"
        account.platform_user_id = session.did
        account.platform_username = session.handle
        account.auth_type = "ephemeral_app_password"
        account.secret_ref = "ephemeral:user-supplied"
        account.status = "connected"
        account.daily_send_limit = 5
    db.commit()
    db.refresh(account)
    return account
