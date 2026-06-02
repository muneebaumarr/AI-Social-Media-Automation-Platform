CREATE DATABASE IF NOT EXISTS ai_social_media_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ai_social_media_db;

CREATE TABLE users (
    user_id       CHAR(36)        NOT NULL DEFAULT (UUID()),
    full_name     VARCHAR(120)    NOT NULL,
    email         VARCHAR(180)    NOT NULL,
    password_hash VARCHAR(255)    NOT NULL,
    role          ENUM('writer','manager','admin','client')
                                  NOT NULL DEFAULT 'writer',
    created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_users           PRIMARY KEY (user_id),
    CONSTRAINT uq_users_email     UNIQUE      (email),
    CONSTRAINT chk_users_email    CHECK       (email LIKE '%@%.%')
);

CREATE INDEX idx_users_role  ON users (role);
CREATE INDEX idx_users_email ON users (email);

-- clients --Stores brand / client profiles. --Every piece of content belongs to a client

CREATE TABLE clients (
    client_id     CHAR(36)        NOT NULL DEFAULT (UUID()),
    client_name   VARCHAR(150)    NOT NULL,
    timezone      VARCHAR(60)     NOT NULL DEFAULT 'UTC',
    active_status TINYINT(1)      NOT NULL DEFAULT 1,
    created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_clients         PRIMARY KEY (client_id),
    CONSTRAINT uq_clients_name    UNIQUE      (client_name),
    CONSTRAINT chk_clients_status CHECK       (active_status IN (0, 1))
);

-- social_accounts  -- Connected social media profiles per client.

CREATE TABLE social_accounts (
    account_id        CHAR(36)    NOT NULL DEFAULT (UUID()),
    client_id         CHAR(36)    NOT NULL,
    platform          ENUM('instagram','linkedin','facebook',
                           'twitter','tiktok','youtube')
                                  NOT NULL,
    account_name      VARCHAR(120) NOT NULL,
    connected_status  TINYINT(1)  NOT NULL DEFAULT 1,
    buffer_profile_id VARCHAR(100) NULL,
    connected_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_social_accounts  PRIMARY KEY (account_id),
    CONSTRAINT fk_sa_client        FOREIGN KEY (client_id)
                                   REFERENCES  clients(client_id)
                                   ON DELETE CASCADE
                                   ON UPDATE CASCADE,
    CONSTRAINT uq_sa_client_platform
                                   UNIQUE (client_id, platform),
    CONSTRAINT chk_sa_status       CHECK  (connected_status IN (0, 1))
);

CREATE INDEX idx_sa_client_id ON social_accounts (client_id);
CREATE INDEX idx_sa_platform  ON social_accounts (platform);

-- content_drafts
--  Original content written by a user for a specific client.
--    One draft → many platform-specific posts.

CREATE TABLE content_drafts (
    draft_id      CHAR(36)        NOT NULL DEFAULT (UUID()),
    client_id     CHAR(36)        NOT NULL,
    created_by    CHAR(36)        NOT NULL,
    draft_title   VARCHAR(200)    NOT NULL,
    draft_content TEXT            NOT NULL,
    draft_status  ENUM('draft','submitted','repurposed','archived')
                                  NOT NULL DEFAULT 'draft',
    created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_content_drafts   PRIMARY KEY (draft_id),
    CONSTRAINT fk_cd_client        FOREIGN KEY (client_id)
                                   REFERENCES  clients(client_id)
                                   ON DELETE CASCADE
                                   ON UPDATE CASCADE,
    CONSTRAINT fk_cd_user          FOREIGN KEY (created_by)
                                   REFERENCES  users(user_id)
                                   ON DELETE RESTRICT
                                   ON UPDATE CASCADE,
    CONSTRAINT chk_cd_title_len    CHECK (CHAR_LENGTH(draft_title) >= 3)
);

CREATE INDEX idx_cd_client_id   ON content_drafts (client_id);
CREATE INDEX idx_cd_created_by  ON content_drafts (created_by);
CREATE INDEX idx_cd_status      ON content_drafts (draft_status);

-- posts
--    AI-repurposed platform-specific versions of a draft.
--    Central workflow table — linked to approvals, scheduling,
--    and analytics.

CREATE TABLE posts (
    post_id             CHAR(36)   NOT NULL DEFAULT (UUID()),
    draft_id            CHAR(36)   NOT NULL,
    platform            ENUM('instagram','linkedin','facebook',
                             'twitter','tiktok','youtube')
                                   NOT NULL,
    repurposed_content  TEXT       NOT NULL,
    caption             TEXT       NULL,
    hashtags            TEXT       NULL,
    status              ENUM('pending_approval','approved',
                             'rejected','request_edit',
                             'scheduled','published')
                                   NOT NULL DEFAULT 'pending_approval',
    created_at          TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_posts       PRIMARY KEY (post_id),
    CONSTRAINT fk_posts_draft FOREIGN KEY (draft_id)
                              REFERENCES  content_drafts(draft_id)
                              ON DELETE CASCADE
                              ON UPDATE CASCADE
);


