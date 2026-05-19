# Normalization Walkthrough

## Project Title
AI Social Media Automation Platform

## Purpose of Normalization

Normalization is the process of organizing database tables to reduce data redundancy and improve data consistency.  
For this project, the database schema is normalized up to Third Normal Form (3NF).

The database contains the following tables:

1. USERS
2. POSTS
3. APPROVALS
4. SCHEDULED_POSTS
5. ANALYTICS_LOGS
6. AI_GENERATIONS

---

# 1. First Normal Form (1NF)

## Rule of 1NF

A table is in First Normal Form if:

- Each column contains atomic values.
- There are no repeating groups.
- Each row is uniquely identified by a primary key.
- Each column contains values of the same type.

---

## 1NF Justification

### USERS Table

The USERS table is in 1NF because each attribute contains a single atomic value.

| Attribute | Reason |
|---|---|
| user_id | Unique value for each user |
| full_name | Stores one user name |
| email | Stores one email address |
| password | Stores one password value |
| role | Stores one role value |
| created_at | Stores one date/time value |

There are no repeating groups in the USERS table.

---

### POSTS Table

The POSTS table is in 1NF because each post record stores atomic values only.

| Attribute | Reason |
|---|---|
| post_id | Unique value for each post |
| user_id | Stores one user reference |
| title | Stores one title |
| content | Stores one post content |
| ai_caption | Stores one AI caption |
| status | Stores one status value |
| created_at | Stores one date/time value |

There are no multiple values stored in a single column.

---

### APPROVALS Table

The APPROVALS table is in 1NF because each approval record contains atomic values.

| Attribute | Reason |
|---|---|
| approval_id | Unique value for each approval record |
| post_id | Stores one post reference |
| approved_by | Stores one user/admin reference |
| approval_status | Stores one approval status |
| approval_date | Stores one date/time value |

Each row represents one approval action.

---

### SCHEDULED_POSTS Table

The SCHEDULED_POSTS table is in 1NF because each row stores one scheduling record.

| Attribute | Reason |
|---|---|
| schedule_id | Unique value for each schedule record |
| post_id | Stores one post reference |
| scheduled_time | Stores one scheduled date/time |
| platform | Stores one platform name |

Each schedule record belongs to one post.

---

### ANALYTICS_LOGS Table

The ANALYTICS_LOGS table is in 1NF because each analytics record contains atomic values.

| Attribute | Reason |
|---|---|
| analytics_id | Unique value for each analytics record |
| post_id | Stores one post reference |
| views | Stores one numeric value |
| likes | Stores one numeric value |
| comments | Stores one numeric value |
| shares | Stores one numeric value |
| recorded_at | Stores one date/time value |

There are no repeated analytics values in one column.

---

### AI_GENERATIONS Table

The AI_GENERATIONS table is in 1NF because each row stores one AI generation record.

| Attribute | Reason |
|---|---|
| generation_id | Unique value for each AI generation |
| post_id | Stores one post reference |
| prompt | Stores one prompt |
| generated_text | Stores one generated response |
| generated_at | Stores one date/time value |

Each row stores one AI-generated output.

---

# 2. Second Normal Form (2NF)

## Rule of 2NF

A table is in Second Normal Form if:

- It is already in 1NF.
- Every non-key attribute depends on the full primary key.
- There is no partial dependency.

Partial dependency usually happens when a table has a composite primary key and some attributes depend only on part of that key.

---

## 2NF Justification

In this database, every table has a single-column primary key.  
Because of this, partial dependency does not exist.

---

### USERS Table

Primary Key: user_id

All non-key attributes depend completely on user_id.

| Attribute | Depends On |
|---|---|
| full_name | user_id |
| email | user_id |
| password | user_id |
| role | user_id |
| created_at | user_id |

So, USERS is in 2NF.

---

### POSTS Table

Primary Key: post_id

All non-key attributes depend completely on post_id.

| Attribute | Depends On |
|---|---|
| user_id | post_id |
| title | post_id |
| content | post_id |
| ai_caption | post_id |
| status | post_id |
| created_at | post_id |

So, POSTS is in 2NF.

---

### APPROVALS Table

Primary Key: approval_id

All non-key attributes depend completely on approval_id.

| Attribute | Depends On |
|---|---|
| post_id | approval_id |
| approved_by | approval_id |
| approval_status | approval_id |
| approval_date | approval_id |

So, APPROVALS is in 2NF.

---

### SCHEDULED_POSTS Table

Primary Key: schedule_id

All non-key attributes depend completely on schedule_id.

