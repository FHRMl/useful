CREATE DATABASE IF NOT EXISTS coursekg
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE coursekg;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64) NOT NULL UNIQUE,
  display_name VARCHAR(80) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS course_reviews (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  course_id VARCHAR(64) NOT NULL,
  rating INT NOT NULL,
  comment TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT uq_review_user_course UNIQUE (user_id, course_id),
  CONSTRAINT ck_review_rating CHECK (rating BETWEEN 1 AND 5),
  INDEX idx_reviews_course (course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS knowledge_annotations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  knowledge_id VARCHAR(64) NOT NULL,
  note TEXT NOT NULL,
  visibility VARCHAR(16) NOT NULL DEFAULT 'private',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_annotations_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT ck_annotation_visibility CHECK (visibility IN ('private', 'public')),
  INDEX idx_annotations_knowledge (knowledge_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO users (id, username, display_name, password_hash, created_at) VALUES
  (1, 'sim_user_a', '周同学', 'pbkdf2_sha256$260000$a1b2c3d4e5f60708$ZHCsgA2Pb1vPNs4EGKL9PgF99H9rTQAQB4YbFoJz2LY=', NOW()),
  (2, 'sim_user_b', '李同学', 'pbkdf2_sha256$260000$b1c2d3e4f5061728$3n3fjXDvK+UXLz5x1Ec/arP+yBFMkABLrPudqHyVMpM=', NOW()),
  (3, 'sim_user_c', '陈同学', 'pbkdf2_sha256$260000$c1d2e3f405162738$723hwq4ktf1N9uqLCkDQOzAsZ8KLweZ8aZTcrCfrghY=', NOW())
ON DUPLICATE KEY UPDATE
  display_name = VALUES(display_name),
  password_hash = VALUES(password_hash);

INSERT INTO course_reviews (user_id, course_id, rating, comment) VALUES
  (1, 'COURSE_INFO_ORGANIZATION', 5, '本体、分类法和主题词表之间的关系很清晰，适合做知识图谱入口。'),
  (1, 'COURSE_INFO_RETRIEVAL', 4, '检索模型和用户需求分析对后续系统设计帮助很大。'),
  (1, 'COURSE_DATA_STRUCTURE', 4, '图结构部分和 Neo4j 建模能形成直接关联。'),
  (2, 'COURSE_MIS', 5, '业务流程、数据库和系统分析适合支撑社区系统需求建模。'),
  (2, 'COURSE_DATA_SCIENCE', 4, '数据清洗和建模内容适合扩展学习分析模块。'),
  (2, 'COURSE_INFO_ANALYSIS', 5, '指标体系和文本挖掘适合做分析展示页。'),
  (3, 'COURSE_INFO_ORGANIZATION', 4, '中图法分类号和主题词关系适合用于课程知识组织。'),
  (3, 'COURSE_MIS', 4, '信息系统和决策支持内容能解释 Web 系统设计。'),
  (3, 'COURSE_INFO_RETRIEVAL', 5, '布尔检索、相关排序和搜索体验在图谱页面可直接体现。')
ON DUPLICATE KEY UPDATE
  rating = VALUES(rating),
  comment = VALUES(comment);

INSERT INTO knowledge_annotations (user_id, knowledge_id, note, visibility) VALUES
  (1, 'KP_THESAURUS', '主题词表可作为课程知识点标准化命名依据。', 'public'),
  (1, 'KP_GRAPH_STRUCTURE', '图结构可映射为课程-知识点-分类节点的边。', 'private'),
  (2, 'KP_BUSINESS_PROCESS', '可在报告中解释为用户评价流程和标注流程。', 'public'),
  (2, 'KP_DATA_VISUALIZATION', '分析展示页适合用条形图和图谱联动。', 'public'),
  (3, 'KP_RELEVANCE_RANKING', '搜索结果可按匹配节点度数或类型加权排序。', 'private'),
  (3, 'KP_METADATA', '课程代码、学分、分类号都属于课程元数据。', 'public');

