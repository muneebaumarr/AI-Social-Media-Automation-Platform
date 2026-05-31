from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid


def create_approval(db: Session, post_id: str, manager_id: str, approval_status:str, remarks: str = None)-> str:

    """"
    Creates an approval record for a post.
    Returns the new approval's ID.
    Records the manager's decision (approved/rejected) and any optional remarks.

    
    """

    appoval_id = str(uuid.uuid4())
    query = text("""
        INSERT INTO approvals
            (approval_id, post_id, manager_id, approval_status, remarks)
        VALUES
            (:approval_id, :post_id, :manager_id, :approval_status, :remarks)
    """)
    db.execute(query, {
        "approval_id":     appoval_id,
        "post_id":         post_id,
        "manager_id":      manager_id,
        "approval_status": approval_status,
        "remarks":         remarks,
    })

    db.commit()
    return appoval_id


def get_approval_history(db: Session, post_id: str):
    """
    Retrieves the approval history for a specific post.
    Returns a list of approval records with manager decisions and remarks.
    """
    query = text("""
    SELECT a.*, u.full_name AS manager_name
    FROM   approvals a
    JOIN   users u ON u.user_id = a.manager_id
    WHERE  a.post_id = :post_id
    ORDER BY a.approval_date DESC
    """)
    result = db.execute(query, {"post_id": post_id})
    return result.mappings().all()