CREATE TABLE IF NOT EXISTS `blacklist` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `group_id` BIGINT NOT NULL,
    `trigger` VARCHAR(255) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`group_id`) REFERENCES `groups_`(`telegram_id`) ON DELETE CASCADE,
    UNIQUE KEY `uq_blacklist_group_trigger` (`group_id`, `trigger`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
