from sqlalchemy import text
from sqlalchemy.orm import Session
import uuid, random, string


def generate_invite_code(length: int = 6) -> str:
    """Generates a random 6-character invite code like 'AMC8X2'."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


def create_brand(db: Session, owner_id: str, brand_name: str,
                 industry: str = None, brand_voice: str = None,
                 target_audience: str = None, brand_color: str = "#0a0a0a",
                 do_not_use: str = None) -> str:
    """
    Creates a new brand owned by the admin.
    Generates a unique invite code automatically.
    """
    client_id   = str(uuid.uuid4())
    invite_code = generate_invite_code()

    # Make sure invite code is unique (very rare collision but possible)
    while True:
        check = db.execute(
            text("SELECT 1 FROM clients WHERE invite_code = :c"),
            {"c": invite_code},
        ).first()
        if not check:
            break
        invite_code = generate_invite_code()

    query = text("""
        INSERT INTO clients
            (client_id, client_name, owner_id, industry,
             brand_voice, target_audience, brand_color,
             do_not_use, invite_code)
        VALUES
            (:cid, :name, :owner, :industry,
             :voice, :audience, :color, :avoid, :code)
    """)
    db.execute(query, {
        "cid":      client_id,
        "name":     brand_name,
        "owner":    owner_id,
        "industry": industry,
        "voice":    brand_voice,
        "audience": target_audience,
        "color":    brand_color,
        "avoid":    do_not_use,
        "code":     invite_code,
    })

    # Owner is automatically a member of their own brand
    db.execute(text("""
        INSERT INTO client_members (client_id, user_id, member_role)
        VALUES (:cid, :uid, 'manager')
    """), {"cid": client_id, "uid": owner_id})

    db.commit()
    return client_id


def get_brands_for_user(db: Session, user_id: str, user_role: str):
    """
    Returns ALL brands accessible to this user.
    - Admin → brands they own + brands they're added to
    - Writer/Manager → only brands they're a member of
    """
    if user_role == "admin":
        # Admin sees: owned brands + brands they're members of
        query = text("""
            SELECT DISTINCT c.*, 'owner' AS access_type
            FROM   clients c
            WHERE  c.owner_id = :uid
            UNION
            SELECT DISTINCT c.*, cm.member_role AS access_type
            FROM   clients c
            JOIN   client_members cm ON cm.client_id = c.client_id
            WHERE  cm.user_id = :uid
            ORDER  BY client_name
        """)
    else:
        # Writers/Managers only see brands they're invited to
        query = text("""
            SELECT c.*, cm.member_role AS access_type
            FROM   clients c
            JOIN   client_members cm ON cm.client_id = c.client_id
            WHERE  cm.user_id = :uid
            ORDER  BY c.client_name
        """)

    return db.execute(query, {"uid": user_id}).mappings().all()


def get_brand_by_id(db: Session, client_id: str, user_id: str):
    """
    Returns brand info if the user has access to it.
    Returns None if no access.
    """
    query = text("""
        SELECT c.*,
               CASE
                   WHEN c.owner_id = :uid THEN 'owner'
                   ELSE COALESCE(cm.member_role, 'none')
               END AS access_type
        FROM   clients c
        LEFT JOIN client_members cm
            ON cm.client_id = c.client_id AND cm.user_id = :uid
        WHERE  c.client_id = :cid
          AND  (c.owner_id = :uid OR cm.user_id = :uid)
    """)
    return db.execute(query, {"cid": client_id, "uid": user_id}).mappings().first()


def update_brand(db: Session, client_id: str, owner_id: str,
                 industry: str, brand_voice: str,
                 target_audience: str, brand_color: str,
                 do_not_use: str) -> bool:
    """
    Updates brand details. Only the owner can edit.
    Returns True if update happened, False if not authorized.
    """
    query = text("""
        UPDATE clients
        SET    industry        = :industry,
               brand_voice     = :voice,
               target_audience = :audience,
               brand_color     = :color,
               do_not_use      = :avoid
        WHERE  client_id = :cid AND owner_id = :owner
    """)
    result = db.execute(query, {
        "cid":      client_id,
        "owner":    owner_id,
        "industry": industry,
        "voice":    brand_voice,
        "audience": target_audience,
        "color":    brand_color,
        "avoid":    do_not_use,
    })
    db.commit()
    return result.rowcount > 0


def add_member_by_invite_code(db: Session, user_id: str, invite_code: str):
    """
    Adds a user to a brand using the invite code.
    Returns the client_id if successful, None if code is invalid.
    """
    brand = db.execute(
        text("SELECT client_id, client_name FROM clients WHERE invite_code = :c"),
        {"c": invite_code.upper()},
    ).mappings().first()

    if not brand:
        return None

    # Check if already a member
    existing = db.execute(text("""
        SELECT 1 FROM client_members
        WHERE client_id = :cid AND user_id = :uid
    """), {"cid": brand["client_id"], "uid": user_id}).first()

    if existing:
        return {"client_id": brand["client_id"],
                "client_name": brand["client_name"],
                "already_member": True}

    # Add as writer
    db.execute(text("""
        INSERT INTO client_members (client_id, user_id, member_role)
        VALUES (:cid, :uid, 'writer')
    """), {"cid": brand["client_id"], "uid": user_id})
    db.commit()

    return {"client_id":   brand["client_id"],
            "client_name": brand["client_name"],
            "already_member": False}


def get_brand_members(db: Session, client_id: str):
    """Returns all users who have access to this brand."""
    query = text("""
        SELECT u.user_id, u.full_name, u.email,
               cm.member_role, cm.added_at
        FROM   client_members cm
        JOIN   users u ON u.user_id = cm.user_id
        WHERE  cm.client_id = :cid
        ORDER  BY cm.added_at DESC
    """)
    return db.execute(query, {"cid": client_id}).mappings().all()