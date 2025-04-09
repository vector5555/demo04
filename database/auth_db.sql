/*
 Navicat Premium Dump SQL

 Source Server         : mysql
 Source Server Type    : MySQL
 Source Server Version : 80040 (8.0.40)
 Source Host           : localhost:3306
 Source Schema         : auth_db

 Target Server Type    : MySQL
 Target Server Version : 80040 (8.0.40)
 File Encoding         : 65001

 Date: 09/04/2025 18:30:27
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for role_permissions
-- ----------------------------
DROP TABLE IF EXISTS `role_permissions`;
CREATE TABLE `role_permissions`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_id` int NOT NULL,
  `db_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `table_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `field_list` json NULL,
  `field_info` json NULL,
  `where_clause` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unique_role_table`(`role_id` ASC, `db_name` ASC, `table_name` ASC) USING BTREE,
  CONSTRAINT `role_permissions_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 23 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of role_permissions
-- ----------------------------
INSERT INTO `role_permissions` VALUES (17, 2, 'air', 'envom_origin', '[\"AQ\", \"AQG\", \"AQI\", \"CDMC\", \"CYRQ\", \"GNQLB\", \"JCQ\", \"KZJB\", \"NO2\", \"O3\", \"OBJECTID\", \"PM\", \"PM25\", \"SO2\", \"X_ORIG\", \"Y_ORIG\", \"YEAR\", \"DWDM\", \"DWLX\", \"CO\", \"FID\", \"SYWRW\"]', '[{\"name\": \"FID\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"OBJECTID\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"YEAR\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"年份\"}, {\"name\": \"SO2\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"二氧化硫浓度\"}, {\"name\": \"NO2\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"氮氧化物浓度\"}, {\"name\": \"PM\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"PM10浓度\"}, {\"name\": \"CO\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"一氧化碳浓度\"}, {\"name\": \"O3\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"臭氧浓度\"}, {\"name\": \"PM25\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"PM2.5浓度\"}, {\"name\": \"AQI\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"空气质量指数\"}, {\"name\": \"AQ\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"空气质量级别（优良中差）\"}, {\"name\": \"AQG\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"空气质量等级（一级、二级、三级）\"}, {\"name\": \"SYWRW\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"首要污染物\"}, {\"name\": \"JCQ\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"监测区\"}, {\"name\": \"X_ORIG\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"监测点经度\"}, {\"name\": \"Y_ORIG\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"监测点纬度\"}, {\"name\": \"KZJB\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"控制级别（国控、省控、市控、区控）\"}, {\"name\": \"DWLX\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"点位类型\"}, {\"name\": \"GNQLB\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"DWDM\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"CDMC\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"测点名称\"}, {\"name\": \"CYRQ\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"采样日期\"}]', '1=1', '2025-04-01 23:27:13', '2025-04-01 23:27:13');
INSERT INTO `role_permissions` VALUES (18, 2, 'air', 'envom_point', '[\"id\", \"year\", \"pm25\", \"aq\", \"area\", \"longitude\", \"latitude\", \"code\", \"name\", \"create_time\"]', '[{\"name\": \"id\", \"type\": \"BIGINT\", \"comment\": \"\"}, {\"name\": \"year\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"pm25\", \"type\": \"DOUBLE\", \"comment\": \"\"}, {\"name\": \"aq\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"area\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"longitude\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"latitude\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"code\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"name\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"create_time\", \"type\": \"DATETIME\", \"comment\": \"\"}]', '1=1', '2025-04-01 23:27:13', '2025-04-01 23:27:13');
INSERT INTO `role_permissions` VALUES (22, 1, 'air', 'envom_origin', '[\"FID\", \"OBJECTID\", \"YEAR\", \"SO2\", \"NO2\", \"PM\", \"CO\", \"O3\", \"PM25\", \"AQ\", \"AQG\", \"SYWRW\", \"ID\", \"X_ORIG\", \"Y_ORIG\", \"X\", \"Y\", \"KZJB\", \"DWLX\", \"GNQLB\", \"Notes\", \"DWDM\", \"CDMC\", \"CYRQ\", \"JCQ\"]', '[{\"name\": \"FID\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"OBJECTID\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"YEAR\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"年份\"}, {\"name\": \"SO2\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"二氧化硫浓度\"}, {\"name\": \"NO2\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"氮氧化物浓度\"}, {\"name\": \"PM\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"PM10浓度\"}, {\"name\": \"CO\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"一氧化碳浓度\"}, {\"name\": \"O3\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"臭氧浓度\"}, {\"name\": \"PM25\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"PM2.5浓度\"}, {\"name\": \"AQ\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"空气质量级别（优良中差）\"}, {\"name\": \"AQG\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"空气质量等级（一级、二级、三级）\"}, {\"name\": \"SYWRW\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"首要污染物\"}, {\"name\": \"ID\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"JCQ\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"监测区\"}, {\"name\": \"X_ORIG\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"监测点经度\"}, {\"name\": \"Y_ORIG\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"监测点纬度\"}, {\"name\": \"X\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"Y\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"KZJB\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"控制级别（国控、省控、市控、区控）\"}, {\"name\": \"DWLX\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"点位类型\"}, {\"name\": \"GNQLB\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"Notes\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"DWDM\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"\"}, {\"name\": \"CDMC\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"测点名称\"}, {\"name\": \"CYRQ\", \"type\": \"VARCHAR(255) COLLATE \\\"utf8mb4_general_ci\\\"\", \"comment\": \"采样日期\"}]', 'KZJB= \'国控\'', '2025-04-08 00:10:40', '2025-04-08 00:10:40');

-- ----------------------------
-- Table structure for roles
-- ----------------------------
DROP TABLE IF EXISTS `roles`;
CREATE TABLE `roles`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `role_name`(`role_name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of roles
-- ----------------------------
INSERT INTO `roles` VALUES (1, 'admin', '系统管理员，拥有所有权限', '2025-03-28 20:05:45', '2025-03-28 20:05:45');
INSERT INTO `roles` VALUES (2, 'jimei_user', '集美区用户，只能查询集美区的数据', '2025-03-28 22:01:46', '2025-03-28 22:02:01');

-- ----------------------------
-- Table structure for user_roles
-- ----------------------------
DROP TABLE IF EXISTS `user_roles`;
CREATE TABLE `user_roles`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `role_id` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unique_user_role`(`user_id` ASC, `role_id` ASC) USING BTREE,
  INDEX `role_id`(`role_id` ASC) USING BTREE,
  CONSTRAINT `user_roles_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `user_roles_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 12 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user_roles
-- ----------------------------
INSERT INTO `user_roles` VALUES (5, 6, 2, '2025-03-31 15:11:39');
INSERT INTO `user_roles` VALUES (9, 3, 1, '2025-03-31 19:53:25');
INSERT INTO `user_roles` VALUES (11, 5, 2, '2025-04-02 22:39:34');

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES (3, 'admin', '$2b$12$hitqUf3YGlG02G6EGuzrOO6ZpVge/vd5eDyAq7YeqNS075jKYxLyC', '2025-03-27 21:30:57');
INSERT INTO `users` VALUES (5, 'test1', '$2b$12$hitqUf3YGlG02G6EGuzrOO6ZpVge/vd5eDyAq7YeqNS075jKYxLyC', '2025-03-28 21:42:25');
INSERT INTO `users` VALUES (6, 'test2', '$2b$12$hitqUf3YGlG02G6EGuzrOO6ZpVge/vd5eDyAq7YeqNS075jKYxLyC', '2025-03-28 21:43:12');
INSERT INTO `users` VALUES (7, 'test3', '$2b$12$0jQrMSHU9bBbgvePhtC3fO8Qhjwiv5r6Z/EUkgGqYTLjJankqtgP6', '2025-04-05 10:00:57');
INSERT INTO `users` VALUES (8, 'test4', '$2b$12$0jQrMSHU9bBbgvePhtC3fO8Qhjwiv5r6Z/EUkgGqYTLjJankqtgP6', '2025-04-05 10:11:20');

SET FOREIGN_KEY_CHECKS = 1;
