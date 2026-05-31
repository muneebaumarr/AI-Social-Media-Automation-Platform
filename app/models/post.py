from sqlalchemy import text
from sqlalchemy.orm import Session
import uuid


def create_post(db: Session, draft_id: str, platform: str,
                repurposed_content: str, caption: str,
                hashtags: str) -> str:
    """
    Saves an AI-generated post to the database.
    Returns the new post's ID.
    """
    post_id = str(uuid.uuid4())
    query = text("""
        INSERT INTO posts
            (post_id, draft_id, platform, repurposed_content,
             caption, hashtags, status)
        VALUES
            (:post_id, :draft_id, :platform, :repurposed_content,
             :caption, :hashtags, 'pending_approval')
    """)
    db.execute(query, {
        "post_id":            post_id,
        "draft_id":           draft_id,
        "platform":           platform,
        "repurposed_content": repurposed_content,
        "caption":            caption,
        "hashtags":           hashtags,
    })
    db.commit()
    return post_id


def save_ai_generation(db: Session, draft_id: str, platform: str,
                       prompt: str, generated_text: str) -> str:
    """
    Logs every AI call for audit trail and debugging.
    Stores the exact prompt sent and the response received.
    """
    generation_id = str(uuid.uuid4())
    query = text("""
        INSERT INTO ai_generations
            (generation_id, draft_id, platform, prompt, generated_text)
        VALUES
            (:generation_id, :draft_id, :platform, :prompt, :generated_text)
    """)
    db.execute(query, {
        "generation_id":  generation_id,
        "draft_id":       draft_id,
        "platform":       platform,
        "prompt":         prompt,
        "generated_text": generated_text,
    })
    db.commit()
    return generation_id


def get_posts_by_draft(db: Session, draft_id: str):
    """
    Returns all posts generated from a specific draft.
    """
    query = text("""
        SELECT * FROM posts
        WHERE  draft_id = :draft_id
        ORDER BY created_at DESC
    """)
    result = db.execute(query, {"draft_id": draft_id})
    return result.mappings().all()


def get_posts_by_status(db: Session, status: str):
    """
    Returns all posts with a specific status.
    Used by the manager review queue.
    """
    query = text("""
        SELECT p.*, cd.draft_title, u.full_name AS author_name
        FROM   posts p
        JOIN   content_drafts cd ON cd.draft_id = p.draft_id
        JOIN   users u           ON u.user_id   = cd.created_by
        WHERE  p.status = :status
        ORDER BY p.created_at DESC
    """)
    result = db.execute(query, {"status": status})
    return result.mappings().all()


def get_all_posts_for_user(db: Session, user_id: str):
    """
    Returns all posts that belong to drafts created by this user.
    """
    query = text("""
        SELECT p.*, cd.draft_title
        FROM   posts p
        JOIN   content_drafts cd ON cd.draft_id = p.draft_id
        WHERE  cd.created_by = :user_id
        ORDER BY p.created_at DESC
    """)
    result = db.execute(query, {"user_id": user_id})
    return result.mappings().all()


def update_post_status(db: Session, post_id: str, new_status: str):
    """
    Updates a post's status.
    Used during approval workflow.
    """
    query = text("""
        UPDATE posts
        SET    status = :status
        WHERE  post_id = :post_id
    """)
    db.execute(query, {"post_id": post_id, "status": new_status})
    db.commit()


def get_post_by_id(db: Session, post_id: str):
    """
    Finds a single post by ID with full context.
    """
    query = text("""
        SELECT p.*, cd.draft_title, cd.draft_content,
               u.full_name AS author_name, u.email AS author_email
        FROM   posts p
        JOIN   content_drafts cd ON cd.draft_id = p.draft_id
        JOIN   users u           ON u.user_id   = cd.created_by
        WHERE  p.post_id = :post_id
    """)
    result = db.execute(query, {"post_id": post_id})
    return result.mappings().first()


def get_posts_with_schedule_for_user(db: Session, user_id: str):
    """
    Returns all posts owned by user along with scheduling info.
    Used by the Posts page so we know which posts are scheduled.
    """
    query = text("""
        SELECT p.*, cd.draft_title,
               sp.schedule_id, sp.scheduled_time, sp.schedule_status,
               (SELECT remarks FROM approvals
                WHERE post_id = p.post_id
                ORDER BY approval_date DESC LIMIT 1) AS latest_remarks
        FROM   posts p
        JOIN   content_drafts cd ON cd.draft_id = p.draft_id
        LEFT JOIN scheduled_posts sp ON sp.post_id = p.post_id
        WHERE  cd.created_by = :user_id
        ORDER BY p.created_at DESC
    """)
    result = db.execute(query, {"user_id": user_id})
    return result.mappings().all()