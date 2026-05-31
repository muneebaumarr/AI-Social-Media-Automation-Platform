from sqlalchemy import text
from sqlalchemy.orm import Session
import uuid


def create_schedule(db: Session, post_id: str, scheduled_time: str) -> str:
    """
    Creates a scheduling record for a post.
    Sets schedule_status to 'pending' until Buffer confirms.
    """
    schedule_id = str(uuid.uuid4())
    query = text("""
        INSERT INTO scheduled_posts
            (schedule_id, post_id, scheduled_time, schedule_status)
        VALUES
            (:schedule_id, :post_id, :scheduled_time, 'pending')
    """)
    db.execute(query, {
        "schedule_id":    schedule_id,
        "post_id":        post_id,
        "scheduled_time": scheduled_time,
    })
    db.commit()
    return schedule_id


def get_schedule_by_post(db: Session, post_id: str):
    """
    Returns the schedule record for a specific post (if any).
    """
    query = text("""
        SELECT * FROM scheduled_posts
        WHERE  post_id = :post_id
    """)
    result = db.execute(query, {"post_id": post_id})
    return result.mappings().first()