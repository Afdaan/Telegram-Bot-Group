CREATE DATABASE IF NOT EXISTS telegram_bot
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE telegram_bot;

CREATE TABLE IF NOT EXISTS users (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id    BIGINT NOT NULL UNIQUE,
    username       VARCHAR(255),
    first_name     VARCHAR(255),
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS groups_ (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id    BIGINT NOT NULL UNIQUE,
    title          VARCHAR(255),
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS group_settings (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    group_id          BIGINT NOT NULL UNIQUE,
    warn_limit        INT DEFAULT 3,
    welcome_msg       TEXT,
    goodbye_msg       TEXT,
    rules_text        TEXT,
    antiflood_limit   INT DEFAULT 5,
    antiflood_time    INT DEFAULT 10,
    slowmode_seconds  INT DEFAULT 0,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES groups_(telegram_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS warnings (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id        BIGINT NOT NULL,
    group_id       BIGINT NOT NULL,
    reason         VARCHAR(512) DEFAULT 'No reason provided',
    warned_by      BIGINT NOT NULL,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES groups_(telegram_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sticker_packs (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    pack_name      VARCHAR(255) NOT NULL UNIQUE,
    owner_id       BIGINT NOT NULL,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(telegram_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_warnings_user_group ON warnings(user_id, group_id);
CREATE INDEX idx_sticker_packs_owner ON sticker_packs(owner_id);
