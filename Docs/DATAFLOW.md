# Dataflow Description
**Project:** AI Social Media Automation Platform  
**Milestone:** 3  
**Commit:** M3: Synthetic data generated; dataflow documented

---

## Overview

This document describes how data enters the AI Social Media Automation Platform, how it moves through the 11 database tables, and what outputs the system produces. The flow follows the real-world lifecycle of a social media post — from a writer's first draft to published content and performance analysis.

---

## Data Entry Points

Data enters the system through three sources:

1. **User Input (GUI Forms):** Writers create drafts. Managers submit approvals. Users configure client profiles and connect social accounts.
2. **AI API (OpenAI / Gemini):** The backend sends draft content to the AI and receives platform-specific repurposed posts. The prompt and response are both stored.
3. **Buffer API:** After scheduling, Buffer returns an `update_id` confirming the post is queued. After publishing, Buffer (or a webhook) returns analytics data.

---

## Step-by-Step Dataflow

### Step 1 — System Setup
```
users → INSERT (writer, manager, admin registered)
clients → INSERT (brand profile created)
social_accounts → INSERT (client connects Instagram, LinkedIn, etc.)
audit_logs → INSERT (LOGIN action recorded)
```
A user registers and is assigned a role. A client profile is created for the brand they manage. Social media accounts are connected per client. Every login and setup action is written to `audit_logs`.

---

### Step 2 — Draft Creation
```
User fills form →
content_drafts → INSERT (draft_id, client_id, created_by, draft_content)
audit_logs → INSERT (action='CREATE', entity_name='content_drafts')
```
A writer selects a client, writes the original draft text, and submits it. One row is inserted into `content_drafts`. The `draft_status` starts as `'draft'`. The action is logged in `audit_logs`.

---

### Step 3 — AI Repurposing
```
draft_content read from content_drafts →
Sent to AI API (OpenAI) →
ai_generations → INSERT (prompt, generated_text per platform)
posts → INSERT (one row per platform: instagram, linkedin, facebook, etc.)
content_drafts → UPDATE (draft_status = 'repurposed')
```
The backend reads the draft content, builds a platform-specific prompt, and calls the AI API. For each connected platform of the client, one row is inserted into `ai_generations` (storing the raw prompt and AI response) and one row is inserted into `posts` (storing the final repurposed content, caption, and hashtags). The draft status is updated to `'repurposed'`.

**Dependency rule:** `posts` depends on `content_drafts`. `ai_generations` depends on `content_drafts`. Both must exist before this step.

---

### Step 4 — Approval Notification
```
posts → UPDATE (status = 'pending_approval')
Email sent to manager (external — not stored in DB)
Manager opens review link → reads from posts table
```
The system updates all new posts to `'pending_approval'` and sends the manager an email with a review link. No new row is inserted at this step — the email is external. The manager uses the review link to read post data from the `posts` table in the GUI.

---

### Step 5 — Manager Review
```
Manager submits action →
approvals → INSERT (post_id, manager_id, approval_status, remarks)
posts → UPDATE (status = 'approved' | 'rejected' | 'request_edit')
audit_logs → INSERT (action='APPROVE' | 'REJECT', entity_name='approvals')
```
The manager reviews each post and chooses Approve, Reject, or Request Edit. Each decision inserts one row into `approvals` with remarks. The corresponding post's `status` column is updated. Every decision is recorded in `audit_logs`.

**Dependency rule:** `approvals` depends on `posts` (FK: post_id) and `users` (FK: manager_id). Both must exist.

---

### Step 6 — Scheduling via Buffer
```
posts (WHERE status = 'approved') read →
User selects date/time →
Buffer API called →
scheduled_posts → INSERT (post_id, buffer_update_id, scheduled_time)
posts → UPDATE (status = 'scheduled')
audit_logs → INSERT (action='SCHEDULE')
```
The writer opens the approved posts list, selects a date and time for each post, and submits. The backend verifies `posts.status = 'approved'`, then calls the Buffer API with the content and schedule time. Buffer returns a `buffer_update_id` which is stored in `scheduled_posts`. The post status is updated to `'scheduled'`.

**Dependency rule:** `scheduled_posts` has a UNIQUE constraint on `post_id` — only one schedule record per post is allowed.

---

### Step 7 — Publishing and Analytics Collection
```
Buffer publishes post (external) →
posts → UPDATE (status = 'published')
analytics_logs → INSERT (post_id, views, likes, comments, shares, engagement_rate)
```
When Buffer publishes the post, the system updates `posts.status` to `'published'`. Analytics data (views, likes, comments, shares) is collected from the Buffer Analytics API or entered manually. Each analytics snapshot is a new INSERT into `analytics_logs`, so a post can have multiple records over time (daily snapshots).

---

### Step 8 — AI Weekly Recommendation
```
analytics_logs → SELECT (best performing posts in last 7 days per client)
Summary sent to AI API →
content_recommendations → INSERT (client_id, week_start_date, week_end_date, best_platform, recommendation_text)
```
The AI agent reads the last 7 days of analytics from `analytics_logs`, calculates which platform had the highest `engagement_rate`, builds a summary, and sends it to the AI API. The AI returns a recommendation text. One row is inserted into `content_recommendations` per client per week.

**Dependency rule:** `content_recommendations` depends on `clients`. A UNIQUE constraint on `(client_id, week_start_date)` prevents duplicate recommendations for the same week.

---

### Step 9 — New Cycle Begins
```
content_recommendations → SELECT (recommendation for this week)
Writer reads recommendation → creates new content_drafts row
Cycle restarts from Step 2
```
The writer reads the AI recommendation on the dashboard and creates a new draft inspired by it. The cycle repeats.

---

## Data Dependency Map

```
users ──────────────────────────┐
                                ▼
clients ─────────────────► content_drafts ──► posts ──► approvals
    │                           │                │
    ▼                           ▼                ├──► scheduled_posts
social_accounts          ai_generations          │
    │                                            └──► analytics_logs
    ▼
content_recommendations ◄─── (analytics_logs summary via AI)

audit_logs ◄──── (every write operation across all tables)
```

---

## Table Read/Write Summary

| Table | Written By | Read By |
|---|---|---|
| `users` | Registration form | Login, approvals, audit |
| `clients` | Admin setup | Draft creation, recommendations |
| `social_accounts` | Client setup form | Scheduling, Buffer API |
| `content_drafts` | Writer form | AI repurposing engine |
| `posts` | AI repurposing engine | Manager review, scheduling |
| `ai_generations` | AI repurposing engine | Debugging, cost tracking |
| `approvals` | Manager review form | Writer dashboard |
| `scheduled_posts` | Buffer API response | Publishing tracker |
| `analytics_logs` | Buffer Analytics / manual | AI agent, reporting |
| `content_recommendations` | AI agent | Writer dashboard |
| `audit_logs` | All write operations | Admin panel, compliance |

---

## What Comes Out of the System

| Output | Source Tables |
|---|---|
| Writer dashboard (draft + post status) | `content_drafts`, `posts`, `approvals` |
| Manager review queue | `posts` WHERE status = 'pending_approval' |
| Published posts report | `posts`, `scheduled_posts`, `analytics_logs` |
| Weekly AI recommendation | `content_recommendations` |
| Admin audit trail | `audit_logs` |
| Best-performing platform report | `analytics_logs` GROUP BY platform |
