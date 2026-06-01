from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid


def get_overview_stats(db: Session, user_id: str) -> dict:
    """
    Returns the four headline numbers shown at the top.
    """
    query = text("""
        SELECT
            COUNT(DISTINCT p.post_id) AS total_posts,
            COALESCE(SUM(al.views), 0)    AS total_views,
            COALESCE(SUM(al.likes), 0)    AS total_likes,
            COALESCE(SUM(al.comments), 0) AS total_comments,
            COALESCE(SUM(al.shares), 0)   AS total_shares,
            COALESCE(AVG(al.engagement_rate), 0) AS avg_engagement
        FROM   posts p
        JOIN   content_drafts cd ON cd.draft_id = p.draft_id
        LEFT JOIN analytics_logs al ON al.post_id = p.post_id
        WHERE  cd.created_by = :user_id
    """)
    row = db.execute(query, {"user_id": user_id}).mappings().first()

    total_engagement = (row["total_likes"] + row["total_comments"]
                        + row["total_shares"])

    return {
        "total_posts":      int(row["total_posts"] or 0),
        "total_views":      int(row["total_views"] or 0),
        "total_engagement": int(total_engagement),
        "avg_engagement":   round(float(row["avg_engagement"] or 0), 2),
    }


def get_engagement_by_platform(db: Session, user_id: str):
    """
    Returns engagement metrics grouped by platform.
    Used for the bar chart.
    """
    query = text("""
        SELECT
            p.platform,
            COUNT(DISTINCT p.post_id) AS post_count,
            COALESCE(SUM(al.likes), 0)    AS likes,
            COALESCE(SUM(al.comments), 0) AS comments,
            COALESCE(SUM(al.shares), 0)   AS shares,
            COALESCE(AVG(al.engagement_rate), 0) AS avg_rate
        FROM   posts p
        JOIN   content_drafts cd ON cd.draft_id = p.draft_id
        LEFT JOIN analytics_logs al ON al.post_id = p.post_id
        WHERE  cd.created_by = :user_id
        GROUP  BY p.platform
        ORDER  BY avg_rate DESC
    """)
    rows = db.execute(query, {"user_id": user_id}).mappings().all()

    return [{
        "platform":    r["platform"],
        "post_count":  int(r["post_count"]),
        "likes":       int(r["likes"]),
        "comments":    int(r["comments"]),
        "shares":      int(r["shares"]),
        "avg_rate":    round(float(r["avg_rate"] or 0), 2),
        "total":       int(r["likes"]) + int(r["comments"]) + int(r["shares"]),
    } for r in rows]


def get_status_breakdown(db: Session, user_id: str):
    """
    Returns post count grouped by status.
    Used for the donut chart.
    """
    query = text("""
        SELECT p.status, COUNT(*) AS count
        FROM   posts p
        JOIN   content_drafts cd ON cd.draft_id = p.draft_id
        WHERE  cd.created_by = :user_id
        GROUP  BY p.status
    """)
    rows = db.execute(query, {"user_id": user_id}).mappings().all()
    return [{"status": r["status"], "count": r["count"]} for r in rows]


def get_top_posts(db: Session, user_id: str, limit: int = 5):
    """
    Returns the highest-engagement posts.
    """
    query = text("""
        SELECT
            p.post_id, p.platform, p.repurposed_content,
            COALESCE(SUM(al.likes), 0)    AS likes,
            COALESCE(SUM(al.comments), 0) AS comments,
            COALESCE(SUM(al.shares), 0)   AS shares,
            COALESCE(MAX(al.engagement_rate), 0) AS engagement_rate
        FROM   posts p
        JOIN   content_drafts cd ON cd.draft_id = p.draft_id
        JOIN   analytics_logs al ON al.post_id = p.post_id
        WHERE  cd.created_by = :user_id
        GROUP  BY p.post_id, p.platform, p.repurposed_content
        ORDER  BY engagement_rate DESC
        LIMIT  :limit
    """)
    rows = db.execute(query, {
        "user_id": user_id,
        "limit":   limit,
    }).mappings().all()

    return [{
        "post_id":         r["post_id"],
        "platform":        r["platform"],
        "preview":         (r["repurposed_content"] or "")[:120] + "...",
        "likes":           int(r["likes"]),
        "comments":        int(r["comments"]),
        "shares":          int(r["shares"]),
        "engagement_rate": round(float(r["engagement_rate"] or 0), 2),
    } for r in rows]


def get_latest_recommendation(db: Session, user_id: str):
    """
    Returns the most recent AI recommendation for this user's clients.
    """
    query = text("""
        SELECT cr.*
        FROM   content_recommendations cr
        WHERE  cr.client_id IN (
            SELECT DISTINCT client_id
            FROM   content_drafts
            WHERE  created_by = :user_id
        )
        ORDER  BY cr.created_at DESC
        LIMIT  1
    """)
    return db.execute(query, {"user_id": user_id}).mappings().first()


def save_recommendation(db: Session, client_id: str,
                        best_platform: str, recommendation_text: str) -> str:
    """
    Saves a new AI-generated recommendation.
    """
    rec_id = str(uuid.uuid4())
    week_start = datetime.now().date()
    week_end   = week_start + timedelta(days=6)

    query = text("""
        INSERT INTO content_recommendations
            (recommendation_id, client_id, week_start_date, week_end_date,
             best_platform, recommendation_text)
        VALUES
            (:rid, :cid, :ws, :we, :bp, :rt)
    """)
    db.execute(query, {
        "rid": rec_id,
        "cid": client_id,
        "ws":  week_start,
        "we":  week_end,
        "bp":  best_platform,
        "rt":  recommendation_text,
    })
    db.commit()
    return rec_id