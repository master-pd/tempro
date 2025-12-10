-- Tempro Bot Database Schema
-- Version: 2.0.0
-- Created: 2024-01-01

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT,
    language_code TEXT DEFAULT 'en',
    is_bot BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_count INTEGER DEFAULT 0,
    is_pirjada BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    pirjada_expiry TIMESTAMP,
    pirjada_token TEXT,
    settings TEXT DEFAULT '{}'
);

-- Emails table
CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    email_address TEXT UNIQUE NOT NULL,
    login TEXT NOT NULL,
    domain TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    message_count INTEGER DEFAULT 0,
    last_checked TIMESTAMP,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    message_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    subject TEXT,
    body_preview TEXT,
    received_at TIMESTAMP NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    raw_data TEXT,
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE
);

-- Pirjada bots table
CREATE TABLE IF NOT EXISTS pirjada_bots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    bot_token TEXT UNIQUE NOT NULL,
    bot_username TEXT NOT NULL,
    bot_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    channel_id INTEGER,
    custom_menu TEXT,
    expiry_date TIMESTAMP NOT NULL,
    settings TEXT DEFAULT '{}',
    stats TEXT DEFAULT '{}',
    FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Statistics table
CREATE TABLE IF NOT EXISTS statistics (
    date DATE PRIMARY KEY,
    total_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    emails_created INTEGER DEFAULT 0,
    messages_received INTEGER DEFAULT 0,
    pirjada_bots_created INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0
);

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- User actions table (bans, warnings, etc.)
CREATE TABLE IF NOT EXISTS user_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    performed_by INTEGER NOT NULL,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (performed_by) REFERENCES users(user_id)
);

-- Broadcast history table
CREATE TABLE IF NOT EXISTS broadcast_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    broadcast_id TEXT UNIQUE NOT NULL,
    message_preview TEXT NOT NULL,
    total_users INTEGER NOT NULL,
    success_count INTEGER NOT NULL,
    failed_count INTEGER NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_by INTEGER NOT NULL,
    FOREIGN KEY (sent_by) REFERENCES users(user_id)
);

-- Email domains table
CREATE TABLE IF NOT EXISTS email_domains (
    domain TEXT PRIMARY KEY,
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active);
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);
CREATE INDEX IF NOT EXISTS idx_users_is_pirjada ON users(is_pirjada);

CREATE INDEX IF NOT EXISTS idx_emails_user ON emails(user_id);
CREATE INDEX IF NOT EXISTS idx_emails_expires ON emails(expires_at);
CREATE INDEX IF NOT EXISTS idx_emails_is_active ON emails(is_active);
CREATE INDEX IF NOT EXISTS idx_emails_created ON emails(created_at);

CREATE INDEX IF NOT EXISTS idx_messages_email ON messages(email_id);
CREATE INDEX IF NOT EXISTS idx_messages_received ON messages(received_at);

CREATE INDEX IF NOT EXISTS idx_pirjada_owner ON pirjada_bots(owner_id);
CREATE INDEX IF NOT EXISTS idx_pirjada_expiry ON pirjada_bots(expiry_date);
CREATE INDEX IF NOT EXISTS idx_pirjada_is_active ON pirjada_bots(is_active);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_actions_user ON user_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_actions_timestamp ON user_actions(timestamp);

CREATE INDEX IF NOT EXISTS idx_broadcast_sent_at ON broadcast_history(sent_at);

-- Default settings
INSERT OR IGNORE INTO settings (key, value, description) VALUES 
    ('bot_version', '2.0.0', 'Current bot version'),
    ('maintenance_mode', 'false', 'Maintenance mode status'),
    ('rate_limit_per_minute', '5', 'Rate limit per minute per user'),
    ('max_emails_per_user', '10', 'Maximum emails per user'),
    ('email_expiry_hours', '1', 'Email expiry time in hours'),
    ('pirjada_max_bots', '3', 'Maximum bots per pirjada'),
    ('pirjada_expiry_days', '30', 'Pirjada access expiry days'),
    ('backup_interval_hours', '24', 'Automatic backup interval'),
    ('max_backup_files', '30', 'Maximum backup files to keep'),
    ('cleanup_days', '30', 'Days before cleaning inactive users');

-- Insert default email domains
INSERT OR IGNORE INTO email_domains (domain, is_active) VALUES 
    ('1secmail.com', 1),
    ('1secmail.org', 1),
    ('1secmail.net', 1),
    ('wwjmp.com', 1),
    ('esiix.com', 1),
    ('xojxe.com', 1),
    ('yoggm.com', 1);

-- Views
CREATE VIEW IF NOT EXISTS vw_user_stats AS
SELECT 
    u.user_id,
    u.username,
    u.first_name,
    u.email_count,
    u.created_at,
    u.last_active,
    COUNT(DISTINCT e.id) as active_emails,
    COALESCE(SUM(e.message_count), 0) as total_messages
FROM users u
LEFT JOIN emails e ON u.user_id = e.user_id AND e.is_active = 1
GROUP BY u.user_id;

CREATE VIEW IF NOT EXISTS vw_daily_stats AS
SELECT 
    date,
    total_users,
    new_users,
    emails_created,
    messages_received,
    pirjada_bots_created,
    active_users,
    ROUND(CAST(active_users AS FLOAT) / total_users * 100, 2) as activity_rate
FROM statistics
ORDER BY date DESC;

-- Triggers
CREATE TRIGGER IF NOT EXISTS trg_update_user_email_count
AFTER INSERT ON emails
BEGIN
    UPDATE users 
    SET email_count = email_count + 1 
    WHERE user_id = NEW.user_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_update_email_message_count
AFTER INSERT ON messages
BEGIN
    UPDATE emails 
    SET message_count = message_count + 1,
        last_checked = CURRENT_TIMESTAMP
    WHERE id = NEW.email_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_update_last_active
AFTER UPDATE ON users
WHEN NEW.last_active != OLD.last_active
BEGIN
    UPDATE users 
    SET last_active = CURRENT_TIMESTAMP 
    WHERE user_id = NEW.user_id;
END;

-- Functions (SQLite doesn't support stored functions directly)
-- These would be implemented in Python code

COMMIT;