| Attribute | Depends On |
|---|---|
| post_id | schedule_id |
| scheduled_time | schedule_id |
| platform | schedule_id |

So, SCHEDULED_POSTS is in 2NF.

---

### ANALYTICS_LOGS Table

Primary Key: analytics_id

All non-key attributes depend completely on analytics_id.

| Attribute | Depends On |
|---|---|
| post_id | analytics_id |
| views | analytics_id |
| likes | analytics_id |
| comments | analytics_id |
| shares | analytics_id |
| recorded_at | analytics_id |

So, ANALYTICS_LOGS is in 2NF.

---

### AI_GENERATIONS Table

Primary Key: generation_id

All non-key attributes depend completely on generation_id.

| Attribute | Depends On |
|---|---|
| post_id | generation_id |
| prompt | generation_id |
| generated_text | generation_id |
| generated_at | generation_id |

So, AI_GENERATIONS is in 2NF.

---

# 3. Third Normal Form (3NF)

## Rule of 3NF

A table is in Third Normal Form if:

- It is already in 2NF.
- There is no transitive dependency.
- Non-key attributes depend only on the primary key, not on another non-key attribute.

---

## 3NF Justification

The database is in 3NF because non-key attributes do not depend on other non-key attributes.

For example:

- In POSTS, title, content, ai_caption, status, and created_at depend on post_id.
- In APPROVALS, approval_status and approval_date depend on approval_id.
- In ANALYTICS_LOGS, views, likes, comments, shares, and recorded_at depend on analytics_id.
- In AI_GENERATIONS, prompt, generated_text, and generated_at depend on generation_id.

Foreign keys are used only to create relationships between tables.

---

### USERS Table

The USERS table is in 3NF because:

- user_id identifies each user.
- full_name, email, password, role, and created_at depend only on user_id.
- No non-key attribute depends on another non-key attribute.

---

### POSTS Table

The POSTS table is in 3NF because:

- post_id identifies each post.
- user_id is a foreign key that connects the post to the user.
- title, content, ai_caption, status, and created_at depend only on post_id.
- User details are not stored inside POSTS, so redundancy is avoided.

---

### APPROVALS Table

The APPROVALS table is in 3NF because:

- approval_id identifies each approval record.
- post_id connects approval to a post.
- approved_by connects approval to the admin/user who approved it.
- approval_status and approval_date depend only on approval_id.
- Post details and user details are not repeated in this table.

---

### SCHEDULED_POSTS Table

The SCHEDULED_POSTS table is in 3NF because:

- schedule_id identifies each scheduled post record.
- post_id connects the schedule to a post.
- scheduled_time and platform depend only on schedule_id.
- Post content is not repeated in this table.

---

### ANALYTICS_LOGS Table

The ANALYTICS_LOGS table is in 3NF because:

- analytics_id identifies each analytics record.
- post_id connects analytics to a post.
- views, likes, comments, shares, and recorded_at depend only on analytics_id.
- Post details are not repeated in this table.

---

### AI_GENERATIONS Table

The AI_GENERATIONS table is in 3NF because:

- generation_id identifies each AI generation record.
- post_id connects AI generation history to a post.
- prompt, generated_text, and generated_at depend only on generation_id.
- Post details are not repeated in this table.

---

# Final Normalized Tables

After normalization, the final tables are:

| Table | Primary Key | Foreign Keys |
|---|---|---|
| USERS | user_id | None |
| POSTS | post_id | user_id |
| APPROVALS | approval_id | post_id, approved_by |
| SCHEDULED_POSTS | schedule_id | post_id |
| ANALYTICS_LOGS | analytics_id | post_id |
| AI_GENERATIONS | generation_id | post_id |

---

# Relationship Summary

| Relationship | Type | Description |
|---|---|---|
| USERS to POSTS | One-to-Many | One user can create many posts |
| POSTS to APPROVALS | One-to-Many | One post can have many approval records |
| USERS to APPROVALS | One-to-Many | One admin can approve many approval records |
| POSTS to SCHEDULED_POSTS | One-to-One | One post can have one schedule record |
| POSTS to ANALYTICS_LOGS | One-to-Many | One post can have many analytics records |
| POSTS to AI_GENERATIONS | One-to-Many | One post can have many AI generation records |

---

# Conclusion

The AI Social Media Automation Platform database is normalized up to Third Normal Form.

The schema avoids:

- Repeating groups
- Partial dependency
- Transitive dependency
- Unnecessary data duplication

This makes the database more consistent, organized, and suitable for a full working SaaS-style project.