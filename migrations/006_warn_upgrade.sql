ALTER TABLE `group_settings` ADD COLUMN `warn_action` VARCHAR(10) NOT NULL DEFAULT 'ban';

CREATE TABLE IF NOT EXISTS `warn_filters` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `group_id` BIGINT NOT NULL,
    `keyword` VARCHAR(255) NOT NULL,
    `reply` VARCHAR(512) DEFAULT '',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`group_id`) REFERENCES `groups_`(`telegram_id`) ON DELETE CASCADE,
    UNIQUE KEY `uq_warnfilter_group_keyword` (`group_id`, `keyword`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
