
CREATE TABLE `nested_a` (
  `id` bigint(20) unsigned NOT NULL,
  `foo` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL,
  `parent_id` bigint(20) unsigned DEFAULT NULL COMMENT 'Adjacency list involves a simple child -> parent ref',
  PRIMARY KEY (`id`),
  KEY `IDX_nested_a_parent_id` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ROW_FORMAT=COMPRESSED COMMENT='Adjacency list nesting';

CREATE TABLE `nested_b` (
  `id` bigint(20) unsigned NOT NULL,
  `foo` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL,
  `path` varchar(64) COLLATE utf8mb4_bin NOT NULL COMMENT 'Materialized path contains string repr of reference chainall the way to top node',
  PRIMARY KEY (`id`),
  KEY `IDX_nested_b_path` (`path`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ROW_FORMAT=COMPRESSED COMMENT='Materialized path nesting';

-- nested set model
-- doesn't seem a great fit for my use case, querying for all children given a parent is awkward and all those updates on any insert...