CREATE INDEX idx_posts_draft_id ON posts (draft_id);
CREATE INDEX idx_posts_status   ON posts (status);
CREATE INDEX idx_posts_platform ON posts (platform);

-- ai_generations
--    Audit trail for every prompt sent to the AI and the response received.

CREATE TABLE ai_generations (
    generation_id  CHAR(36)    NOT NULL DEFAULT (UUID()),
    draft_id       CHAR(36)    NOT NULL,
    platform       ENUM('instagram','linkedin','facebook',
                        'twitter','tiktok','youtube')
                               NOT NULL,
    prompt         TEXT        NOT NULL,
    generated_text TEXT        NOT NULL,
    generated_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_ai_generations PRIMARY KEY (generation_id),
    CONSTRAINT fk_ag_draft       FOREIGN KEY (draft_id)
                                 REFERENCES  content_drafts(draft_id)
                                 ON DELETE CASCADE
                                 ON UPDATE CASCADE
);

CREATE INDEX idx_ag_draft_id ON ai_generations (draft_id);

-- approvals
--    Manager review actions on posts.
--    A post can have multiple approval records over time
--    (e.g., rejected → request_edit → approved).

CREATE TABLE approvals (
    approval_id     CHAR(36)   NOT NULL DEFAULT (UUID()),
    post_id         CHAR(36)   NOT NULL,
    manager_id      CHAR(36)   NOT NULL,
    approval_status ENUM('approved','rejected','request_edit')
                               NOT NULL,
    remarks         TEXT       NULL,
    approval_date   TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_approvals        PRIMARY KEY (approval_id),
    CONSTRAINT fk_appr_post        FOREIGN KEY (post_id)
                                   REFERENCES  posts(post_id)
                                   ON DELETE CASCADE
                                   ON UPDATE CASCADE,
    CONSTRAINT fk_appr_manager     FOREIGN KEY (manager_id)
                                   REFERENCES  users(user_id)
                                   ON DELETE RESTRICT
                                   ON UPDATE CASCADE
);

CREATE INDEX idx_appr_post_id    ON approvals (post_id);
CREATE INDEX idx_appr_manager_id ON approvals (manager_id);
CREATE INDEX idx_appr_status     ON approvals (approval_status);

-- scheduled_posts
--    Buffer scheduling records for approved posts.
--    One-to-one with posts (one approved post = one schedule).


CREATE TABLE scheduled_posts (
    schedule_id      CHAR(36)   NOT NULL DEFAULT (UUID()),
    post_id          CHAR(36)   NOT NULL,
    buffer_update_id VARCHAR(120) NULL,
    scheduled_time   DATETIME   NOT NULL,
    schedule_status  ENUM('pending','sent','failed','cancelled')
                                NOT NULL DEFAULT 'pending',
    created_at       TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_scheduled_posts  PRIMARY KEY (schedule_id),
    CONSTRAINT fk_sp_post          FOREIGN KEY (post_id)
                                   REFERENCES  posts(post_id)
                                   ON DELETE CASCADE
                                   ON UPDATE CASCADE,
    CONSTRAINT uq_sp_post_id       UNIQUE (post_id),
    CONSTRAINT chk_sp_time         CHECK  (scheduled_time > '2024-01-01 00:00:00')
);

CREATE INDEX idx_sp_post_id        ON scheduled_posts (post_id);
CREATE INDEX idx_sp_scheduled_time ON scheduled_posts (scheduled_time);

-- analytics_logs
--    Performance data per post over time.
--    engagement_rate is stored (not computed) for historical
--    accuracy — a post's metric at a point in time is fixed.

CREATE TABLE analytics_logs (
    analytics_id    CHAR(36)   NOT NULL DEFAULT (UUID()),
    post_id         CHAR(36)   NOT NULL,
    views           INT        NOT NULL DEFAULT 0,
    likes           INT        NOT NULL DEFAULT 0,
    comments        INT        NOT NULL DEFAULT 0,
    shares          INT        NOT NULL DEFAULT 0,
    engagement_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    recorded_at     TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_analytics_logs   PRIMARY KEY (analytics_id),
    CONSTRAINT fk_al_post          FOREIGN KEY (post_id)
                                   REFERENCES  posts(post_id)
                                   ON DELETE CASCADE
                                   ON UPDATE CASCADE,
    CONSTRAINT chk_al_views        CHECK (views    >= 0),
    CONSTRAINT chk_al_likes        CHECK (likes    >= 0),
    CONSTRAINT chk_al_comments     CHECK (comments >= 0),
    CONSTRAINT chk_al_shares       CHECK (shares   >= 0),
    CONSTRAINT chk_al_engagement   CHECK (engagement_rate BETWEEN 0.00 AND 100.00)
);

