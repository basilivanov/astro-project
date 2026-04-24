# START_MODULE_CONTRACT: M-API-GATEWAY-ADMIN-CLIENTS
# purpose: Expose admin client CRUD routes.
# owns:
#   - backend/app/routers/admin-clients.py
# invariants:
#   - preserve extracted main.py route behavior and dependency semantics
#   - keep auth and access-control dependencies unchanged
# non_goals:
#   - product behavior redesign
# END_MODULE_CONTRACT: M-API-GATEWAY-ADMIN-CLIENTS

# START_MODULE_MAP: M-API-GATEWAY-ADMIN-CLIENTS
# public_entrypoints:
#   - router
#   - list_admin_clients
#   - get_admin_client
# semantic_blocks:
#   - ROUTER_EXTRACTION: moved gateway code with stable route contracts
# END_MODULE_MAP: M-API-GATEWAY-ADMIN-CLIENTS

from fastapi import APIRouter

from .gateway_context import *

router = APIRouter()

# START_BLOCK: ROUTER_EXTRACTION
@router.get("/api/admin/clients", response_model=List[AdminClientOut])
def list_admin_clients(
    limit: int = 25,
    offset: int = 0,
    q: Optional[str] = None,
    show_test: bool = False,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Return clients with report summaries.
    # INPUT: limit, offset, q.
    # OUTPUT: List[AdminClientOut].
    # CONTEXT: Used by the admin UI clients list.
    """

    query = db.query(Client)
    if not show_test:
        query = query.filter(Client.is_test == False)
        
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Client.full_name.ilike(search),
                Client.notes.ilike(search)
            )
        )

    rows = (
        query.order_by(Client.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [serialize_client(client) for client in rows]


@router.post("/api/admin/clients", response_model=AdminClientOut)
def create_admin_client(
    payload: AdminClientCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Create a client without generating a report.
    # INPUT: AdminClientCreateRequest payload.
    # OUTPUT: AdminClientOut.
    # CONTEXT: Admin-only manual client creation.
    """

    birth_dt = None
    try:
        birth_dt = parse_birth_datetime(payload.birth_date, payload.birth_timezone)
    except ValueError:
        birth_dt = None

    client = Client(
        full_name=payload.client_name,
        user_id=uuid.UUID(payload.user_id) if payload.user_id else None,
        notes=payload.client_note,
        birth_datetime=birth_dt,
        birth_time_known=payload.birth_time_known,
        birth_location=payload.birth_location,
        birth_lat=payload.birth_lat,
        birth_lon=payload.birth_lon,
        birth_timezone=payload.birth_timezone,
        birth_place_id=payload.birth_place_id,
        is_test=payload.is_test,
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    return serialize_client(client)


@router.put("/api/admin/clients/{client_id}", response_model=AdminClientOut)
def update_admin_client(
    client_id: str,
    payload: AdminClientCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Update existing client details.
    # INPUT: client_id, payload.
    # OUTPUT: Updated client.
    """
    try:
        client_uuid = uuid.UUID(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid client id.") from exc

    client = db.query(Client).filter(Client.id == client_uuid).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    birth_dt = None
    try:
        if payload.birth_date:
            birth_dt = parse_birth_datetime(payload.birth_date, payload.birth_timezone)
    except ValueError:
        pass

    client.full_name = payload.client_name
    client.notes = payload.client_note
    client.birth_datetime = birth_dt
    client.birth_time_known = payload.birth_time_known
    client.birth_location = payload.birth_location
    client.birth_lat = payload.birth_lat
    client.birth_lon = payload.birth_lon
    client.birth_timezone = payload.birth_timezone
    client.birth_place_id = payload.birth_place_id
    client.is_test = payload.is_test

    db.commit()
    db.refresh(client)
    return serialize_client(client)


@router.get("/api/admin/clients/{client_id}", response_model=AdminClientDetailOut)
def get_admin_client(
    client_id: str, 
    show_test: bool = False,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Return client detail with related reports.
    # INPUT: client_id.
    # OUTPUT: AdminClientDetailOut.
    # CONTEXT: Used by the admin client detail page.
    """

    try:
        client_uuid = uuid.UUID(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid client id.") from exc

    client = (
        db.query(Client)
        .filter(Client.id == client_uuid)
        .first()
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    reports_query = (
        db.query(Report)
        .filter(Report.client_id == client.id)
    )
    
    if not show_test:
        reports_query = reports_query.filter(Report.is_test == False)
        
    reports = reports_query.order_by(Report.created_at.desc()).all()

    reports_payload = []
    for report in reports:
        reports_payload.append(
            {
                "id": str(report.id),
                "report_type": report.report_type,
                "status": report.status,
                "paid": report.paid,
                "error_message": report.error_message,
                "error_at": format_datetime(report.error_at),
                "created_at": format_datetime(report.created_at),
                "updated_at": format_datetime(report.updated_at),
                "client_id": str(report.client_id),
                "client_name": report.client.full_name if report.client else "",
                "chunk_count": len(report.chunks),
            }
        )

    return {
        "client": serialize_client(client),
        "reports": reports_payload,
    }

# END_BLOCK: ROUTER_EXTRACTION
