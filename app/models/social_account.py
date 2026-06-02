from sqlalchemy import text
from sqlalchemy.orm import Session
import uuid


def get_accounts_for_brand(db: Session, client_id: str):
    """
    Returns all social accounts connected to a brand.
    Used to show which platforms are connected and which aren't.
    """
    query = text("""
        SELECT account_id, platform, account_name,
               connected_status, buffer_profile_id, connected_at
        FROM   social_accounts
        WHERE  client_id = :cid
        ORDER  BY platform
    """)
    return db.execute(query, {"cid": client_id}).mappings().all()


def connect_account(db: Session, client_id: str, platform: str,
                    account_name: str) -> str:
    """
    Connects a social account to a brand.
    Returns the account_id.
    Uses upsert logic: if platform already exists for this brand, update it.
    """
    # Check if already exists (we have UNIQUE constraint on client+platform)
    existing = db.execute(text("""
        SELECT account_id FROM social_accounts
        WHERE client_id = :cid AND platform = :p
    """), {"cid": client_id, "p": platform}).first()

    if existing:
        # Update the existing connection
        db.execute(text("""
            UPDATE social_accounts
            SET    account_name      = :name,
                   connected_status  = 1,
                   buffer_profile_id = :buf
            WHERE  client_id = :cid AND platform = :p
        """), {
            "cid":  client_id,
            "p":    platform,
            "name": account_name,
            "buf":  str(uuid.uuid4()),
        })
        db.commit()
        return existing[0]

    # Create new connection
    account_id = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO social_accounts
            (account_id, client_id, platform, account_name,
             connected_status, buffer_profile_id)
        VALUES
            (:aid, :cid, :p, :name, 1, :buf)
    """), {
        "aid":  account_id,
        "cid":  client_id,
        "p":    platform,
        "name": account_name,
        "buf":  str(uuid.uuid4()),
    })
    db.commit()
    return account_id


def disconnect_account(db: Session, client_id: str, platform: str) -> bool:
    """
    Disconnects a social account.
    We don't delete the row — we mark it disconnected for audit.
    """
    result = db.execute(text("""
        UPDATE social_accounts
        SET    connected_status = 0
        WHERE  client_id = :cid AND platform = :p
    """), {"cid": client_id, "p": platform})
    db.commit()
    return result.rowcount > 0