CREATE INDEX idx_al_post_id     ON analytics_logs (post_id);
CREATE INDEX idx_al_recorded_at ON analytics_logs (recorded_at);


-- content_recommendations
--     Weekly AI-generated content plans per client,
--     based on analytics performance.

CREATE TABLE content_recommendations (
    recommendation_id  CHAR(36)  NOT NULL DEFAULT (UUID()),
    client_id          CHAR(36)  NOT NULL,
    week_start_date    DATE      NOT NULL,
    week_end_date      DATE      NOT NULL,
    best_platform      ENUM('instagram','linkedin','facebook',
                            'twitter','tiktok','youtube')
                                 NOT NULL,
    recommendation_text TEXT     NOT NULL,
    created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_content_recs      PRIMARY KEY (recommendation_id),
    CONSTRAINT fk_cr_client         FOREIGN KEY (client_id)
                                    REFERENCES  clients(client_id)
                                    ON DELETE CASCADE
                                    ON UPDATE CASCADE,
    CONSTRAINT chk_cr_dates         CHECK (week_end_date > week_start_date),
    CONSTRAINT uq_cr_client_week    UNIQUE (client_id, week_start_date)
);

CREATE INDEX idx_cr_client_id ON content_recommendations (client_id);

-- audit_logs
--     Immutable record of every important system action.


CREATE TABLE audit_logs (
    log_id      CHAR(36)     NOT NULL DEFAULT (UUID()),
    user_id     CHAR(36)     NULL,
    action      VARCHAR(100) NOT NULL,
    entity_name VARCHAR(80)  NOT NULL,
    entity_id   CHAR(36)     NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_audit_logs PRIMARY KEY (log_id),
    CONSTRAINT fk_al_user    FOREIGN KEY (user_id)
                             REFERENCES  users(user_id)
                             ON DELETE SET NULL
                             ON UPDATE CASCADE
);

CREATE INDEX idx_audit_user_id    ON audit_logs (user_id);
CREATE INDEX idx_audit_entity     ON audit_logs (entity_name, entity_id);
CREATE INDEX idx_audit_created_at ON audit_logs (created_at);

select * from analytics_logs;


SELECT user_id, full_name, email, role FROM users 
WHERE email = 'test@example.com';

-- ─── 1. Add brand identity columns to clients ──────────
ALTER TABLE clients
    ADD COLUMN owner_id        CHAR(36)     NULL AFTER client_id,
    ADD COLUMN industry        VARCHAR(100) NULL,
    ADD COLUMN brand_voice     TEXT         NULL,
    ADD COLUMN target_audience TEXT         NULL,
    ADD COLUMN brand_color     VARCHAR(7)   DEFAULT '#0a0a0a',
    ADD COLUMN do_not_use      TEXT         NULL,
    ADD COLUMN invite_code     VARCHAR(8)   NULL;

ALTER TABLE clients
    ADD CONSTRAINT fk_clients_owner
    FOREIGN KEY (owner_id) REFERENCES users(user_id)
    ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE clients
    ADD UNIQUE INDEX uq_invite_code (invite_code);

-- ─── 2. Create client_members table ────────────────────
-- This is the multi-tenancy bridge.
-- Maps which writers/managers belong to which brand.
CREATE TABLE client_members (
    membership_id CHAR(36)    NOT NULL DEFAULT (UUID()),
    client_id     CHAR(36)    NOT NULL,
    user_id       CHAR(36)    NOT NULL,
    member_role   ENUM('writer','manager') NOT NULL DEFAULT 'writer',
    added_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_client_members   PRIMARY KEY (membership_id),
    CONSTRAINT fk_cm_client        FOREIGN KEY (client_id)
                                   REFERENCES  clients(client_id)
                                   ON DELETE CASCADE,
    CONSTRAINT fk_cm_user          FOREIGN KEY (user_id)
                                   REFERENCES  users(user_id)
                                   ON DELETE CASCADE,
    CONSTRAINT uq_cm_user_client   UNIQUE (client_id, user_id)
);

CREATE INDEX idx_cm_client ON client_members (client_id);
CREATE INDEX idx_cm_user   ON client_members (user_id);

-- ─── 3. Verify ────────────────────────────────────────
DESCRIBE clients;
DESCRIBE client_members;

SHOW COLUMNS FROM clients;
