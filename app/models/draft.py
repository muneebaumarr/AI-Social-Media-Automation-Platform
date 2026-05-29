from sqlalchemy import text
from sqlalchemy.orm import Session

import uuid

def create_draft(db: Session, client_id: str, created_by: str, draft_title: str, draft_content: str)->str:
    """
    Insert a new draft into the database and return the draft ID.
    
    """
    draft_id = str(uuid.uuid4())
    query = text("""
        INSERT INTO content_drafts
            (draft_id, client_id, created_by, draft_title,
             draft_content, draft_status)
        VALUES
            (:draft_id, :client_id, :created_by, :draft_title,
             :draft_content, 'draft')
    """)
    db.execute(query, {
        "draft_id":      draft_id,
        "client_id":     client_id,
        "created_by":    created_by,
        "draft_title":   draft_title,
        "draft_content": draft_content,
    })
    db.commit()
    return draft_id

def get_draft_by_id(db: Session, draft_id: str):
    """"
    Finds s single draft by its ID and returns row or none if not found.

    """
    query = text("""

        SELECT cd.*, c.client_name, u.full_name AS author_name
        FROM   content_drafts cd
        LEFT JOIN clients c ON c.client_id = cd.client_id
        LEFT JOIN users   u ON u.user_id   = cd.created_by
        WHERE  cd.draft_id = :draft_id

    """)

    result = db.execute(query, {"draft_id": draft_id})
    return result.mappings().first()

def get_drafts_by_user(db: Session, user_id: str, limit: int = 50):
    """"
    Returns a list of all drafts created by a specific user.    
    """

    query = text("""
        SELECT cd.draft_id, cd.draft_title, cd.draft_status,
               cd.created_at, c.client_name,
               (SELECT COUNT(*) FROM posts p
                WHERE p.draft_id = cd.draft_id) AS post_count
        FROM   content_drafts cd
        LEFT JOIN clients c ON c.client_id = cd.client_id
        WHERE  cd.created_by = :user_id
        ORDER BY cd.created_at DESC
        LIMIT  :limit
    """)
    result = db.execute(query, {"user_id": user_id, "limit": limit})
    return result.mappings().all()


def update_draft_status(db: Session, draft_id: str, new_status: str):
    """
    Updates the status of a draft.
    Used after AI repurposing completes.
    """
    query = text("""
        UPDATE content_drafts
        SET    draft_status = :status
        WHERE  draft_id = :draft_id
    """)
    db.execute(query, {"draft_id": draft_id, "status": new_status})
    db.commit()


def delete_draft(db: Session, draft_id: str, user_id: str) -> bool:
    """
    Deletes a draft. Only the owner can delete it.
    Returns True if deletion happened, False otherwise.
    """
    query = text("""
        DELETE FROM content_drafts
        WHERE draft_id = :draft_id AND created_by = :user_id
    """)
    result = db.execute(query, {
        "draft_id": draft_id,
        "user_id":  user_id,
    })
    db.commit()
    return result.rowcount > 0