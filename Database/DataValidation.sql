Use ai_social_media_db;

-- SECTION B — ROW COUNT VALIDATION
-- Expected: all counts should be > 0

SELECT 'users'                   AS table_name, COUNT(*) AS row_count FROM users
UNION ALL
SELECT 'clients',                               COUNT(*) FROM clients
UNION ALL
SELECT 'social_accounts',                       COUNT(*) FROM social_accounts
UNION ALL
SELECT 'content_drafts',                        COUNT(*) FROM content_drafts
UNION ALL
SELECT 'posts',                                 COUNT(*) FROM posts
UNION ALL
SELECT 'ai_generations',                        COUNT(*) FROM ai_generations
UNION ALL
SELECT 'approvals',                             COUNT(*) FROM approvals
UNION ALL
SELECT 'scheduled_posts',                       COUNT(*) FROM scheduled_posts
UNION ALL
SELECT 'analytics_logs',                        COUNT(*) FROM analytics_logs
UNION ALL
SELECT 'content_recommendations',               COUNT(*) FROM content_recommendations
UNION ALL
SELECT 'audit_logs',                            COUNT(*) FROM audit_logs;


-- SECTION C — NULL CHECKS ON KEY COLUMNS
-- Expected: all counts should return 0

-- users: critical columns must never be NULL
SELECT 'users - NULL email'       AS check_name,
       COUNT(*) AS null_count
FROM users
WHERE email IS NULL OR email = ''

UNION ALL

-- content_drafts: must always have an author and client
SELECT 'drafts - NULL created_by', COUNT(*)
FROM content_drafts
WHERE created_by IS NULL

UNION ALL

SELECT 'drafts - NULL client_id',  COUNT(*)
FROM content_drafts
WHERE client_id IS NULL

UNION ALL

-- posts: must always belong to a draft
SELECT 'posts - NULL draft_id',    COUNT(*)
FROM posts
WHERE draft_id IS NULL

UNION ALL

-- approvals: must always reference a post and a manager
SELECT 'approvals - NULL post_id', COUNT(*)
FROM approvals
WHERE post_id IS NULL

UNION ALL

SELECT 'approvals - NULL manager', COUNT(*)
FROM approvals
WHERE manager_id IS NULL

UNION ALL

-- analytics: engagement rate must always be set
SELECT 'analytics - NULL engagement', COUNT(*)
FROM analytics_logs
WHERE engagement_rate IS NULL

UNION ALL

-- scheduled_posts: must have a scheduled time
SELECT 'scheduled - NULL time',    COUNT(*)
FROM scheduled_posts
WHERE scheduled_time IS NULL;

-- SECTION D — FOREIGN KEY INTEGRITY CHECKS
-- Expected: all counts should return 0 (no orphan records)

-- Are there posts whose draft_id does not exist in content_drafts?
SELECT 'orphan posts (no draft)'       AS fk_check, COUNT(*) AS orphan_count
FROM posts p
LEFT JOIN content_drafts cd ON p.draft_id = cd.draft_id
WHERE cd.draft_id IS NULL

UNION ALL

-- Are there approvals whose post_id does not exist in posts?
SELECT 'orphan approvals (no post)',   COUNT(*)
FROM approvals a
LEFT JOIN posts p ON a.post_id = p.post_id
WHERE p.post_id IS NULL

UNION ALL

-- Are there approvals whose manager_id does not exist in users?
SELECT 'orphan approvals (no manager)', COUNT(*)
FROM approvals a
LEFT JOIN users u ON a.manager_id = u.user_id
WHERE u.user_id IS NULL

UNION ALL

-- Are there scheduled_posts whose post_id does not exist in posts?
SELECT 'orphan scheduled (no post)',   COUNT(*)
FROM scheduled_posts sp
LEFT JOIN posts p ON sp.post_id = p.post_id
WHERE p.post_id IS NULL

UNION ALL

-- Are there analytics_logs whose post_id does not exist in posts?
SELECT 'orphan analytics (no post)',   COUNT(*)
FROM analytics_logs al
LEFT JOIN posts p ON al.post_id = p.post_id
WHERE p.post_id IS NULL

UNION ALL

-- Are there social_accounts whose client_id does not exist in clients?
SELECT 'orphan social (no client)',    COUNT(*)
FROM social_accounts sa
LEFT JOIN clients c ON sa.client_id = c.client_id
WHERE c.client_id IS NULL

UNION ALL

-- Are there content_drafts whose client_id does not exist in clients?
SELECT 'orphan drafts (no client)',    COUNT(*)
FROM content_drafts cd
LEFT JOIN clients c ON cd.client_id = c.client_id
WHERE c.client_id IS NULL;


-- SECTION E — UPDATE AND DELETE EXAMPLES (required by M5)


-- UPDATE example: change a post status from pending to approved
UPDATE posts
SET    status = 'approved'
WHERE  status = 'pending_approval'
  AND  created_at < DATE_SUB(NOW(), INTERVAL 7 DAY)
LIMIT  1;

-- Confirm the update
SELECT post_id, platform, status
FROM   posts
WHERE  status = 'approved'
ORDER BY created_at DESC
LIMIT  3;

-- DELETE example: remove rejected posts older than 60 days
DELETE FROM posts
WHERE  status = 'rejected'
  AND  created_at < DATE_SUB(NOW(), INTERVAL 60 DAY);

-- Confirm the delete
SELECT status, COUNT(*) AS count
FROM   posts
GROUP BY status;

-- SECTION F — BUSINESS LOGIC VALIDATION QUERIES

-- Which platform generates the highest average engagement?
SELECT   platform,
         ROUND(AVG(al.engagement_rate), 2) AS avg_engagement,
         COUNT(*)                           AS post_count
FROM     analytics_logs al
JOIN     posts p ON al.post_id = p.post_id
GROUP BY platform
ORDER BY avg_engagement DESC;

-- How many posts per approval status?
SELECT   approval_status,
         COUNT(*) AS total
FROM     approvals
GROUP BY approval_status;

-- Which clients have the most scheduled posts?
SELECT   c.client_name,
         COUNT(sp.schedule_id) AS scheduled_count
FROM     clients c
JOIN     content_drafts cd ON cd.client_id = c.client_id
JOIN     posts p            ON p.draft_id  = cd.draft_id
JOIN     scheduled_posts sp ON sp.post_id  = p.post_id
GROUP BY c.client_name
ORDER BY scheduled_count DESC
LIMIT 5;