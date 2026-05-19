# Dataflow Description

## Project Title
AI Social Media Automation Platform

## Purpose
This document explains how data moves through the system from user registration to post creation, AI generation, approval, scheduling, and analytics tracking.

## Dataflow Steps

### 1. User Registration
A user account is created and stored in the USERS table. Each user has a role such as admin, manager, or content_creator.

### 2. Post Creation
A content creator creates a social media post. The post title, content, status, and creator reference are stored in the POSTS table.

### 3. AI Caption Generation
When the user requests AI help, the system sends the prompt to the AI service. The generated text is stored in the AI_GENERATIONS table. The selected caption can also be saved in the ai_caption field of the POSTS table.

### 4. Approval Workflow
A post can be sent for approval. Admin or manager users approve or reject the post. Each approval action is stored in the APPROVALS table with post_id and approved_by references.

### 5. Scheduling
After approval, the post can be scheduled for a specific platform and time. Scheduling data is stored in the SCHEDULED_POSTS table.

### 6. Analytics Tracking
After a post is published, performance metrics such as views, likes, comments, and shares are stored in the ANALYTICS_LOGS table. Multiple analytics records can exist for the same post over time.

## Dataflow Summary
USERS → POSTS → AI_GENERATIONS → APPROVALS → SCHEDULED_POSTS → ANALYTICS_LOGS

## CSV Files Generated
- users.csv
- posts.csv
- approvals.csv
- scheduled_posts.csv
- analytics_logs.csv
- ai_generations.csv
