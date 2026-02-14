CREATE TABLE IF NOT EXISTS `rss_feeds` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `chat_id` BIGINT NOT NULL,
    `feed_link` VARCHAR(512) NOT NULL,
    `old_entry_link` VARCHAR(512) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_rss_chat_link` (`chat_id`, `feed_link`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
