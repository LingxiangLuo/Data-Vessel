-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: portal_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `portal_db`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `portal_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `portal_db`;

--
-- Table structure for table `alert_rule`
--

DROP TABLE IF EXISTS `alert_rule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alert_rule` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  `target_type` varchar(32) NOT NULL DEFAULT 'all',
  `target_id` bigint DEFAULT NULL,
  `trigger_type` varchar(32) NOT NULL,
  `trigger_value` int DEFAULT NULL,
  `notify_type` varchar(32) NOT NULL,
  `notify_config` json NOT NULL,
  `enabled` tinyint NOT NULL DEFAULT '1',
  `created_by` bigint DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alert_rule`
--

LOCK TABLES `alert_rule` WRITE;
/*!40000 ALTER TABLE `alert_rule` DISABLE KEYS */;
/*!40000 ALTER TABLE `alert_rule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `component`
--

DROP TABLE IF EXISTS `component`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `component` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `config_json` json NOT NULL,
  `version` int NOT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ds_task_code` bigint DEFAULT NULL,
  `created_by` bigint DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `folder_id` bigint DEFAULT NULL COMMENT 'æ‰€å±žæ–‡ä»¶å¤¹id',
  `previous_status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `component`
--

LOCK TABLES `component` WRITE;
/*!40000 ALTER TABLE `component` DISABLE KEYS */;
INSERT INTO `component` VALUES (7,'extract_users_from_portal','sql','从 Portal MySQL 抽取用户表','{\"sql\": \"SELECT id, username, created_at FROM sys_user LIMIT 100;\", \"timeout\": 300, \"datasource_id\": 3}',1,'online',NULL,1,'2026-05-12 03:13:19','2026-05-12 03:13:19',NULL,NULL),(8,'transform_user_data','python','Python 数据处理示例 (打印当前时间和环境)','{\"script\": \"import datetime\\nprint(\'[transform] starting at\', datetime.datetime.now())\\nprint(\'[transform] done\')\", \"timeout\": 120}',1,'online',NULL,1,'2026-05-12 03:13:19','2026-05-12 03:13:19',NULL,NULL),(9,'cleanup_temp_files','shell','Shell 清理临时文件示例','{\"script\": \"echo \'[cleanup] start\' && date && echo \'[cleanup] done\'\", \"timeout\": 60}',1,'online',NULL,1,'2026-05-12 03:13:19','2026-05-12 03:13:20',NULL,NULL),(10,'datax_user_sync_demo','datax','DataX 用户表同步示例(streamreader→streamwriter)','{\"rawJson\": \"{\\n  \\\"job\\\": {\\n    \\\"content\\\": [\\n      {\\n        \\\"reader\\\": {\\n          \\\"name\\\": \\\"streamreader\\\",\\n          \\\"parameter\\\": {\\n            \\\"sliceRecordCount\\\": 5,\\n            \\\"column\\\": [\\n              {\\n                \\\"type\\\": \\\"string\\\",\\n                \\\"value\\\": \\\"demo-user\\\"\\n              },\\n              {\\n                \\\"type\\\": \\\"long\\\",\\n                \\\"value\\\": 100\\n              }\\n            ]\\n          }\\n        },\\n        \\\"writer\\\": {\\n          \\\"name\\\": \\\"streamwriter\\\",\\n          \\\"parameter\\\": {\\n            \\\"print\\\": true,\\n            \\\"encoding\\\": \\\"UTF-8\\\"\\n          }\\n        }\\n      }\\n    ],\\n    \\\"setting\\\": {\\n      \\\"speed\\\": {\\n        \\\"channel\\\": 1\\n      }\\n    }\\n  }\\n}\", \"timeout\": 600}',1,'online',NULL,1,'2026-05-12 03:13:20','2026-05-12 03:13:20',NULL,NULL),(11,'alert_summary_log','shell','工作流末尾汇总日志','{\"script\": \"echo \'[summary] pipeline finished\' && date && echo \'OK\'\", \"timeout\": 60}',1,'online',NULL,1,'2026-05-12 03:13:20','2026-05-12 03:13:20',NULL,NULL),(12,'temp','sql',NULL,'{}',1,'testing',NULL,1,'2026-05-12 09:22:46','2026-05-13 02:11:16',NULL,NULL),(13,'123','sql',NULL,'{\"sql\": \"SELECT * FROM ads_brand_insight_question\", \"datasource_id\": 5}',1,'online',NULL,1,'2026-05-13 01:20:24','2026-05-13 01:59:49',2,NULL),(14,'456','sql',NULL,'{\"sql\": \"\", \"datasource_id\": 5}',1,'draft',NULL,1,'2026-05-13 02:12:15','2026-05-13 02:12:15',2,NULL),(15,'789','sql',NULL,'{\"sql\": \"\", \"datasource_id\": 5}',1,'draft',NULL,1,'2026-05-13 03:09:13','2026-05-13 03:09:13',2,NULL),(16,'sync_ods_sc_gxt_prod_question_df','datax','AL_ODS → ODS: ods_sc_gxt_prod_question_df','{\"rawJson\": \"{\\\"job\\\": {\\\"content\\\": [{\\\"reader\\\": {\\\"name\\\": \\\"mysqlreader\\\", \\\"parameter\\\": {\\\"username\\\": \\\"data_devops\\\", \\\"password\\\": \\\"devops_2023!\\\", \\\"column\\\": [\\\"id\\\", \\\"tenant_name\\\", \\\"brand\\\", \\\"scene_type\\\", \\\"seq_no\\\", \\\"question\\\", \\\"gmt_create\\\", \\\"gmt_modified\\\", \\\"dt\\\"], \\\"connection\\\": [{\\\"table\\\": [\\\"ods_sc_gxt_prod_question_df\\\"], \\\"jdbcUrl\\\": [\\\"jdbc:mysql://rm-8vb0aam8k3g0pi3gsmo.mysql.zhangbei.rds.aliyuncs.com:3306/taiji_terminal_digital?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai\\\"]}]}}, \\\"writer\\\": {\\\"name\\\": \\\"mysqlwriter\\\", \\\"parameter\\\": {\\\"username\\\": \\\"root\\\", \\\"password\\\": \\\"DpMvp2026Secure\\\", \\\"column\\\": [\\\"id\\\", \\\"tenant_name\\\", \\\"brand\\\", \\\"scene_type\\\", \\\"seq_no\\\", \\\"question\\\", \\\"gmt_create\\\", \\\"gmt_modified\\\", \\\"dt\\\"], \\\"writeMode\\\": \\\"replace\\\", \\\"connection\\\": [{\\\"table\\\": [\\\"ods_sc_gxt_prod_question_df\\\"], \\\"jdbcUrl\\\": \\\"jdbc:mysql://mysql:3306/ods?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai\\\"}]}}}], \\\"setting\\\": {\\\"speed\\\": {\\\"channel\\\": 3}, \\\"errorLimit\\\": {\\\"record\\\": 0}}}}\\n\", \"timeout\": 3600}',1,'draft',NULL,1,'2026-05-13 05:04:11','2026-05-13 05:04:11',NULL,NULL),(17,'sync_ods_sc_gxt_scene_detail_df','datax','AL_ODS → ODS: ods_sc_gxt_scene_detail_df','{\"rawJson\": \"{\\\"job\\\": {\\\"content\\\": [{\\\"reader\\\": {\\\"name\\\": \\\"mysqlreader\\\", \\\"parameter\\\": {\\\"username\\\": \\\"data_devops\\\", \\\"password\\\": \\\"devops_2023!\\\", \\\"column\\\": [\\\"id\\\", \\\"tenant_name\\\", \\\"gmt_create\\\", \\\"gmt_modified\\\", \\\"brand\\\", \\\"media_id\\\", \\\"news_uuid\\\", \\\"news_content\\\", \\\"platform_name\\\", \\\"is_valid\\\", \\\"invalid_reason\\\", \\\"content_type\\\", \\\"disease\\\", \\\"symptom\\\", \\\"crowd\\\", \\\"trigger_scene\\\", \\\"core_intent\\\", \\\"disease_stage\\\", \\\"mentioned_drug\\\", \\\"drug_evaluation\\\", \\\"query_intent\\\", \\\"completion_tokens\\\", \\\"prompt_tokens\\\", \\\"total_tokens\\\", \\\"scene_l1\\\", \\\"scene_l2\\\", \\\"dt\\\"], \\\"connection\\\": [{\\\"table\\\": [\\\"ods_sc_gxt_scene_detail_df\\\"], \\\"jdbcUrl\\\": [\\\"jdbc:mysql://rm-8vb0aam8k3g0pi3gsmo.mysql.zhangbei.rds.aliyuncs.com:3306/taiji_terminal_digital?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai\\\"]}]}}, \\\"writer\\\": {\\\"name\\\": \\\"mysqlwriter\\\", \\\"parameter\\\": {\\\"username\\\": \\\"root\\\", \\\"password\\\": \\\"DpMvp2026Secure\\\", \\\"column\\\": [\\\"id\\\", \\\"tenant_name\\\", \\\"gmt_create\\\", \\\"gmt_modified\\\", \\\"brand\\\", \\\"media_id\\\", \\\"news_uuid\\\", \\\"news_content\\\", \\\"platform_name\\\", \\\"is_valid\\\", \\\"invalid_reason\\\", \\\"content_type\\\", \\\"disease\\\", \\\"symptom\\\", \\\"crowd\\\", \\\"trigger_scene\\\", \\\"core_intent\\\", \\\"disease_stage\\\", \\\"mentioned_drug\\\", \\\"drug_evaluation\\\", \\\"query_intent\\\", \\\"completion_tokens\\\", \\\"prompt_tokens\\\", \\\"total_tokens\\\", \\\"scene_l1\\\", \\\"scene_l2\\\", \\\"dt\\\"], \\\"writeMode\\\": \\\"replace\\\", \\\"connection\\\": [{\\\"table\\\": [\\\"ods_sc_gxt_scene_detail_df\\\"], \\\"jdbcUrl\\\": \\\"jdbc:mysql://mysql:3306/ods?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai\\\"}]}}}], \\\"setting\\\": {\\\"speed\\\": {\\\"channel\\\": 3}, \\\"errorLimit\\\": {\\\"record\\\": 0}}}}\\n\", \"timeout\": 3600}',1,'draft',NULL,1,'2026-05-13 05:04:11','2026-05-13 05:04:11',NULL,NULL),(18,'sync_ods_sc_gxt_scene_disease_stat_df','datax','AL_ODS → ODS: ods_sc_gxt_scene_disease_stat_df','{\"rawJson\": \"{\\\"job\\\": {\\\"content\\\": [{\\\"reader\\\": {\\\"name\\\": \\\"mysqlreader\\\", \\\"parameter\\\": {\\\"username\\\": \\\"data_devops\\\", \\\"password\\\": \\\"devops_2023!\\\", \\\"column\\\": [\\\"id\\\", \\\"tenant_name\\\", \\\"gmt_create\\\", \\\"gmt_modified\\\", \\\"brand\\\", \\\"scene_l2\\\", \\\"disease_kw\\\", \\\"cnt\\\", \\\"dt\\\"], \\\"connection\\\": [{\\\"table\\\": [\\\"ods_sc_gxt_scene_disease_stat_df\\\"], \\\"jdbcUrl\\\": [\\\"jdbc:mysql://rm-8vb0aam8k3g0pi3gsmo.mysql.zhangbei.rds.aliyuncs.com:3306/taiji_terminal_digital?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai\\\"]}]}}, \\\"writer\\\": {\\\"name\\\": \\\"mysqlwriter\\\", \\\"parameter\\\": {\\\"username\\\": \\\"root\\\", \\\"password\\\": \\\"DpMvp2026Secure\\\", \\\"column\\\": [\\\"id\\\", \\\"tenant_name\\\", \\\"gmt_create\\\", \\\"gmt_modified\\\", \\\"brand\\\", \\\"scene_l2\\\", \\\"disease_kw\\\", \\\"cnt\\\", \\\"dt\\\"], \\\"writeMode\\\": \\\"replace\\\", \\\"connection\\\": [{\\\"table\\\": [\\\"ods_sc_gxt_scene_disease_stat_df\\\"], \\\"jdbcUrl\\\": \\\"jdbc:mysql://mysql:3306/ods?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai\\\"}]}}}], \\\"setting\\\": {\\\"speed\\\": {\\\"channel\\\": 3}, \\\"errorLimit\\\": {\\\"record\\\": 0}}}}\\n\", \"timeout\": 3600}',1,'draft',NULL,1,'2026-05-13 05:04:11','2026-05-13 05:04:11',NULL,NULL),(19,'sync_ods_sc_gxt_scene_drug_stat_df','datax','AL_ODS → ODS: ods_sc_gxt_scene_drug_stat_df','{\"rawJson\": \"{\\\"job\\\": {\\\"content\\\": [{\\\"reader\\\": {\\\"name\\\": \\\"mysqlreader\\\", \\\"parameter\\\": {\\\"username\\\": \\\"data_devops\\\", \\\"password\\\": \\\"devops_2023!\\\", \\\"column\\\": [\\\"id\\\", \\\"tenant_name\\\", \\\"gmt_create\\\", \\\"gmt_modified\\\", \\\"brand\\\", \\\"scene_l2\\\", \\\"drug_kw\\\", \\\"cnt\\\", \\\"dt\\\"], \\\"connection\\\": [{\\\"table\\\": [\\\"ods_sc_gxt_scene_drug_stat_df\\\"], \\\"jdbcUrl\\\": [\\\"jdbc:mysql://rm-8vb0aam8k3g0pi3gsmo.mysql.zhangbei.rds.aliyuncs.com:3306/taiji_terminal_digital?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai\\\"]}]}}, \\\"writer\\\": {\\\"name\\\": \\\"mysqlwriter\\\", \\\"parameter\\\": {\\\"username\\\": \\\"root\\\", \\\"password\\\": \\\"DpMvp2026Secure\\\", \\\"column\\\": [\\\"id\\\", \\\"tenant_name\\\", \\\"gmt_create\\\", \\\"gmt_modified\\\", \\\"brand\\\", \\\"scene_l2\\\", \\\"drug_kw\\\", \\\"cnt\\\", \\\"dt\\\"], \\\"writeMode\\\": \\\"replace\\\", \\\"connection\\\": [{\\\"table\\\": [\\\"ods_sc_gxt_scene_drug_stat_df\\\"], \\\"jdbcUrl\\\": \\\"jdbc:mysql://mysql:3306/ods?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai\\\"}]}}}], \\\"setting\\\": {\\\"speed\\\": {\\\"channel\\\": 3}, \\\"errorLimit\\\": {\\\"record\\\": 0}}}}\\n\", \"timeout\": 3600}',1,'draft',NULL,1,'2026-05-13 05:04:11','2026-05-13 05:04:11',NULL,NULL),(20,'sync_ods_sc_gxt_scene_mapping_df','datax','AL_ODS → ODS: ods_sc_gxt_scene_mapping_df','{\"rawJson\": \"{\\\"job\\\": {\\\"content\\\": [{\\\"reader\\\": {\\\"name\\\": \\\"mysqlreader\\\", \\\"parameter\\\": {\\\"username\\\": \\\"data_devops\\\", \\\"password\\\": \\\"devops_2023!\\\", \\\"column\\\": [\\\"id\\\", \\\"tenant_name\\\", \\\"gmt_create\\\", \\\"gmt_modified\\\", \\\"brand\\\", \\\"trigger_scene\\\", \\\"post_cnt\\\", \\\"scene_l1\\\", \\\"scene_l2\\\", \\\"dt\\\"], \\\"connection\\\": [{\\\"table\\\": [\\\"ods_sc_gxt_scene_mapping_df\\\"], \\\"jdbcUrl\\\": [\\\"jdbc:mysql://rm-8vb0aam8k3g0pi3gsmo.mysql.zhangbei.rds.aliyuncs.com:3306/taiji_terminal_digital?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai\\\"]}]}}, \\\"writer\\\": {\\\"name\\\": \\\"mysqlwriter\\\", \\\"parameter\\\": {\\\"username\\\": \\\"root\\\", \\\"password\\\": \\\"DpMvp2026Secure\\\", \\\"column\\\": [\\\"id\\\", \\\"tenant_name\\\", \\\"gmt_create\\\", \\\"gmt_modified\\\", \\\"brand\\\", \\\"trigger_scene\\\", \\\"post_cnt\\\", \\\"scene_l1\\\", \\\"scene_l2\\\", \\\"dt\\\"], \\\"writeMode\\\": \\\"replace\\\", \\\"connection\\\": [{\\\"table\\\": [\\\"ods_sc_gxt_scene_mapping_df\\\"], \\\"jdbcUrl\\\": \\\"jdbc:mysql://mysql:3306/ods?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai\\\"}]}}}], \\\"setting\\\": {\\\"speed\\\": {\\\"channel\\\": 3}, \\\"errorLimit\\\": {\\\"record\\\": 0}}}}\\n\", \"timeout\": 3600}',1,'draft',NULL,1,'2026-05-13 05:04:12','2026-05-13 05:04:12',NULL,NULL),(21,'sync_ods_sc_gxt_scene_symptom_stat_df','datax','AL_ODS → ODS: ods_sc_gxt_scene_symptom_stat_df','{\"rawJson\": \"{\\\"job\\\": {\\\"content\\\": [{\\\"reader\\\": {\\\"name\\\": \\\"mysqlreader\\\", \\\"parameter\\\": {\\\"username\\\": \\\"data_devops\\\", \\\"password\\\": \\\"devops_2023!\\\", \\\"column\\\": [\\\"id\\\", \\\"tenant_name\\\", \\\"gmt_create\\\", \\\"gmt_modified\\\", \\\"brand\\\", \\\"scene_l2\\\", \\\"symptom_kw\\\", \\\"cnt\\\", \\\"dt\\\"], \\\"connection\\\": [{\\\"table\\\": [\\\"ods_sc_gxt_scene_symptom_stat_df\\\"], \\\"jdbcUrl\\\": [\\\"jdbc:mysql://rm-8vb0aam8k3g0pi3gsmo.mysql.zhangbei.rds.aliyuncs.com:3306/taiji_terminal_digital?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai\\\"]}]}}, \\\"writer\\\": {\\\"name\\\": \\\"mysqlwriter\\\", \\\"parameter\\\": {\\\"username\\\": \\\"root\\\", \\\"password\\\": \\\"DpMvp2026Secure\\\", \\\"column\\\": [\\\"id\\\", \\\"tenant_name\\\", \\\"gmt_create\\\", \\\"gmt_modified\\\", \\\"brand\\\", \\\"scene_l2\\\", \\\"symptom_kw\\\", \\\"cnt\\\", \\\"dt\\\"], \\\"writeMode\\\": \\\"replace\\\", \\\"connection\\\": [{\\\"table\\\": [\\\"ods_sc_gxt_scene_symptom_stat_df\\\"], \\\"jdbcUrl\\\": \\\"jdbc:mysql://mysql:3306/ods?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai\\\"}]}}}], \\\"setting\\\": {\\\"speed\\\": {\\\"channel\\\": 3}, \\\"errorLimit\\\": {\\\"record\\\": 0}}}}\\n\", \"timeout\": 3600}',1,'draft',NULL,1,'2026-05-13 05:04:12','2026-05-13 05:04:12',NULL,NULL);
/*!40000 ALTER TABLE `component` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `component_folder`
--

DROP TABLE IF EXISTS `component_folder`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `component_folder` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `parent_id` bigint DEFAULT NULL COMMENT '父文件夹 id, NULL 为根',
  `depth` int DEFAULT NULL COMMENT '层级: 0=一级, 1=二级, 2=三级',
  `created_by` bigint DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `component_folder`
--

LOCK TABLES `component_folder` WRITE;
/*!40000 ALTER TABLE `component_folder` DISABLE KEYS */;
INSERT INTO `component_folder` VALUES (1,'123','python',NULL,0,NULL,'2026-05-13 01:03:08','2026-05-13 01:03:08'),(2,'123','sql',NULL,0,NULL,'2026-05-13 01:11:49','2026-05-13 01:11:49');
/*!40000 ALTER TABLE `component_folder` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `data_source`
--

DROP TABLE IF EXISTS `data_source`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `data_source` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL COMMENT 'æ•°æ®æºåç§°',
  `type` varchar(32) NOT NULL COMMENT 'mysql/sqlserver/postgresql',
  `host` varchar(255) NOT NULL,
  `port` int NOT NULL,
  `database_name` varchar(128) NOT NULL,
  `username` varchar(128) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `description` text,
  `status` tinyint DEFAULT '1' COMMENT '1=å¯ç”¨ 0=ä¸å¯ç”¨',
  `last_check_time` datetime DEFAULT NULL,
  `created_by` bigint DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `data_source`
--

LOCK TABLES `data_source` WRITE;
/*!40000 ALTER TABLE `data_source` DISABLE KEYS */;
INSERT INTO `data_source` VALUES (3,'PortalMySQL','mysql','mysql',3306,'portal_db','root','DpMvp2026Secure','Portal 元数据库 (内网)',1,NULL,1,'2026-05-12 03:13:19','2026-05-12 03:13:19'),(5,'观星台-A (源库)','mysql','mysql',3306,'guanxingtai','root','DpMvp2026Secure','观星台业务源库 - 含测试数据',1,NULL,1,'2026-05-12 06:13:47','2026-05-12 06:13:47'),(6,'观星台-B (目标库)','mysql','mysql',3306,'guanxingtai_b','root','DpMvp2026Secure','观星台目标库 - DataX 同步演示',1,NULL,1,'2026-05-12 06:13:47','2026-05-12 07:50:16'),(7,'ODS','mysql','mysql',3306,'ods','root','DpMvp2026Secure','ODS 贴源层',1,NULL,1,'2026-05-13 04:58:54','2026-05-13 04:58:54'),(8,'ADS','mysql','mysql',3306,'ads','root','DpMvp2026Secure','ADS 应用层',1,NULL,1,'2026-05-13 04:58:54','2026-05-13 04:58:54');
/*!40000 ALTER TABLE `data_source` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notification`
--

DROP TABLE IF EXISTS `notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notification` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci,
  `source` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_read` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notification`
--

LOCK TABLES `notification` WRITE;
/*!40000 ALTER TABLE `notification` DISABLE KEYS */;
/*!40000 ALTER TABLE `notification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `operation_log`
--

DROP TABLE IF EXISTS `operation_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `operation_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint DEFAULT NULL,
  `username` varchar(64) DEFAULT NULL,
  `module` varchar(64) DEFAULT NULL COMMENT 'æ“ä½œæ¨¡å—',
  `action` varchar(64) DEFAULT NULL COMMENT 'æ“ä½œç±»åž‹',
  `detail` text COMMENT 'æ“ä½œè¯¦æƒ…',
  `ip` varchar(64) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operation_log`
--

LOCK TABLES `operation_log` WRITE;
/*!40000 ALTER TABLE `operation_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `operation_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project`
--

DROP TABLE IF EXISTS `project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `project` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '项目名称',
  `code` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '项目编码 — 用于 DS 工作流命名前缀',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '项目描述',
  `color` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '项目主题色 — 系统按 id 分配 8 色调色板',
  `status` int DEFAULT NULL COMMENT '1=启用 0=禁用',
  `is_default` int DEFAULT NULL COMMENT '1=系统默认未分组项目，不可删',
  `owner_id` bigint DEFAULT NULL COMMENT '负责人 user_id',
  `created_by` bigint DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project`
--

LOCK TABLES `project` WRITE;
/*!40000 ALTER TABLE `project` DISABLE KEYS */;
INSERT INTO `project` VALUES (1,'未分组','default','系统默认项目，存放未指定归属的同步任务','#2B5AED',1,1,NULL,NULL,'2026-05-12 04:30:15','2026-05-12 04:30:15'),(2,'观星台 ETL','guanxingtai','医药品牌洞察平台数据管道','#00C9A7',1,0,1,1,'2026-05-12 04:31:44','2026-05-12 04:31:44'),(3,'BI 报表层','bi_reports','BI 报表汇总与导出','#722ED1',1,0,1,1,'2026-05-12 04:31:45','2026-05-12 04:31:45');
/*!40000 ALTER TABLE `project` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sync_task`
--

DROP TABLE IF EXISTS `sync_task`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sync_task` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL COMMENT 'ä»»åŠ¡åç§°',
  `source_id` bigint NOT NULL COMMENT 'æºæ•°æ®æºID',
  `target_id` bigint NOT NULL COMMENT 'ç›®æ ‡æ•°æ®æºID',
  `source_table` varchar(128) NOT NULL,
  `target_table` varchar(128) NOT NULL,
  `sync_type` varchar(32) DEFAULT 'full' COMMENT 'full/incremental',
  `increment_column` varchar(128) DEFAULT NULL COMMENT 'å¢žé‡å­—æ®µ',
  `schedule_cron` varchar(64) DEFAULT NULL COMMENT 'è°ƒåº¦ cron è¡¨è¾¾å¼',
  `ds_workflow_id` bigint DEFAULT NULL COMMENT 'DS å·¥ä½œæµID',
  `status` varchar(32) DEFAULT 'draft' COMMENT 'draft/active/paused/error',
  `last_run_time` datetime DEFAULT NULL,
  `last_run_status` varchar(32) DEFAULT NULL,
  `created_by` bigint DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `project_id` bigint DEFAULT NULL COMMENT '所属项目',
  `field_mapping` text COMMENT '字段映射JSON',
  `where_clause` text COMMENT '源端WHERE过滤',
  `split_pk` varchar(128) DEFAULT NULL COMMENT 'DataX splitPk',
  `write_mode` varchar(32) DEFAULT 'insert' COMMENT '写入模式',
  `pre_sql` text COMMENT '导入前SQL JSON数组',
  `post_sql` text COMMENT '导入后SQL JSON数组',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sync_task`
--

LOCK TABLES `sync_task` WRITE;
/*!40000 ALTER TABLE `sync_task` DISABLE KEYS */;
INSERT INTO `sync_task` VALUES (4,'ods_sc_gxt_scene_disease_stat_df',9,7,'ods_sc_gxt_scene_disease_stat_df','ods_sc_gxt_scene_disease_stat_df','incremental',NULL,'',NULL,'draft',NULL,NULL,1,'2026-05-12 04:54:09','2026-05-13 05:57:54',2,'[{\"kind\": \"column\", \"src\": \"id\", \"dst\": \"id\", \"type\": \"bigint unsigned\"}, {\"kind\": \"column\", \"src\": \"tenant_name\", \"dst\": \"tenant_name\", \"type\": \"varchar(128)\"}, {\"kind\": \"column\", \"src\": \"gmt_create\", \"dst\": \"gmt_create\", \"type\": \"timestamp\"}, {\"kind\": \"column\", \"src\": \"gmt_modified\", \"dst\": \"gmt_modified\", \"type\": \"timestamp\"}, {\"kind\": \"column\", \"src\": \"brand\", \"dst\": \"brand\", \"type\": \"varchar(50)\"}, {\"kind\": \"column\", \"src\": \"scene_l2\", \"dst\": \"scene_l2\", \"type\": \"varchar(100)\"}, {\"kind\": \"column\", \"src\": \"disease_kw\", \"dst\": \"disease_kw\", \"type\": \"varchar(100)\"}, {\"kind\": \"column\", \"src\": \"cnt\", \"dst\": \"cnt\", \"type\": \"int\"}, {\"kind\": \"column\", \"src\": \"dt\", \"dst\": \"dt\", \"type\": \"varchar(8)\"}]',NULL,NULL,'insert',NULL,NULL),(5,'ods_sc_gxt_scene_detail_df',9,7,'ods_sc_gxt_scene_detail_df','ods_sc_gxt_scene_detail_df','full',NULL,'',NULL,'draft',NULL,NULL,1,'2026-05-12 05:50:35','2026-05-13 05:57:21',2,'[{\"kind\": \"column\", \"src\": \"id\", \"dst\": \"id\", \"type\": \"bigint unsigned\"}, {\"kind\": \"column\", \"src\": \"tenant_name\", \"dst\": \"tenant_name\", \"type\": \"varchar(128)\"}, {\"kind\": \"column\", \"src\": \"gmt_create\", \"dst\": \"gmt_create\", \"type\": \"timestamp\"}, {\"kind\": \"column\", \"src\": \"gmt_modified\", \"dst\": \"gmt_modified\", \"type\": \"timestamp\"}, {\"kind\": \"column\", \"src\": \"brand\", \"dst\": \"brand\", \"type\": \"varchar(50)\"}, {\"kind\": \"column\", \"src\": \"media_id\", \"dst\": \"media_id\", \"type\": \"varchar(100)\"}, {\"kind\": \"column\", \"src\": \"news_uuid\", \"dst\": \"news_uuid\", \"type\": \"varchar(100)\"}, {\"kind\": \"column\", \"src\": \"news_content\", \"dst\": \"news_content\", \"type\": \"text\"}, {\"kind\": \"column\", \"src\": \"platform_name\", \"dst\": \"platform_name\", \"type\": \"varchar(100)\"}, {\"kind\": \"column\", \"src\": \"is_valid\", \"dst\": \"is_valid\", \"type\": \"varchar(10)\"}, {\"kind\": \"column\", \"src\": \"invalid_reason\", \"dst\": \"invalid_reason\", \"type\": \"varchar(500)\"}, {\"kind\": \"column\", \"src\": \"content_type\", \"dst\": \"content_type\", \"type\": \"varchar(50)\"}, {\"kind\": \"column\", \"src\": \"disease\", \"dst\": \"disease\", \"type\": \"varchar(500)\"}, {\"kind\": \"column\", \"src\": \"symptom\", \"dst\": \"symptom\", \"type\": \"varchar(500)\"}, {\"kind\": \"column\", \"src\": \"crowd\", \"dst\": \"crowd\", \"type\": \"varchar(200)\"}, {\"kind\": \"column\", \"src\": \"trigger_scene\", \"dst\": \"trigger_scene\", \"type\": \"varchar(2000)\"}, {\"kind\": \"column\", \"src\": \"core_intent\", \"dst\": \"core_intent\", \"type\": \"varchar(200)\"}, {\"kind\": \"column\", \"src\": \"disease_stage\", \"dst\": \"disease_stage\", \"type\": \"varchar(100)\"}, {\"kind\": \"column\", \"src\": \"mentioned_drug\", \"dst\": \"mentioned_drug\", \"type\": \"varchar(500)\"}, {\"kind\": \"column\", \"src\": \"drug_evaluation\", \"dst\": \"drug_evaluation\", \"type\": \"text\"}, {\"kind\": \"column\", \"src\": \"query_intent\", \"dst\": \"query_intent\", \"type\": \"varchar(100)\"}, {\"kind\": \"column\", \"src\": \"completion_tokens\", \"dst\": \"completion_tokens\", \"type\": \"int\"}, {\"kind\": \"column\", \"src\": \"prompt_tokens\", \"dst\": \"prompt_tokens\", \"type\": \"int\"}, {\"kind\": \"column\", \"src\": \"total_tokens\", \"dst\": \"total_tokens\", \"type\": \"int\"}, {\"kind\": \"column\", \"src\": \"scene_l1\", \"dst\": \"scene_l1\", \"type\": \"varchar(50)\"}, {\"kind\": \"column\", \"src\": \"scene_l2\", \"dst\": \"scene_l2\", \"type\": \"varchar(100)\"}, {\"kind\": \"column\", \"src\": \"dt\", \"dst\": \"dt\", \"type\": \"varchar(8)\"}]',NULL,NULL,'insert',NULL,NULL),(7,'测试A到B-dim_brand',5,6,'dim_brand','dim_brand','full',NULL,'',NULL,'draft','2026-05-12 08:37:36','success',1,'2026-05-12 07:20:22','2026-05-12 08:37:47',NULL,'[{\"kind\": \"column\", \"src\": \"id\", \"dst\": \"id\", \"type\": \"varchar(32)\"}, {\"kind\": \"column\", \"src\": \"tenant_id\", \"dst\": \"tenant_id\", \"type\": \"varchar(32)\"}, {\"kind\": \"column\", \"src\": \"name\", \"dst\": \"name\", \"type\": \"varchar(100)\"}, {\"kind\": \"column\", \"src\": \"icon\", \"dst\": \"icon\", \"type\": \"varchar(20)\"}, {\"kind\": \"column\", \"src\": \"color\", \"dst\": \"color\", \"type\": \"varchar(200)\"}, {\"kind\": \"column\", \"src\": \"sub_name\", \"dst\": \"sub_name\", \"type\": \"varchar(100)\"}, {\"kind\": \"column\", \"src\": \"source_brand_kw\", \"dst\": \"source_brand_kw\", \"type\": \"varchar(500)\"}, {\"kind\": \"column\", \"src\": \"sort_order\", \"dst\": \"sort_order\", \"type\": \"int\"}, {\"kind\": \"column\", \"src\": \"status\", \"dst\": \"status\", \"type\": \"varchar(20)\"}, {\"kind\": \"column\", \"src\": \"created_at\", \"dst\": \"created_at\", \"type\": \"datetime\"}, {\"kind\": \"column\", \"src\": \"updated_at\", \"dst\": \"updated_at\", \"type\": \"datetime\"}]',NULL,NULL,'insert',NULL,NULL),(8,'ods_sc_gxt_prod_question_df',9,7,'ods_sc_gxt_prod_question_df','ods_sc_gxt_prod_question_df','full',NULL,'1',NULL,'active','2026-05-13 05:55:54','success',1,'2026-05-13 05:17:16','2026-05-13 06:51:13',2,'[{\"kind\": \"column\", \"src\": \"id\", \"dst\": \"id\", \"type\": \"bigint unsigned\"}, {\"kind\": \"column\", \"src\": \"tenant_name\", \"dst\": \"tenant_name\", \"type\": \"varchar(128)\"}, {\"kind\": \"column\", \"src\": \"brand\", \"dst\": \"brand\", \"type\": \"varchar(128)\"}, {\"kind\": \"column\", \"src\": \"scene_type\", \"dst\": \"scene_type\", \"type\": \"varchar(200)\"}, {\"kind\": \"column\", \"src\": \"seq_no\", \"dst\": \"seq_no\", \"type\": \"int\"}, {\"kind\": \"column\", \"src\": \"question\", \"dst\": \"question\", \"type\": \"varchar(1000)\"}, {\"kind\": \"column\", \"src\": \"gmt_create\", \"dst\": \"gmt_create\", \"type\": \"timestamp\"}, {\"kind\": \"column\", \"src\": \"gmt_modified\", \"dst\": \"gmt_modified\", \"type\": \"timestamp\"}, {\"kind\": \"column\", \"src\": \"dt\", \"dst\": \"dt\", \"type\": \"varchar(8)\"}]',NULL,NULL,'insert','[\"truncate table ods_sc_gxt_prod_question_df\"]',NULL);
/*!40000 ALTER TABLE `sync_task` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sys_user`
--

DROP TABLE IF EXISTS `sys_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(64) NOT NULL,
  `password` varchar(255) NOT NULL,
  `real_name` varchar(64) DEFAULT NULL,
  `email` varchar(128) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `role` varchar(32) DEFAULT 'user' COMMENT 'admin/user',
  `status` tinyint DEFAULT '1' COMMENT '1=å¯ç”¨ 0=ç¦ç”¨',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_user`
--

LOCK TABLES `sys_user` WRITE;
/*!40000 ALTER TABLE `sys_user` DISABLE KEYS */;
INSERT INTO `sys_user` VALUES (1,'admin','$2b$12$hDG2TCQeF4F0sjz.1qSSiOZTk6kcQ7ELlaOYEyVP/ErS44vS4VNsq','系统管理员',NULL,NULL,'admin',1,'2026-05-11 05:21:15','2026-05-13 08:38:52');
/*!40000 ALTER TABLE `sys_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `word_root`
--

DROP TABLE IF EXISTS `word_root`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `word_root` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `en` varchar(64) NOT NULL COMMENT '英文词根',
  `cn` varchar(64) NOT NULL COMMENT '中文名',
  `category` varchar(32) NOT NULL DEFAULT 'business' COMMENT 'business/technical/metric',
  `description` varchar(255) DEFAULT NULL COMMENT '说明',
  `example` varchar(255) DEFAULT NULL COMMENT '示例用法',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_en` (`en`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `word_root`
--

LOCK TABLES `word_root` WRITE;
/*!40000 ALTER TABLE `word_root` DISABLE KEYS */;
/*!40000 ALTER TABLE `word_root` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow`
--

DROP TABLE IF EXISTS `workflow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `tags` json DEFAULT NULL,
  `steps_json` json NOT NULL,
  `dag_json` json DEFAULT NULL,
  `cron_expression` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `schedule_status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `version` int NOT NULL,
  `ds_process_code` bigint DEFAULT NULL,
  `ds_schedule_id` bigint DEFAULT NULL,
  `created_by` bigint DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `priority` int NOT NULL DEFAULT '3' COMMENT '优先级 1=P1高 2=P2中 3=P3低',
  `last_run_status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '最近运行状态',
  `last_run_time` datetime DEFAULT NULL COMMENT '最近运行时间',
  `last_run_duration` int DEFAULT NULL COMMENT '最近运行耗时秒',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow`
--

LOCK TABLES `workflow` WRITE;
/*!40000 ALTER TABLE `workflow` DISABLE KEYS */;
INSERT INTO `workflow` VALUES (4,'daily_user_etl','每日用户全量同步 (DataX → Python → Shell)',NULL,'[{\"name\": \"datax_extract\", \"component_id\": 10}, {\"name\": \"transform\", \"component_id\": 8}, {\"name\": \"alert\", \"component_id\": 11}]',NULL,'0 0 2 * * ?','OFFLINE','online',1,173184205699456,3,1,'2026-05-12 03:13:20','2026-05-13 06:40:07',3,'SUCCESS','2026-05-13 14:08:10',3),(5,'nightly_cleanup','每晚清理临时文件',NULL,'[{\"name\": \"cleanup\", \"component_id\": 9}, {\"name\": \"alert\", \"component_id\": 11}]',NULL,'0 30 23 * * ?','OFFLINE','offline',1,173184206033280,4,1,'2026-05-12 03:13:21','2026-05-13 06:40:07',3,'SUCCESS','2026-05-13 14:08:10',3),(6,'user_data_export','用户数据导出 (SQL 抽取 + Python 加工)',NULL,'[{\"name\": \"sql_extract\", \"component_id\": 7}, {\"name\": \"transform\", \"component_id\": 8}]',NULL,NULL,'OFFLINE','online',1,173184206372224,NULL,1,'2026-05-12 03:13:21','2026-05-13 06:40:07',3,'SUCCESS','2026-05-13 14:08:10',3),(7,'demo01',NULL,NULL,'[{\"name\": \"datax_user_sync_demo\", \"component_id\": 10}, {\"name\": \"datax_user_sync_demo\", \"component_id\": 10}, {\"name\": \"transform_user_data\", \"component_id\": 8}]',NULL,'11','OFFLINE','tested',2,NULL,NULL,1,'2026-05-12 03:15:50','2026-05-12 03:15:58',3,NULL,NULL,NULL),(8,'测试01',NULL,NULL,'[{\"name\": \"123\", \"component_id\": 13}, {\"name\": \"transform_user_data\", \"component_id\": 8}, {\"name\": \"extract_users_from_portal\", \"component_id\": 7}]','{\"edges\": [{\"id\": \"edge-1778642800569\", \"source\": \"node-1778642790189\", \"target\": \"node-1778642796404\"}, {\"id\": \"edge-1778642816767\", \"source\": \"node-1778642790189\", \"target\": \"node-1778642810879\"}], \"nodes\": [{\"id\": \"node-1778642790189\", \"name\": \"123\", \"skip\": false, \"position\": {\"x\": 132.0328298577339, \"y\": 60.94632381596152}, \"component_id\": 13}, {\"id\": \"node-1778642796404\", \"name\": \"transform_user_data\", \"skip\": false, \"position\": {\"x\": 453.0, \"y\": 238.5}, \"component_id\": 8}, {\"id\": \"node-1778642810879\", \"name\": \"extract_users_from_portal\", \"skip\": false, \"position\": {\"x\": 139.3172200837448, \"y\": 237.2023155816762}, \"component_id\": 7}]}',NULL,'OFFLINE','offline',1,173278852484480,NULL,1,'2026-05-13 03:27:09','2026-05-13 06:40:07',3,'SUCCESS','2026-05-13 14:08:10',3),(9,'002',NULL,'[]','[{\"name\": \"123\", \"component_id\": 13}]','{\"edges\": [], \"nodes\": [{\"id\": \"node-1778654882021\", \"name\": \"123\", \"skip\": false, \"position\": {\"x\": 191.0, \"y\": 185.5}, \"component_id\": 13}]}',NULL,'OFFLINE','online',1,173285883084160,NULL,1,'2026-05-13 06:48:09','2026-05-13 06:48:15',3,NULL,NULL,NULL);
/*!40000 ALTER TABLE `workflow` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `dolphinscheduler`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `dolphinscheduler` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `dolphinscheduler`;

--
-- Table structure for table `QRTZ_BLOB_TRIGGERS`
--

DROP TABLE IF EXISTS `QRTZ_BLOB_TRIGGERS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `QRTZ_BLOB_TRIGGERS` (
  `SCHED_NAME` varchar(120) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_NAME` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_GROUP` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `BLOB_DATA` blob,
  PRIMARY KEY (`SCHED_NAME`,`TRIGGER_NAME`,`TRIGGER_GROUP`),
  KEY `SCHED_NAME` (`SCHED_NAME`,`TRIGGER_NAME`,`TRIGGER_GROUP`),
  CONSTRAINT `QRTZ_BLOB_TRIGGERS_ibfk_1` FOREIGN KEY (`SCHED_NAME`, `TRIGGER_NAME`, `TRIGGER_GROUP`) REFERENCES `QRTZ_TRIGGERS` (`SCHED_NAME`, `TRIGGER_NAME`, `TRIGGER_GROUP`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `QRTZ_BLOB_TRIGGERS`
--

LOCK TABLES `QRTZ_BLOB_TRIGGERS` WRITE;
/*!40000 ALTER TABLE `QRTZ_BLOB_TRIGGERS` DISABLE KEYS */;
/*!40000 ALTER TABLE `QRTZ_BLOB_TRIGGERS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `QRTZ_CALENDARS`
--

DROP TABLE IF EXISTS `QRTZ_CALENDARS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `QRTZ_CALENDARS` (
  `SCHED_NAME` varchar(120) COLLATE utf8mb3_bin NOT NULL,
  `CALENDAR_NAME` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `CALENDAR` blob NOT NULL,
  PRIMARY KEY (`SCHED_NAME`,`CALENDAR_NAME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `QRTZ_CALENDARS`
--

LOCK TABLES `QRTZ_CALENDARS` WRITE;
/*!40000 ALTER TABLE `QRTZ_CALENDARS` DISABLE KEYS */;
/*!40000 ALTER TABLE `QRTZ_CALENDARS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `QRTZ_CRON_TRIGGERS`
--

DROP TABLE IF EXISTS `QRTZ_CRON_TRIGGERS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `QRTZ_CRON_TRIGGERS` (
  `SCHED_NAME` varchar(120) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_NAME` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_GROUP` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `CRON_EXPRESSION` varchar(120) COLLATE utf8mb3_bin NOT NULL,
  `TIME_ZONE_ID` varchar(80) COLLATE utf8mb3_bin DEFAULT NULL,
  PRIMARY KEY (`SCHED_NAME`,`TRIGGER_NAME`,`TRIGGER_GROUP`),
  CONSTRAINT `QRTZ_CRON_TRIGGERS_ibfk_1` FOREIGN KEY (`SCHED_NAME`, `TRIGGER_NAME`, `TRIGGER_GROUP`) REFERENCES `QRTZ_TRIGGERS` (`SCHED_NAME`, `TRIGGER_NAME`, `TRIGGER_GROUP`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `QRTZ_CRON_TRIGGERS`
--

LOCK TABLES `QRTZ_CRON_TRIGGERS` WRITE;
/*!40000 ALTER TABLE `QRTZ_CRON_TRIGGERS` DISABLE KEYS */;
/*!40000 ALTER TABLE `QRTZ_CRON_TRIGGERS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `QRTZ_FIRED_TRIGGERS`
--

DROP TABLE IF EXISTS `QRTZ_FIRED_TRIGGERS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `QRTZ_FIRED_TRIGGERS` (
  `SCHED_NAME` varchar(120) COLLATE utf8mb3_bin NOT NULL,
  `ENTRY_ID` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_NAME` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_GROUP` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `INSTANCE_NAME` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `FIRED_TIME` bigint NOT NULL,
  `SCHED_TIME` bigint NOT NULL,
  `PRIORITY` int NOT NULL,
  `STATE` varchar(16) COLLATE utf8mb3_bin NOT NULL,
  `JOB_NAME` varchar(200) COLLATE utf8mb3_bin DEFAULT NULL,
  `JOB_GROUP` varchar(200) COLLATE utf8mb3_bin DEFAULT NULL,
  `IS_NONCONCURRENT` varchar(1) COLLATE utf8mb3_bin DEFAULT NULL,
  `REQUESTS_RECOVERY` varchar(1) COLLATE utf8mb3_bin DEFAULT NULL,
  PRIMARY KEY (`SCHED_NAME`,`ENTRY_ID`),
  KEY `IDX_QRTZ_FT_TRIG_INST_NAME` (`SCHED_NAME`,`INSTANCE_NAME`),
  KEY `IDX_QRTZ_FT_INST_JOB_REQ_RCVRY` (`SCHED_NAME`,`INSTANCE_NAME`,`REQUESTS_RECOVERY`),
  KEY `IDX_QRTZ_FT_J_G` (`SCHED_NAME`,`JOB_NAME`,`JOB_GROUP`),
  KEY `IDX_QRTZ_FT_JG` (`SCHED_NAME`,`JOB_GROUP`),
  KEY `IDX_QRTZ_FT_T_G` (`SCHED_NAME`,`TRIGGER_NAME`,`TRIGGER_GROUP`),
  KEY `IDX_QRTZ_FT_TG` (`SCHED_NAME`,`TRIGGER_GROUP`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `QRTZ_FIRED_TRIGGERS`
--

LOCK TABLES `QRTZ_FIRED_TRIGGERS` WRITE;
/*!40000 ALTER TABLE `QRTZ_FIRED_TRIGGERS` DISABLE KEYS */;
/*!40000 ALTER TABLE `QRTZ_FIRED_TRIGGERS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `QRTZ_JOB_DETAILS`
--

DROP TABLE IF EXISTS `QRTZ_JOB_DETAILS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `QRTZ_JOB_DETAILS` (
  `SCHED_NAME` varchar(120) COLLATE utf8mb3_bin NOT NULL,
  `JOB_NAME` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `JOB_GROUP` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `DESCRIPTION` varchar(250) COLLATE utf8mb3_bin DEFAULT NULL,
  `JOB_CLASS_NAME` varchar(250) COLLATE utf8mb3_bin NOT NULL,
  `IS_DURABLE` varchar(1) COLLATE utf8mb3_bin NOT NULL,
  `IS_NONCONCURRENT` varchar(1) COLLATE utf8mb3_bin NOT NULL,
  `IS_UPDATE_DATA` varchar(1) COLLATE utf8mb3_bin NOT NULL,
  `REQUESTS_RECOVERY` varchar(1) COLLATE utf8mb3_bin NOT NULL,
  `JOB_DATA` blob,
  PRIMARY KEY (`SCHED_NAME`,`JOB_NAME`,`JOB_GROUP`),
  KEY `IDX_QRTZ_J_REQ_RECOVERY` (`SCHED_NAME`,`REQUESTS_RECOVERY`),
  KEY `IDX_QRTZ_J_GRP` (`SCHED_NAME`,`JOB_GROUP`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `QRTZ_JOB_DETAILS`
--

LOCK TABLES `QRTZ_JOB_DETAILS` WRITE;
/*!40000 ALTER TABLE `QRTZ_JOB_DETAILS` DISABLE KEYS */;
/*!40000 ALTER TABLE `QRTZ_JOB_DETAILS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `QRTZ_LOCKS`
--

DROP TABLE IF EXISTS `QRTZ_LOCKS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `QRTZ_LOCKS` (
  `SCHED_NAME` varchar(120) COLLATE utf8mb3_bin NOT NULL,
  `LOCK_NAME` varchar(40) COLLATE utf8mb3_bin NOT NULL,
  PRIMARY KEY (`SCHED_NAME`,`LOCK_NAME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `QRTZ_LOCKS`
--

LOCK TABLES `QRTZ_LOCKS` WRITE;
/*!40000 ALTER TABLE `QRTZ_LOCKS` DISABLE KEYS */;
INSERT INTO `QRTZ_LOCKS` VALUES ('DolphinScheduler','STATE_ACCESS'),('DolphinScheduler','TRIGGER_ACCESS');
/*!40000 ALTER TABLE `QRTZ_LOCKS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `QRTZ_PAUSED_TRIGGER_GRPS`
--

DROP TABLE IF EXISTS `QRTZ_PAUSED_TRIGGER_GRPS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `QRTZ_PAUSED_TRIGGER_GRPS` (
  `SCHED_NAME` varchar(120) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_GROUP` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  PRIMARY KEY (`SCHED_NAME`,`TRIGGER_GROUP`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `QRTZ_PAUSED_TRIGGER_GRPS`
--

LOCK TABLES `QRTZ_PAUSED_TRIGGER_GRPS` WRITE;
/*!40000 ALTER TABLE `QRTZ_PAUSED_TRIGGER_GRPS` DISABLE KEYS */;
/*!40000 ALTER TABLE `QRTZ_PAUSED_TRIGGER_GRPS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `QRTZ_SCHEDULER_STATE`
--

DROP TABLE IF EXISTS `QRTZ_SCHEDULER_STATE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `QRTZ_SCHEDULER_STATE` (
  `SCHED_NAME` varchar(120) COLLATE utf8mb3_bin NOT NULL,
  `INSTANCE_NAME` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `LAST_CHECKIN_TIME` bigint NOT NULL,
  `CHECKIN_INTERVAL` bigint NOT NULL,
  PRIMARY KEY (`SCHED_NAME`,`INSTANCE_NAME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `QRTZ_SCHEDULER_STATE`
--

LOCK TABLES `QRTZ_SCHEDULER_STATE` WRITE;
/*!40000 ALTER TABLE `QRTZ_SCHEDULER_STATE` DISABLE KEYS */;
INSERT INTO `QRTZ_SCHEDULER_STATE` VALUES ('DolphinScheduler','3194bc8c0e3c1778510379894',1778662871003,5000);
/*!40000 ALTER TABLE `QRTZ_SCHEDULER_STATE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `QRTZ_SIMPLE_TRIGGERS`
--

DROP TABLE IF EXISTS `QRTZ_SIMPLE_TRIGGERS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `QRTZ_SIMPLE_TRIGGERS` (
  `SCHED_NAME` varchar(120) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_NAME` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_GROUP` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `REPEAT_COUNT` bigint NOT NULL,
  `REPEAT_INTERVAL` bigint NOT NULL,
  `TIMES_TRIGGERED` bigint NOT NULL,
  PRIMARY KEY (`SCHED_NAME`,`TRIGGER_NAME`,`TRIGGER_GROUP`),
  CONSTRAINT `QRTZ_SIMPLE_TRIGGERS_ibfk_1` FOREIGN KEY (`SCHED_NAME`, `TRIGGER_NAME`, `TRIGGER_GROUP`) REFERENCES `QRTZ_TRIGGERS` (`SCHED_NAME`, `TRIGGER_NAME`, `TRIGGER_GROUP`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `QRTZ_SIMPLE_TRIGGERS`
--

LOCK TABLES `QRTZ_SIMPLE_TRIGGERS` WRITE;
/*!40000 ALTER TABLE `QRTZ_SIMPLE_TRIGGERS` DISABLE KEYS */;
/*!40000 ALTER TABLE `QRTZ_SIMPLE_TRIGGERS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `QRTZ_SIMPROP_TRIGGERS`
--

DROP TABLE IF EXISTS `QRTZ_SIMPROP_TRIGGERS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `QRTZ_SIMPROP_TRIGGERS` (
  `SCHED_NAME` varchar(120) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_NAME` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_GROUP` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `STR_PROP_1` varchar(512) COLLATE utf8mb3_bin DEFAULT NULL,
  `STR_PROP_2` varchar(512) COLLATE utf8mb3_bin DEFAULT NULL,
  `STR_PROP_3` varchar(512) COLLATE utf8mb3_bin DEFAULT NULL,
  `INT_PROP_1` int DEFAULT NULL,
  `INT_PROP_2` int DEFAULT NULL,
  `LONG_PROP_1` bigint DEFAULT NULL,
  `LONG_PROP_2` bigint DEFAULT NULL,
  `DEC_PROP_1` decimal(13,4) DEFAULT NULL,
  `DEC_PROP_2` decimal(13,4) DEFAULT NULL,
  `BOOL_PROP_1` varchar(1) COLLATE utf8mb3_bin DEFAULT NULL,
  `BOOL_PROP_2` varchar(1) COLLATE utf8mb3_bin DEFAULT NULL,
  PRIMARY KEY (`SCHED_NAME`,`TRIGGER_NAME`,`TRIGGER_GROUP`),
  CONSTRAINT `QRTZ_SIMPROP_TRIGGERS_ibfk_1` FOREIGN KEY (`SCHED_NAME`, `TRIGGER_NAME`, `TRIGGER_GROUP`) REFERENCES `QRTZ_TRIGGERS` (`SCHED_NAME`, `TRIGGER_NAME`, `TRIGGER_GROUP`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `QRTZ_SIMPROP_TRIGGERS`
--

LOCK TABLES `QRTZ_SIMPROP_TRIGGERS` WRITE;
/*!40000 ALTER TABLE `QRTZ_SIMPROP_TRIGGERS` DISABLE KEYS */;
/*!40000 ALTER TABLE `QRTZ_SIMPROP_TRIGGERS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `QRTZ_TRIGGERS`
--

DROP TABLE IF EXISTS `QRTZ_TRIGGERS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `QRTZ_TRIGGERS` (
  `SCHED_NAME` varchar(120) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_NAME` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_GROUP` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `JOB_NAME` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `JOB_GROUP` varchar(200) COLLATE utf8mb3_bin NOT NULL,
  `DESCRIPTION` varchar(250) COLLATE utf8mb3_bin DEFAULT NULL,
  `NEXT_FIRE_TIME` bigint DEFAULT NULL,
  `PREV_FIRE_TIME` bigint DEFAULT NULL,
  `PRIORITY` int DEFAULT NULL,
  `TRIGGER_STATE` varchar(16) COLLATE utf8mb3_bin NOT NULL,
  `TRIGGER_TYPE` varchar(8) COLLATE utf8mb3_bin NOT NULL,
  `START_TIME` bigint NOT NULL,
  `END_TIME` bigint DEFAULT NULL,
  `CALENDAR_NAME` varchar(200) COLLATE utf8mb3_bin DEFAULT NULL,
  `MISFIRE_INSTR` smallint DEFAULT NULL,
  `JOB_DATA` blob,
  PRIMARY KEY (`SCHED_NAME`,`TRIGGER_NAME`,`TRIGGER_GROUP`),
  KEY `IDX_QRTZ_T_J` (`SCHED_NAME`,`JOB_NAME`,`JOB_GROUP`),
  KEY `IDX_QRTZ_T_JG` (`SCHED_NAME`,`JOB_GROUP`),
  KEY `IDX_QRTZ_T_C` (`SCHED_NAME`,`CALENDAR_NAME`),
  KEY `IDX_QRTZ_T_G` (`SCHED_NAME`,`TRIGGER_GROUP`),
  KEY `IDX_QRTZ_T_STATE` (`SCHED_NAME`,`TRIGGER_STATE`),
  KEY `IDX_QRTZ_T_N_STATE` (`SCHED_NAME`,`TRIGGER_NAME`,`TRIGGER_GROUP`,`TRIGGER_STATE`),
  KEY `IDX_QRTZ_T_N_G_STATE` (`SCHED_NAME`,`TRIGGER_GROUP`,`TRIGGER_STATE`),
  KEY `IDX_QRTZ_T_NEXT_FIRE_TIME` (`SCHED_NAME`,`NEXT_FIRE_TIME`),
  KEY `IDX_QRTZ_T_NFT_ST` (`SCHED_NAME`,`TRIGGER_STATE`,`NEXT_FIRE_TIME`),
  KEY `IDX_QRTZ_T_NFT_MISFIRE` (`SCHED_NAME`,`MISFIRE_INSTR`,`NEXT_FIRE_TIME`),
  KEY `IDX_QRTZ_T_NFT_ST_MISFIRE` (`SCHED_NAME`,`MISFIRE_INSTR`,`NEXT_FIRE_TIME`,`TRIGGER_STATE`),
  KEY `IDX_QRTZ_T_NFT_ST_MISFIRE_GRP` (`SCHED_NAME`,`MISFIRE_INSTR`,`NEXT_FIRE_TIME`,`TRIGGER_GROUP`,`TRIGGER_STATE`),
  CONSTRAINT `QRTZ_TRIGGERS_ibfk_1` FOREIGN KEY (`SCHED_NAME`, `JOB_NAME`, `JOB_GROUP`) REFERENCES `QRTZ_JOB_DETAILS` (`SCHED_NAME`, `JOB_NAME`, `JOB_GROUP`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `QRTZ_TRIGGERS`
--

LOCK TABLES `QRTZ_TRIGGERS` WRITE;
/*!40000 ALTER TABLE `QRTZ_TRIGGERS` DISABLE KEYS */;
/*!40000 ALTER TABLE `QRTZ_TRIGGERS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_access_token`
--

DROP TABLE IF EXISTS `t_ds_access_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_access_token` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `user_id` int DEFAULT NULL COMMENT 'user id',
  `token` varchar(64) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'token',
  `expire_time` datetime DEFAULT NULL COMMENT 'end time of token ',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_access_token`
--

LOCK TABLES `t_ds_access_token` WRITE;
/*!40000 ALTER TABLE `t_ds_access_token` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_access_token` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_alert`
--

DROP TABLE IF EXISTS `t_ds_alert`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_alert` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `title` varchar(512) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'title',
  `sign` char(40) COLLATE utf8mb3_bin NOT NULL DEFAULT '' COMMENT 'sign=sha1(content)',
  `content` text COLLATE utf8mb3_bin COMMENT 'Message content (can be email, can be SMS. Mail is stored in JSON map, and SMS is string)',
  `alert_status` tinyint DEFAULT '0' COMMENT '0:wait running,1:success,2:failed',
  `warning_type` tinyint DEFAULT '2' COMMENT '1 process is successfully, 2 process/task is failed',
  `log` text COLLATE utf8mb3_bin COMMENT 'log',
  `alertgroup_id` int DEFAULT NULL COMMENT 'alert group id',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  `project_code` bigint DEFAULT NULL COMMENT 'project_code',
  `process_definition_code` bigint DEFAULT NULL COMMENT 'process_definition_code',
  `process_instance_id` int DEFAULT NULL COMMENT 'process_instance_id',
  `alert_type` int DEFAULT NULL COMMENT 'alert_type',
  PRIMARY KEY (`id`),
  KEY `idx_status` (`alert_status`) USING BTREE,
  KEY `idx_sign` (`sign`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_alert`
--

LOCK TABLES `t_ds_alert` WRITE;
/*!40000 ALTER TABLE `t_ds_alert` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_alert` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_alert_plugin_instance`
--

DROP TABLE IF EXISTS `t_ds_alert_plugin_instance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_alert_plugin_instance` (
  `id` int NOT NULL AUTO_INCREMENT,
  `plugin_define_id` int NOT NULL,
  `plugin_instance_params` text COLLATE utf8mb3_bin COMMENT 'plugin instance params. Also contain the params value which user input in web ui.',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `instance_name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'alert instance name',
  `instance_type` int NOT NULL DEFAULT '0',
  `warning_type` int NOT NULL DEFAULT '3',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_alert_plugin_instance`
--

LOCK TABLES `t_ds_alert_plugin_instance` WRITE;
/*!40000 ALTER TABLE `t_ds_alert_plugin_instance` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_alert_plugin_instance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_alert_send_status`
--

DROP TABLE IF EXISTS `t_ds_alert_send_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_alert_send_status` (
  `id` int NOT NULL AUTO_INCREMENT,
  `alert_id` int NOT NULL,
  `alert_plugin_instance_id` int NOT NULL,
  `send_status` tinyint DEFAULT '0',
  `log` text COLLATE utf8mb3_bin,
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `alert_send_status_unique` (`alert_id`,`alert_plugin_instance_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_alert_send_status`
--

LOCK TABLES `t_ds_alert_send_status` WRITE;
/*!40000 ALTER TABLE `t_ds_alert_send_status` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_alert_send_status` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_alertgroup`
--

DROP TABLE IF EXISTS `t_ds_alertgroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_alertgroup` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `alert_instance_ids` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'alert instance ids',
  `create_user_id` int DEFAULT NULL COMMENT 'create user id',
  `group_name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'group name',
  `description` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `t_ds_alertgroup_name_un` (`group_name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_alertgroup`
--

LOCK TABLES `t_ds_alertgroup` WRITE;
/*!40000 ALTER TABLE `t_ds_alertgroup` DISABLE KEYS */;
INSERT INTO `t_ds_alertgroup` VALUES (1,NULL,1,'default admin warning group','default admin warning group','2026-05-11 07:21:44','2026-05-11 07:21:44'),(2,NULL,1,'global alert group','global alert group','2026-05-11 07:21:44','2026-05-11 07:21:44');
/*!40000 ALTER TABLE `t_ds_alertgroup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_audit_log`
--

DROP TABLE IF EXISTS `t_ds_audit_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_audit_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'key',
  `user_id` int NOT NULL COMMENT 'user id',
  `model_id` bigint DEFAULT NULL COMMENT 'model id',
  `model_name` varchar(100) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'model name',
  `model_type` varchar(100) COLLATE utf8mb3_bin NOT NULL COMMENT 'model type',
  `operation_type` varchar(100) COLLATE utf8mb3_bin NOT NULL COMMENT 'operation type',
  `description` varchar(100) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'api description',
  `latency` int DEFAULT NULL COMMENT 'api cost milliseconds',
  `detail` varchar(100) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'object change detail',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'operation time',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_audit_log`
--

LOCK TABLES `t_ds_audit_log` WRITE;
/*!40000 ALTER TABLE `t_ds_audit_log` DISABLE KEYS */;
INSERT INTO `t_ds_audit_log` VALUES (1,1,173117159418176,'1','Project','Create','CREATE_PROJECT_NOTES',35,NULL,'2026-05-11 17:02:06'),(2,1,173134550293824,'监管报送','Project','Create','CREATE_PROJECT_NOTES',38,NULL,'2026-05-11 21:45:09'),(3,1,173134550388032,'估值数据导入','Project','Create','CREATE_PROJECT_NOTES',9,NULL,'2026-05-11 21:45:09'),(4,1,173117159418176,'默认项目','Project','Update','UPDATE_PROJECT_NOTES',66,NULL,'2026-05-11 21:48:13'),(5,1,173134949053760,'demo01','Process','Create','CREATE_PROCESS_DEFINITION_NOTES',1025,NULL,'2026-05-11 21:51:38'),(6,1,173134949053760,'demo01','Process','Online','RELEASE_PROCESS_DEFINITION_NOTES',168,NULL,'2026-05-11 21:51:45'),(7,1,173135002280256,'1','Process','Create','CREATE_PROCESS_DEFINITION_NOTES',84,NULL,'2026-05-11 21:52:31'),(8,1,173135002280256,'1','Process','Online','RELEASE_PROCESS_DEFINITION_NOTES',17,NULL,'2026-05-11 22:45:54'),(9,1,173135002280256,'1','Schedule','Create','CREATE_SCHEDULE_NOTES',57,'1','2026-05-11 22:45:57'),(10,1,173179744097664,'12','Process','Create','CREATE_PROCESS_DEFINITION_NOTES',60,NULL,'2026-05-12 10:00:44'),(11,1,173183930480000,'e2e_pipeline_002','Process','Create','CREATE_PROCESS_DEFINITION_NOTES',22,NULL,'2026-05-12 11:08:52'),(12,1,173183930480000,'e2e_pipeline_002','Process','Online','RELEASE_PROCESS_DEFINITION_NOTES',8,NULL,'2026-05-12 11:08:52'),(13,1,173183930480000,'e2e_pipeline_002','Schedule','Create','CREATE_SCHEDULE_NOTES',16,'2','2026-05-12 11:08:52'),(14,1,173183930480000,'e2e_pipeline_002','Process','Start','RUN_PROCESS_INSTANCE_NOTES',32,'latest','2026-05-12 11:09:11'),(15,1,173183930480000,'e2e_pipeline_002','Schedule','Online','ONLINE_SCHEDULE_NOTES',55,'2','2026-05-12 11:09:30'),(16,1,173183930480000,'e2e_pipeline_002','Schedule','Offline','OFFLINE_SCHEDULE_NOTES',30,'2','2026-05-12 11:09:31'),(17,1,173183930480000,'e2e_pipeline_002','Process','Offline','RELEASE_PROCESS_DEFINITION_NOTES',8,NULL,'2026-05-12 11:09:31'),(18,1,173183930480000,'e2e_pipeline_002','Schedule','Delete','DELETE_SCHEDULE_NOTES',6,'2','2026-05-12 11:09:31'),(19,1,173183930480000,'e2e_pipeline_002','Process','Offline','RELEASE_PROCESS_DEFINITION_NOTES',2,NULL,'2026-05-12 11:09:31'),(20,1,173183930480000,'e2e_pipeline_002','Process','Delete','DELETE_PROCESS_DEFINITION_BY_ID_NOTES',99,NULL,'2026-05-12 11:09:31'),(21,1,173184205699456,'daily_user_etl','Process','Create','CREATE_PROCESS_DEFINITION_NOTES',20,NULL,'2026-05-12 11:13:21'),(22,1,173184205699456,'daily_user_etl','Process','Online','RELEASE_PROCESS_DEFINITION_NOTES',9,NULL,'2026-05-12 11:13:21'),(23,1,173184205699456,'daily_user_etl','Schedule','Create','CREATE_SCHEDULE_NOTES',11,'3','2026-05-12 11:13:21'),(24,1,173184206033280,'nightly_cleanup','Process','Create','CREATE_PROCESS_DEFINITION_NOTES',18,NULL,'2026-05-12 11:13:21'),(25,1,173184206033280,'nightly_cleanup','Process','Online','RELEASE_PROCESS_DEFINITION_NOTES',7,NULL,'2026-05-12 11:13:21'),(26,1,173184206033280,'nightly_cleanup','Schedule','Create','CREATE_SCHEDULE_NOTES',9,'4','2026-05-12 11:13:21'),(27,1,173184206372224,'user_data_export','Process','Create','CREATE_PROCESS_DEFINITION_NOTES',19,NULL,'2026-05-12 11:13:22'),(28,1,173184206372224,'user_data_export','Process','Online','RELEASE_PROCESS_DEFINITION_NOTES',8,NULL,'2026-05-12 11:13:22'),(29,1,173184205699456,'daily_user_etl','Process','Start','RUN_PROCESS_INSTANCE_NOTES',11,'latest','2026-05-12 11:13:22'),(30,1,173184205699456,'daily_user_etl','Process','Start','RUN_PROCESS_INSTANCE_NOTES',11,'latest','2026-05-12 11:13:23'),(31,1,173184206033280,'nightly_cleanup','Process','Start','RUN_PROCESS_INSTANCE_NOTES',9,'latest','2026-05-12 11:13:24'),(32,1,173184206033280,'nightly_cleanup','Process','Start','RUN_PROCESS_INSTANCE_NOTES',11,'latest','2026-05-12 11:13:25'),(33,1,173184206372224,'user_data_export','Process','Start','RUN_PROCESS_INSTANCE_NOTES',11,'latest','2026-05-12 11:13:26'),(34,1,173278852484480,'测试01','Process','Create','CREATE_PROCESS_DEFINITION_NOTES',20,NULL,'2026-05-13 12:53:49'),(35,1,173278852484480,'测试01','Process','Online','RELEASE_PROCESS_DEFINITION_NOTES',6,NULL,'2026-05-13 12:53:49'),(36,1,173184206033280,'nightly_cleanup','Process','Offline','RELEASE_PROCESS_DEFINITION_NOTES',5,NULL,'2026-05-13 12:54:13'),(37,1,173278852484480,'测试01','Process','Offline','RELEASE_PROCESS_DEFINITION_NOTES',5,NULL,'2026-05-13 12:54:28'),(38,1,6,'user_data_export-1-20260512111327002','Process','Rerun','EXECUTE_ACTION_TO_PROCESS_INSTANCE_NOTES',15,NULL,'2026-05-13 14:07:58'),(39,1,5,'nightly_cleanup-1-20260512111324988','Process','Rerun','EXECUTE_ACTION_TO_PROCESS_INSTANCE_NOTES',6,NULL,'2026-05-13 14:08:09'),(40,1,173285883084160,'002','Process','Create','CREATE_PROCESS_DEFINITION_NOTES',11,NULL,'2026-05-13 14:48:15'),(41,1,173285883084160,'002','Process','Online','RELEASE_PROCESS_DEFINITION_NOTES',6,NULL,'2026-05-13 14:48:15'),(42,1,173285883084160,'002','Process','Start','RUN_PROCESS_INSTANCE_NOTES',8,'latest','2026-05-13 15:12:47'),(43,1,173285883084160,'002','Process','Start','RUN_PROCESS_INSTANCE_NOTES',7,'latest','2026-05-13 15:12:59');
/*!40000 ALTER TABLE `t_ds_audit_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_cluster`
--

DROP TABLE IF EXISTS `t_ds_cluster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_cluster` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'id',
  `code` bigint DEFAULT NULL COMMENT 'encoding',
  `name` varchar(255) COLLATE utf8mb3_bin NOT NULL COMMENT 'cluster name',
  `config` text COLLATE utf8mb3_bin COMMENT 'this config contains many cluster variables config',
  `description` text COLLATE utf8mb3_bin COMMENT 'the details',
  `operator` int DEFAULT NULL COMMENT 'operator user id',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `cluster_name_unique` (`name`),
  UNIQUE KEY `cluster_code_unique` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_cluster`
--

LOCK TABLES `t_ds_cluster` WRITE;
/*!40000 ALTER TABLE `t_ds_cluster` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_cluster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_command`
--

DROP TABLE IF EXISTS `t_ds_command`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_command` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `command_type` tinyint DEFAULT NULL COMMENT 'Command type: 0 start workflow, 1 start execution from current node, 2 resume fault-tolerant workflow, 3 resume pause process, 4 start execution from failed node, 5 complement, 6 schedule, 7 rerun, 8 pause, 9 stop, 10 resume waiting thread',
  `process_definition_code` bigint NOT NULL COMMENT 'process definition code',
  `process_definition_version` int DEFAULT '0' COMMENT 'process definition version',
  `process_instance_id` int DEFAULT '0' COMMENT 'process instance id',
  `command_param` text COLLATE utf8mb3_bin COMMENT 'json command parameters',
  `task_depend_type` tinyint DEFAULT NULL COMMENT 'Node dependency type: 0 current node, 1 forward, 2 backward',
  `failure_strategy` tinyint DEFAULT '0' COMMENT 'Failed policy: 0 end, 1 continue',
  `warning_type` tinyint DEFAULT '0' COMMENT 'Alarm type: 0 is not sent, 1 process is sent successfully, 2 process is sent failed, 3 process is sent successfully and all failures are sent',
  `warning_group_id` int DEFAULT NULL COMMENT 'warning group',
  `schedule_time` datetime DEFAULT NULL COMMENT 'schedule time',
  `start_time` datetime DEFAULT NULL COMMENT 'start time',
  `executor_id` int DEFAULT NULL COMMENT 'executor id',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  `process_instance_priority` int DEFAULT '2' COMMENT 'process instance priority: 0 Highest,1 High,2 Medium,3 Low,4 Lowest',
  `worker_group` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'worker group',
  `tenant_code` varchar(64) COLLATE utf8mb3_bin DEFAULT 'default' COMMENT 'tenant code',
  `environment_code` bigint DEFAULT '-1' COMMENT 'environment code',
  `dry_run` tinyint DEFAULT '0' COMMENT 'dry run flagï¼š0 normal, 1 dry run',
  `test_flag` tinyint DEFAULT NULL COMMENT 'test flagï¼š0 normal, 1 test run',
  PRIMARY KEY (`id`),
  KEY `priority_id_index` (`process_instance_priority`,`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_command`
--

LOCK TABLES `t_ds_command` WRITE;
/*!40000 ALTER TABLE `t_ds_command` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_command` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_datasource`
--

DROP TABLE IF EXISTS `t_ds_datasource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_datasource` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `name` varchar(64) COLLATE utf8mb3_bin NOT NULL COMMENT 'data source name',
  `note` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'description',
  `type` tinyint NOT NULL COMMENT 'data source type: 0:mysql,1:postgresql,2:hive,3:spark',
  `user_id` int NOT NULL COMMENT 'the creator id',
  `connection_params` text COLLATE utf8mb3_bin NOT NULL COMMENT 'json connection params',
  `create_time` datetime NOT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `t_ds_datasource_name_un` (`name`,`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_datasource`
--

LOCK TABLES `t_ds_datasource` WRITE;
/*!40000 ALTER TABLE `t_ds_datasource` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_datasource` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_dq_comparison_type`
--

DROP TABLE IF EXISTS `t_ds_dq_comparison_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_dq_comparison_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(255) COLLATE utf8mb3_bin NOT NULL,
  `execute_sql` text COLLATE utf8mb3_bin,
  `output_table` varchar(100) COLLATE utf8mb3_bin DEFAULT NULL,
  `name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `is_inner_source` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_dq_comparison_type`
--

LOCK TABLES `t_ds_dq_comparison_type` WRITE;
/*!40000 ALTER TABLE `t_ds_dq_comparison_type` DISABLE KEYS */;
INSERT INTO `t_ds_dq_comparison_type` VALUES (1,'FixValue',NULL,NULL,NULL,'2026-05-11 07:21:45','2026-05-11 07:21:45',0),(2,'DailyAvg','select round(avg(statistics_value),2) as day_avg from t_ds_dq_task_statistics_value where data_time >=date_trunc(\'DAY\', ${data_time}) and data_time < date_add(date_trunc(\'day\', ${data_time}),1) and unique_code = ${unique_code} and statistics_name = \'${statistics_name}\'','day_range','day_range.day_avg','2026-05-11 07:21:45','2026-05-11 07:21:45',1),(3,'WeeklyAvg','select round(avg(statistics_value),2) as week_avg from t_ds_dq_task_statistics_value where  data_time >= date_trunc(\'WEEK\', ${data_time}) and data_time <date_trunc(\'day\', ${data_time}) and unique_code = ${unique_code} and statistics_name = \'${statistics_name}\'','week_range','week_range.week_avg','2026-05-11 07:21:45','2026-05-11 07:21:45',1),(4,'MonthlyAvg','select round(avg(statistics_value),2) as month_avg from t_ds_dq_task_statistics_value where  data_time >= date_trunc(\'MONTH\', ${data_time}) and data_time <date_trunc(\'day\', ${data_time}) and unique_code = ${unique_code} and statistics_name = \'${statistics_name}\'','month_range','month_range.month_avg','2026-05-11 07:21:45','2026-05-11 07:21:45',1),(5,'Last7DayAvg','select round(avg(statistics_value),2) as last_7_avg from t_ds_dq_task_statistics_value where  data_time >= date_add(date_trunc(\'day\', ${data_time}),-7) and  data_time <date_trunc(\'day\', ${data_time}) and unique_code = ${unique_code} and statistics_name = \'${statistics_name}\'','last_seven_days','last_seven_days.last_7_avg','2026-05-11 07:21:45','2026-05-11 07:21:45',1),(6,'Last30DayAvg','select round(avg(statistics_value),2) as last_30_avg from t_ds_dq_task_statistics_value where  data_time >= date_add(date_trunc(\'day\', ${data_time}),-30) and  data_time < date_trunc(\'day\', ${data_time}) and unique_code = ${unique_code} and statistics_name = \'${statistics_name}\'','last_thirty_days','last_thirty_days.last_30_avg','2026-05-11 07:21:45','2026-05-11 07:21:45',1),(7,'SrcTableTotalRows','SELECT COUNT(*) AS total FROM ${src_table} WHERE (${src_filter})','total_count','total_count.total','2026-05-11 07:21:45','2026-05-11 07:21:45',0),(8,'TargetTableTotalRows','SELECT COUNT(*) AS total FROM ${target_table} WHERE (${target_filter})','total_count','total_count.total','2026-05-11 07:21:45','2026-05-11 07:21:45',0);
/*!40000 ALTER TABLE `t_ds_dq_comparison_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_dq_execute_result`
--

DROP TABLE IF EXISTS `t_ds_dq_execute_result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_dq_execute_result` (
  `id` int NOT NULL AUTO_INCREMENT,
  `process_definition_id` int DEFAULT NULL,
  `process_instance_id` int DEFAULT NULL,
  `task_instance_id` int DEFAULT NULL,
  `rule_type` int DEFAULT NULL,
  `rule_name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `statistics_value` double DEFAULT NULL,
  `comparison_value` double DEFAULT NULL,
  `check_type` int DEFAULT NULL,
  `threshold` double DEFAULT NULL,
  `operator` int DEFAULT NULL,
  `failure_strategy` int DEFAULT NULL,
  `state` int DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  `comparison_type` int DEFAULT NULL,
  `error_output_path` text COLLATE utf8mb3_bin,
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_dq_execute_result`
--

LOCK TABLES `t_ds_dq_execute_result` WRITE;
/*!40000 ALTER TABLE `t_ds_dq_execute_result` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_dq_execute_result` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_dq_rule`
--

DROP TABLE IF EXISTS `t_ds_dq_rule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_dq_rule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `type` int DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_dq_rule`
--

LOCK TABLES `t_ds_dq_rule` WRITE;
/*!40000 ALTER TABLE `t_ds_dq_rule` DISABLE KEYS */;
INSERT INTO `t_ds_dq_rule` VALUES (1,'$t(null_check)',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(2,'$t(custom_sql)',1,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(3,'$t(multi_table_accuracy)',2,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(4,'$t(multi_table_value_comparison)',3,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(5,'$t(field_length_check)',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(6,'$t(uniqueness_check)',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(7,'$t(regexp_check)',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(8,'$t(timeliness_check)',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(9,'$t(enumeration_check)',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(10,'$t(table_count_check)',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45');
/*!40000 ALTER TABLE `t_ds_dq_rule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_dq_rule_execute_sql`
--

DROP TABLE IF EXISTS `t_ds_dq_rule_execute_sql`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_dq_rule_execute_sql` (
  `id` int NOT NULL AUTO_INCREMENT,
  `index` int DEFAULT NULL,
  `sql` text COLLATE utf8mb3_bin,
  `table_alias` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `type` int DEFAULT NULL,
  `is_error_output_sql` tinyint(1) DEFAULT '0',
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_dq_rule_execute_sql`
--

LOCK TABLES `t_ds_dq_rule_execute_sql` WRITE;
/*!40000 ALTER TABLE `t_ds_dq_rule_execute_sql` DISABLE KEYS */;
INSERT INTO `t_ds_dq_rule_execute_sql` VALUES (1,1,'SELECT COUNT(*) AS nulls FROM null_items','null_count',1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(2,1,'SELECT COUNT(*) AS total FROM ${src_table} WHERE (${src_filter})','total_count',2,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(3,1,'SELECT COUNT(*) AS miss from miss_items','miss_count',1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(4,1,'SELECT COUNT(*) AS valids FROM invalid_length_items','invalid_length_count',1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(5,1,'SELECT COUNT(*) AS total FROM ${target_table} WHERE (${target_filter})','total_count',2,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(6,1,'SELECT ${src_field} FROM ${src_table} group by ${src_field} having count(*) > 1','duplicate_items',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(7,1,'SELECT COUNT(*) AS duplicates FROM duplicate_items','duplicate_count',1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(8,1,'SELECT ${src_table}.* FROM (SELECT * FROM ${src_table} WHERE (${src_filter})) ${src_table} LEFT JOIN (SELECT * FROM ${target_table} WHERE (${target_filter})) ${target_table} ON ${on_clause} WHERE ${where_clause}','miss_items',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(9,1,'SELECT * FROM ${src_table} WHERE (${src_field} not regexp \'${regexp_pattern}\') AND (${src_filter}) ','regexp_items',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(10,1,'SELECT COUNT(*) AS regexps FROM regexp_items','regexp_count',1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(11,1,'SELECT * FROM ${src_table} WHERE (to_unix_timestamp(${src_field}, \'${datetime_format}\')-to_unix_timestamp(\'${deadline}\', \'${datetime_format}\') <= 0) AND (to_unix_timestamp(${src_field}, \'${datetime_format}\')-to_unix_timestamp(\'${begin_time}\', \'${datetime_format}\') >= 0) AND (${src_filter}) ','timeliness_items',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(12,1,'SELECT COUNT(*) AS timeliness FROM timeliness_items','timeliness_count',1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(13,1,'SELECT * FROM ${src_table} where (${src_field} not in ( ${enum_list} ) or ${src_field} is null) AND (${src_filter}) ','enum_items',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(14,1,'SELECT COUNT(*) AS enums FROM enum_items','enum_count',1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(15,1,'SELECT COUNT(*) AS total FROM ${src_table} WHERE (${src_filter})','table_count',1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(16,1,'SELECT * FROM ${src_table} WHERE (${src_field} is null or ${src_field} = \'\') AND (${src_filter})','null_items',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(17,1,'SELECT * FROM ${src_table} WHERE (length(${src_field}) ${logic_operator} ${field_length}) AND (${src_filter})','invalid_length_items',0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45');
/*!40000 ALTER TABLE `t_ds_dq_rule_execute_sql` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_dq_rule_input_entry`
--

DROP TABLE IF EXISTS `t_ds_dq_rule_input_entry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_dq_rule_input_entry` (
  `id` int NOT NULL AUTO_INCREMENT,
  `field` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `type` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `title` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `data` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `options` text COLLATE utf8mb3_bin,
  `placeholder` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `option_source_type` int DEFAULT NULL,
  `data_type` int DEFAULT NULL,
  `input_type` int DEFAULT NULL,
  `is_show` tinyint(1) DEFAULT '1',
  `can_edit` tinyint(1) DEFAULT '1',
  `is_emit` tinyint(1) DEFAULT '0',
  `is_validate` tinyint(1) DEFAULT '1',
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_dq_rule_input_entry`
--

LOCK TABLES `t_ds_dq_rule_input_entry` WRITE;
/*!40000 ALTER TABLE `t_ds_dq_rule_input_entry` DISABLE KEYS */;
INSERT INTO `t_ds_dq_rule_input_entry` VALUES (1,'src_connector_type','select','$t(src_connector_type)','','[{\"label\":\"HIVE\",\"value\":\"HIVE\"},{\"label\":\"JDBC\",\"value\":\"JDBC\"}]','please select source connector type',2,2,0,1,1,1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(2,'src_datasource_id','select','$t(src_datasource_id)','',NULL,'please select source datasource id',1,2,0,1,1,1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(3,'src_table','select','$t(src_table)',NULL,NULL,'Please enter source table name',0,0,0,1,1,1,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(4,'src_filter','input','$t(src_filter)',NULL,NULL,'Please enter filter expression',0,3,0,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(5,'src_field','select','$t(src_field)',NULL,NULL,'Please enter column, only single column is supported',0,0,0,1,1,0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(6,'statistics_name','input','$t(statistics_name)',NULL,NULL,'Please enter statistics name, the alias in statistics execute sql',0,0,1,0,0,0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(7,'check_type','select','$t(check_type)','0','[{\"label\":\"Expected - Actual\",\"value\":\"0\"},{\"label\":\"Actual - Expected\",\"value\":\"1\"},{\"label\":\"Actual / Expected\",\"value\":\"2\"},{\"label\":\"(Expected - Actual) / Expected\",\"value\":\"3\"}]','please select check type',0,0,3,1,1,1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(8,'operator','select','$t(operator)','0','[{\"label\":\"=\",\"value\":\"0\"},{\"label\":\"<\",\"value\":\"1\"},{\"label\":\"<=\",\"value\":\"2\"},{\"label\":\">\",\"value\":\"3\"},{\"label\":\">=\",\"value\":\"4\"},{\"label\":\"!=\",\"value\":\"5\"}]','please select operator',0,0,3,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(9,'threshold','input','$t(threshold)',NULL,NULL,'Please enter threshold, number is needed',0,2,3,1,1,0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(10,'failure_strategy','select','$t(failure_strategy)','0','[{\"label\":\"Alert\",\"value\":\"0\"},{\"label\":\"Block\",\"value\":\"1\"}]','please select failure strategy',0,0,3,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(11,'target_connector_type','select','$t(target_connector_type)','','[{\"label\":\"HIVE\",\"value\":\"HIVE\"},{\"label\":\"JDBC\",\"value\":\"JDBC\"}]','Please select target connector type',2,0,0,1,1,1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(12,'target_datasource_id','select','$t(target_datasource_id)','',NULL,'Please select target datasource',1,2,0,1,1,1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(13,'target_table','select','$t(target_table)',NULL,NULL,'Please enter target table',0,0,0,1,1,1,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(14,'target_filter','input','$t(target_filter)',NULL,NULL,'Please enter target filter expression',0,3,0,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(15,'mapping_columns','group','$t(mapping_columns)',NULL,'[{\"field\":\"src_field\",\"props\":{\"placeholder\":\"Please input src field\",\"rows\":0,\"disabled\":false,\"size\":\"small\"},\"type\":\"input\",\"title\":\"src_field\"},{\"field\":\"operator\",\"props\":{\"placeholder\":\"Please input operator\",\"rows\":0,\"disabled\":false,\"size\":\"small\"},\"type\":\"input\",\"title\":\"operator\"},{\"field\":\"target_field\",\"props\":{\"placeholder\":\"Please input target field\",\"rows\":0,\"disabled\":false,\"size\":\"small\"},\"type\":\"input\",\"title\":\"target_field\"}]','please enter mapping columns',0,0,0,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(16,'statistics_execute_sql','textarea','$t(statistics_execute_sql)',NULL,NULL,'Please enter statistics execute sql',0,3,0,1,1,0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(17,'comparison_name','input','$t(comparison_name)',NULL,NULL,'Please enter comparison name, the alias in comparison execute sql',0,0,0,0,0,0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(18,'comparison_execute_sql','textarea','$t(comparison_execute_sql)',NULL,NULL,'Please enter comparison execute sql',0,3,0,1,1,0,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(19,'comparison_type','select','$t(comparison_type)','',NULL,'Please enter comparison title',3,0,2,1,0,1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(20,'writer_connector_type','select','$t(writer_connector_type)','','[{\"label\":\"MYSQL\",\"value\":\"0\"},{\"label\":\"POSTGRESQL\",\"value\":\"1\"}]','please select writer connector type',0,2,0,1,1,1,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(21,'writer_datasource_id','select','$t(writer_datasource_id)','',NULL,'please select writer datasource id',1,2,0,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(22,'target_field','select','$t(target_field)',NULL,NULL,'Please enter column, only single column is supported',0,0,0,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(23,'field_length','input','$t(field_length)',NULL,NULL,'Please enter length limit',0,3,0,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(24,'logic_operator','select','$t(logic_operator)','=','[{\"label\":\"=\",\"value\":\"=\"},{\"label\":\"<\",\"value\":\"<\"},{\"label\":\"<=\",\"value\":\"<=\"},{\"label\":\">\",\"value\":\">\"},{\"label\":\">=\",\"value\":\">=\"},{\"label\":\"<>\",\"value\":\"<>\"}]','please select logic operator',0,0,3,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(25,'regexp_pattern','input','$t(regexp_pattern)',NULL,NULL,'Please enter regexp pattern',0,0,0,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(26,'deadline','input','$t(deadline)',NULL,NULL,'Please enter deadline',0,0,0,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(27,'datetime_format','input','$t(datetime_format)',NULL,NULL,'Please enter datetime format',0,0,0,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(28,'enum_list','input','$t(enum_list)',NULL,NULL,'Please enter enumeration',0,0,0,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(29,'begin_time','input','$t(begin_time)',NULL,NULL,'Please enter begin time',0,0,0,1,1,0,0,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(30,'src_database','select','$t(src_database)',NULL,NULL,'Please select source database',0,0,0,1,1,1,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(31,'target_database','select','$t(target_database)',NULL,NULL,'Please select target database',0,0,0,1,1,1,1,'2026-05-11 07:21:45','2026-05-11 07:21:45');
/*!40000 ALTER TABLE `t_ds_dq_rule_input_entry` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_dq_task_statistics_value`
--

DROP TABLE IF EXISTS `t_ds_dq_task_statistics_value`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_dq_task_statistics_value` (
  `id` int NOT NULL AUTO_INCREMENT,
  `process_definition_id` int DEFAULT NULL,
  `task_instance_id` int DEFAULT NULL,
  `rule_id` int NOT NULL,
  `unique_code` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `statistics_name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `statistics_value` double DEFAULT NULL,
  `data_time` datetime DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_dq_task_statistics_value`
--

LOCK TABLES `t_ds_dq_task_statistics_value` WRITE;
/*!40000 ALTER TABLE `t_ds_dq_task_statistics_value` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_dq_task_statistics_value` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_environment`
--

DROP TABLE IF EXISTS `t_ds_environment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_environment` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'id',
  `code` bigint DEFAULT NULL COMMENT 'encoding',
  `name` varchar(255) COLLATE utf8mb3_bin NOT NULL COMMENT 'environment name',
  `config` text COLLATE utf8mb3_bin COMMENT 'this config contains many environment variables config',
  `description` text COLLATE utf8mb3_bin COMMENT 'the details',
  `operator` int DEFAULT NULL COMMENT 'operator user id',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `environment_name_unique` (`name`),
  UNIQUE KEY `environment_code_unique` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_environment`
--

LOCK TABLES `t_ds_environment` WRITE;
/*!40000 ALTER TABLE `t_ds_environment` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_environment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_environment_worker_group_relation`
--

DROP TABLE IF EXISTS `t_ds_environment_worker_group_relation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_environment_worker_group_relation` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'id',
  `environment_code` bigint NOT NULL COMMENT 'environment code',
  `worker_group` varchar(255) COLLATE utf8mb3_bin NOT NULL COMMENT 'worker group id',
  `operator` int DEFAULT NULL COMMENT 'operator user id',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `environment_worker_group_unique` (`environment_code`,`worker_group`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_environment_worker_group_relation`
--

LOCK TABLES `t_ds_environment_worker_group_relation` WRITE;
/*!40000 ALTER TABLE `t_ds_environment_worker_group_relation` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_environment_worker_group_relation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_error_command`
--

DROP TABLE IF EXISTS `t_ds_error_command`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_error_command` (
  `id` int NOT NULL COMMENT 'key',
  `command_type` tinyint DEFAULT NULL COMMENT 'command type',
  `executor_id` int DEFAULT NULL COMMENT 'executor id',
  `process_definition_code` bigint NOT NULL COMMENT 'process definition code',
  `process_definition_version` int DEFAULT '0' COMMENT 'process definition version',
  `process_instance_id` int DEFAULT '0' COMMENT 'process instance id: 0',
  `command_param` text COLLATE utf8mb3_bin COMMENT 'json command parameters',
  `task_depend_type` tinyint DEFAULT NULL COMMENT 'task depend type',
  `failure_strategy` tinyint DEFAULT '0' COMMENT 'failure strategy',
  `warning_type` tinyint DEFAULT '0' COMMENT 'warning type',
  `warning_group_id` int DEFAULT NULL COMMENT 'warning group id',
  `schedule_time` datetime DEFAULT NULL COMMENT 'scheduler time',
  `start_time` datetime DEFAULT NULL COMMENT 'start time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  `process_instance_priority` int DEFAULT '2' COMMENT 'process instance priority, 0 Highest,1 High,2 Medium,3 Low,4 Lowest',
  `worker_group` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'worker group',
  `tenant_code` varchar(64) COLLATE utf8mb3_bin DEFAULT 'default' COMMENT 'tenant code',
  `environment_code` bigint DEFAULT '-1' COMMENT 'environment code',
  `message` text COLLATE utf8mb3_bin COMMENT 'message',
  `dry_run` tinyint DEFAULT '0' COMMENT 'dry run flag: 0 normal, 1 dry run',
  `test_flag` tinyint DEFAULT NULL COMMENT 'test flagï¼š0 normal, 1 test run',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_error_command`
--

LOCK TABLES `t_ds_error_command` WRITE;
/*!40000 ALTER TABLE `t_ds_error_command` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_error_command` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_fav_task`
--

DROP TABLE IF EXISTS `t_ds_fav_task`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_fav_task` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'id',
  `task_type` varchar(64) COLLATE utf8mb3_bin NOT NULL COMMENT 'favorite task type name',
  `user_id` int NOT NULL COMMENT 'user id',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_fav_task`
--

LOCK TABLES `t_ds_fav_task` WRITE;
/*!40000 ALTER TABLE `t_ds_fav_task` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_fav_task` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_k8s`
--

DROP TABLE IF EXISTS `t_ds_k8s`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_k8s` (
  `id` int NOT NULL AUTO_INCREMENT,
  `k8s_name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `k8s_config` text COLLATE utf8mb3_bin,
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_k8s`
--

LOCK TABLES `t_ds_k8s` WRITE;
/*!40000 ALTER TABLE `t_ds_k8s` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_k8s` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_k8s_namespace`
--

DROP TABLE IF EXISTS `t_ds_k8s_namespace`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_k8s_namespace` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` bigint NOT NULL DEFAULT '0',
  `namespace` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  `cluster_code` bigint NOT NULL DEFAULT '0',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `k8s_namespace_unique` (`namespace`,`cluster_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_k8s_namespace`
--

LOCK TABLES `t_ds_k8s_namespace` WRITE;
/*!40000 ALTER TABLE `t_ds_k8s_namespace` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_k8s_namespace` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_listener_event`
--

DROP TABLE IF EXISTS `t_ds_listener_event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_listener_event` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `content` text COLLATE utf8mb3_bin COMMENT 'listener event json content',
  `sign` char(64) COLLATE utf8mb3_bin NOT NULL DEFAULT '' COMMENT 'sign=sha1(content)',
  `post_status` tinyint NOT NULL DEFAULT '0' COMMENT '0:wait running,1:success,2:failed,3:partial success',
  `event_type` int NOT NULL COMMENT 'listener event type',
  `log` text COLLATE utf8mb3_bin COMMENT 'log',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  KEY `idx_status` (`post_status`) USING BTREE,
  KEY `idx_sign` (`sign`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_listener_event`
--

LOCK TABLES `t_ds_listener_event` WRITE;
/*!40000 ALTER TABLE `t_ds_listener_event` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_listener_event` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_plugin_define`
--

DROP TABLE IF EXISTS `t_ds_plugin_define`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_plugin_define` (
  `id` int NOT NULL AUTO_INCREMENT,
  `plugin_name` varchar(255) COLLATE utf8mb3_bin NOT NULL COMMENT 'the name of plugin eg: email',
  `plugin_type` varchar(63) COLLATE utf8mb3_bin NOT NULL COMMENT 'plugin type . alert=alert plugin, job=job plugin',
  `plugin_params` text COLLATE utf8mb3_bin COMMENT 'plugin params',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `t_ds_plugin_define_UN` (`plugin_name`,`plugin_type`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_plugin_define`
--

LOCK TABLES `t_ds_plugin_define` WRITE;
/*!40000 ALTER TABLE `t_ds_plugin_define` DISABLE KEYS */;
INSERT INTO `t_ds_plugin_define` VALUES (2,'Prometheus AlertManager','alert','[{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input request URL\",\"size\":\"small\"},\"field\":\"url\",\"name\":\"$t(\'url\')\",\"type\":\"input\",\"title\":\"$t(\'url\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"please input annotation in json form\",\"size\":\"small\"},\"field\":\"annotations\",\"name\":\"$t(\'annotations\')\",\"type\":\"input\",\"title\":\"$t(\'annotations\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"please input Generator URL\",\"size\":\"small\"},\"field\":\"generatorURL\",\"name\":\"$t(\'generatorURL\')\",\"type\":\"input\",\"title\":\"$t(\'generatorURL\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null}]','2026-05-11 15:22:25','2026-05-11 15:22:25'),(3,'Script','alert','[{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"the custom parameters passed when calling scripts\",\"size\":\"small\"},\"field\":\"userParams\",\"name\":\"$t(\'userParams\')\",\"type\":\"input\",\"title\":\"$t(\'userParams\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"the absolute script path under alert-server, and make sure access rights\",\"size\":\"small\"},\"field\":\"path\",\"name\":\"$t(\'scriptPath\')\",\"type\":\"input\",\"title\":\"$t(\'scriptPath\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"type\",\"name\":\"$t(\'scriptType\')\",\"type\":\"radio\",\"title\":\"$t(\'scriptType\')\",\"value\":\"SHELL\",\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"SHELL\",\"value\":\"SHELL\",\"disabled\":false}]}]','2026-05-11 15:22:25','2026-05-11 15:22:25'),(4,'Telegram','alert','[{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input WebHook Url\",\"size\":\"small\"},\"field\":\"webHook\",\"name\":\"$t(\'webHook\')\",\"type\":\"input\",\"title\":\"$t(\'webHook\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input bot access token\",\"size\":\"small\"},\"field\":\"botToken\",\"name\":\"botToken\",\"type\":\"input\",\"title\":\"botToken\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input telegram channel chat id\",\"size\":\"small\"},\"field\":\"chatId\",\"name\":\"chatId\",\"type\":\"input\",\"title\":\"chatId\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"field\":\"parseMode\",\"name\":\"parseMode\",\"props\":{\"disabled\":null,\"placeholder\":null,\"size\":\"small\"},\"type\":\"select\",\"title\":\"parseMode\",\"value\":\"Txt\",\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"Txt\",\"value\":\"Txt\",\"disabled\":false},{\"label\":\"Markdown\",\"value\":\"Markdown\",\"disabled\":false},{\"label\":\"MarkdownV2\",\"value\":\"MarkdownV2\",\"disabled\":false},{\"label\":\"Html\",\"value\":\"Html\",\"disabled\":false}]},{\"props\":null,\"field\":\"IsEnableProxy\",\"name\":\"$t(\'isEnableProxy\')\",\"type\":\"radio\",\"title\":\"$t(\'isEnableProxy\')\",\"value\":\"false\",\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"YES\",\"value\":\"true\",\"disabled\":false},{\"label\":\"NO\",\"value\":\"false\",\"disabled\":false}]},{\"props\":null,\"field\":\"Proxy\",\"name\":\"$t(\'proxy\')\",\"type\":\"input\",\"title\":\"$t(\'proxy\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"Port\",\"name\":\"$t(\'port\')\",\"type\":\"input-number\",\"title\":\"$t(\'port\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"number\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"User\",\"name\":\"$t(\'user\')\",\"type\":\"input\",\"title\":\"$t(\'user\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":\"password\",\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"if enable use authentication, you need input password\",\"size\":\"small\"},\"field\":\"Password\",\"name\":\"$t(\'password\')\",\"type\":\"input\",\"title\":\"$t(\'password\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null}]','2026-05-11 15:22:25','2026-05-11 15:22:25'),(5,'WeChat','alert','[{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"please input corp id\",\"size\":\"small\"},\"field\":\"corpId\",\"name\":\"$t(\'corpId\')\",\"type\":\"input\",\"title\":\"$t(\'corpId\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"please input secret\",\"size\":\"small\"},\"field\":\"secret\",\"name\":\"$t(\'secret\')\",\"type\":\"input\",\"title\":\"$t(\'secret\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"use `|` to separate userIds and `@all` to everyone\",\"size\":\"small\"},\"field\":\"users\",\"name\":\"$t(\'users\')\",\"type\":\"input\",\"title\":\"$t(\'users\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"please input agent id or chat id\",\"size\":\"small\"},\"field\":\"agentId/chatId\",\"name\":\"$t(\'agentId/chatId\')\",\"type\":\"input\",\"title\":\"$t(\'agentId/chatId\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"sendType\",\"name\":\"send.type\",\"type\":\"radio\",\"title\":\"send.type\",\"value\":\"APP/应用\",\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"APP/应用\",\"value\":\"APP/应用\",\"disabled\":false},{\"label\":\"GROUP CHAT/群聊\",\"value\":\"GROUP CHAT/群聊\",\"disabled\":false}]},{\"props\":null,\"field\":\"showType\",\"name\":\"$t(\'showType\')\",\"type\":\"radio\",\"title\":\"$t(\'showType\')\",\"value\":\"markdown\",\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"markdown\",\"value\":\"markdown\",\"disabled\":false},{\"label\":\"text\",\"value\":\"text\",\"disabled\":false}]}]','2026-05-11 15:22:25','2026-05-11 15:22:25'),(6,'Email','alert','[{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"please input receivers\",\"size\":\"small\"},\"field\":\"receivers\",\"name\":\"$t(\'receivers\')\",\"type\":\"input\",\"title\":\"$t(\'receivers\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"receiverCcs\",\"name\":\"$t(\'receiverCcs\')\",\"type\":\"input\",\"title\":\"$t(\'receiverCcs\')\",\"value\":null,\"validate\":null,\"emit\":null},{\"props\":null,\"field\":\"serverHost\",\"name\":\"mail.smtp.host\",\"type\":\"input\",\"title\":\"mail.smtp.host\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"serverPort\",\"name\":\"mail.smtp.port\",\"type\":\"input-number\",\"title\":\"mail.smtp.port\",\"value\":25,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"number\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"sender\",\"name\":\"$t(\'mailSender\')\",\"type\":\"input\",\"title\":\"$t(\'mailSender\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"enableSmtpAuth\",\"name\":\"mail.smtp.auth\",\"type\":\"radio\",\"title\":\"mail.smtp.auth\",\"value\":\"true\",\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"YES\",\"value\":\"true\",\"disabled\":false},{\"label\":\"NO\",\"value\":\"false\",\"disabled\":false}]},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"if enable use authentication, you need input user\",\"size\":\"small\"},\"field\":\"User\",\"name\":\"$t(\'mailUser\')\",\"type\":\"input\",\"title\":\"$t(\'mailUser\')\",\"value\":null,\"validate\":null,\"emit\":null},{\"props\":{\"disabled\":null,\"type\":\"password\",\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"if enable use authentication, you need input password\",\"size\":\"small\"},\"field\":\"Password\",\"name\":\"$t(\'mailPasswd\')\",\"type\":\"input\",\"title\":\"$t(\'mailPasswd\')\",\"value\":null,\"validate\":null,\"emit\":null},{\"props\":null,\"field\":\"starttlsEnable\",\"name\":\"mail.smtp.starttls.enable\",\"type\":\"radio\",\"title\":\"mail.smtp.starttls.enable\",\"value\":\"false\",\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"YES\",\"value\":\"true\",\"disabled\":false},{\"label\":\"NO\",\"value\":\"false\",\"disabled\":false}]},{\"props\":null,\"field\":\"sslEnable\",\"name\":\"mail.smtp.ssl.enable\",\"type\":\"radio\",\"title\":\"mail.smtp.ssl.enable\",\"value\":\"false\",\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"YES\",\"value\":\"true\",\"disabled\":false},{\"label\":\"NO\",\"value\":\"false\",\"disabled\":false}]},{\"props\":null,\"field\":\"smtpSslTrust\",\"name\":\"mail.smtp.ssl.trust\",\"type\":\"input\",\"title\":\"mail.smtp.ssl.trust\",\"value\":\"*\",\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"showType\",\"name\":\"$t(\'showType\')\",\"type\":\"radio\",\"title\":\"$t(\'showType\')\",\"value\":\"table\",\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"table\",\"value\":\"table\",\"disabled\":false},{\"label\":\"text\",\"value\":\"text\",\"disabled\":false},{\"label\":\"attachment\",\"value\":\"attachment\",\"disabled\":false},{\"label\":\"table attachment\",\"value\":\"table attachment\",\"disabled\":false}]}]','2026-05-11 15:22:25','2026-05-11 15:22:25'),(7,'Slack','alert','[{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input WebHook Url\",\"size\":\"small\"},\"field\":\"webHook\",\"name\":\"$t(\'webhook\')\",\"type\":\"input\",\"title\":\"$t(\'webhook\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input the bot username\",\"size\":\"small\"},\"field\":\"username\",\"name\":\"$t(\'Username\')\",\"type\":\"input\",\"title\":\"$t(\'Username\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null}]','2026-05-11 15:22:25','2026-05-11 15:22:25'),(8,'AliyunVoice','alert','[{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"please input called number\",\"size\":\"small\"},\"field\":\"calledNumber\",\"name\":\"$t(\'calledNumber\')\",\"type\":\"input\",\"title\":\"$t(\'calledNumber\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"Please enter the call display number (the default number will be used if you do not fill in)\",\"size\":\"small\"},\"field\":\"calledShowNumber\",\"name\":\"$t(\'calledShowNumber\')\",\"type\":\"input\",\"title\":\"$t(\'calledShowNumber\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"please input tts code\",\"size\":\"small\"},\"field\":\"ttsCode\",\"name\":\"$t(\'ttsCode\')\",\"type\":\"input\",\"title\":\"$t(\'ttsCode\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"please input aliyun viice address\",\"size\":\"small\"},\"field\":\"address\",\"name\":\"$t(\'address\')\",\"type\":\"input\",\"title\":\"$t(\'address\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"please input accessKeyId\",\"size\":\"small\"},\"field\":\"accessKeyId\",\"name\":\"$t(\'accessKeyId\')\",\"type\":\"input\",\"title\":\"$t(\'accessKeyId\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"please input accessKeySecret\",\"size\":\"small\"},\"field\":\"accessKeySecret\",\"name\":\"$t(\'accessKeySecret\')\",\"type\":\"input\",\"title\":\"$t(\'accessKeySecret\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null}]','2026-05-11 15:22:25','2026-05-11 15:22:25'),(9,'Feishu','alert','[{\"props\":null,\"field\":\"WebHook\",\"name\":\"$t(\'webhook\')\",\"type\":\"input\",\"title\":\"$t(\'webhook\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"IsEnableProxy\",\"name\":\"$t(\'isEnableProxy\')\",\"type\":\"radio\",\"title\":\"$t(\'isEnableProxy\')\",\"value\":\"true\",\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"YES\",\"value\":\"true\",\"disabled\":false},{\"label\":\"NO\",\"value\":\"false\",\"disabled\":false}]},{\"props\":null,\"field\":\"Proxy\",\"name\":\"$t(\'proxy\')\",\"type\":\"input\",\"title\":\"$t(\'proxy\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"Port\",\"name\":\"$t(\'port\')\",\"type\":\"input-number\",\"title\":\"$t(\'port\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"number\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"User\",\"name\":\"$t(\'user\')\",\"type\":\"input\",\"title\":\"$t(\'user\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":\"password\",\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"if enable use authentication, you need input password\",\"size\":\"small\"},\"field\":\"Password\",\"name\":\"$t(\'password\')\",\"type\":\"input\",\"title\":\"$t(\'password\')\",\"value\":null,\"validate\":null,\"emit\":null}]','2026-05-11 15:22:25','2026-05-11 15:22:25'),(10,'Http','alert','[{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input request URL\",\"size\":\"small\"},\"field\":\"url\",\"name\":\"$t(\'url\')\",\"type\":\"input\",\"title\":\"$t(\'url\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input request type POST or GET\",\"size\":\"small\"},\"field\":\"requestType\",\"name\":\"$t(\'requestType\')\",\"type\":\"input\",\"title\":\"$t(\'requestType\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input request headers as JSON format\",\"size\":\"small\"},\"field\":\"headerParams\",\"name\":\"$t(\'headerParams\')\",\"type\":\"input\",\"title\":\"$t(\'headerParams\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input request body as JSON format\",\"size\":\"small\"},\"field\":\"bodyParams\",\"name\":\"$t(\'bodyParams\')\",\"type\":\"input\",\"title\":\"$t(\'bodyParams\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input alert msg field name\",\"size\":\"small\"},\"field\":\"contentField\",\"name\":\"$t(\'contentField\')\",\"type\":\"input\",\"title\":\"$t(\'contentField\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"timeout\",\"name\":\"$t(\'timeout\')\",\"type\":\"input-number\",\"title\":\"$t(\'timeout\')\",\"value\":120,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"number\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null}]','2026-05-11 15:22:25','2026-05-11 15:22:25'),(11,'DingTalk','alert','[{\"props\":null,\"field\":\"WebHook\",\"name\":\"$t(\'webhook\')\",\"type\":\"input\",\"title\":\"$t(\'webhook\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"Keyword\",\"name\":\"$t(\'keyword\')\",\"type\":\"input\",\"title\":\"$t(\'keyword\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"Secret\",\"name\":\"$t(\'secret\')\",\"type\":\"input\",\"title\":\"$t(\'secret\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"MsgType\",\"name\":\"$t(\'msgType\')\",\"type\":\"radio\",\"title\":\"$t(\'msgType\')\",\"value\":\"text\",\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"text\",\"value\":\"text\",\"disabled\":false},{\"label\":\"markdown\",\"value\":\"markdown\",\"disabled\":false}]},{\"props\":null,\"field\":\"AtMobiles\",\"name\":\"$t(\'atMobiles\')\",\"type\":\"input\",\"title\":\"$t(\'atMobiles\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"AtUserIds\",\"name\":\"$t(\'atUserIds\')\",\"type\":\"input\",\"title\":\"$t(\'atUserIds\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"IsAtAll\",\"name\":\"$t(\'isAtAll\')\",\"type\":\"radio\",\"title\":\"$t(\'isAtAll\')\",\"value\":\"false\",\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"YES\",\"value\":\"true\",\"disabled\":false},{\"label\":\"NO\",\"value\":\"false\",\"disabled\":false}]},{\"props\":null,\"field\":\"IsEnableProxy\",\"name\":\"$t(\'isEnableProxy\')\",\"type\":\"radio\",\"title\":\"$t(\'isEnableProxy\')\",\"value\":\"false\",\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"YES\",\"value\":\"true\",\"disabled\":false},{\"label\":\"NO\",\"value\":\"false\",\"disabled\":false}]},{\"props\":null,\"field\":\"Proxy\",\"name\":\"$t(\'proxy\')\",\"type\":\"input\",\"title\":\"$t(\'proxy\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"Port\",\"name\":\"$t(\'port\')\",\"type\":\"input-number\",\"title\":\"$t(\'port\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"number\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"User\",\"name\":\"$t(\'user\')\",\"type\":\"input\",\"title\":\"$t(\'user\')\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":\"password\",\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"if enable use authentication, you need input password\",\"size\":\"small\"},\"field\":\"Password\",\"name\":\"$t(\'password\')\",\"type\":\"input\",\"title\":\"$t(\'password\')\",\"value\":null,\"validate\":null,\"emit\":null}]','2026-05-11 15:22:25','2026-05-11 15:22:25'),(12,'WebexTeams','alert','[{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input bot access token\",\"size\":\"small\"},\"field\":\"BotAccessToken\",\"name\":\"botAccessToken\",\"type\":\"input\",\"title\":\"botAccessToken\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input the room ID the alert message send to\",\"size\":\"small\"},\"field\":\"RoomId\",\"name\":\"roomId\",\"type\":\"input\",\"title\":\"roomId\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input the person ID of the alert message recipient\",\"size\":\"small\"},\"field\":\"ToPersonId\",\"name\":\"toPersonId\",\"type\":\"input\",\"title\":\"toPersonId\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"input the email address of the alert message recipient\",\"size\":\"small\"},\"field\":\"ToPersonEmail\",\"name\":\"toPersonEmail\",\"type\":\"input\",\"title\":\"toPersonEmail\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":{\"disabled\":null,\"type\":null,\"maxlength\":null,\"minlength\":null,\"clearable\":null,\"prefixIcon\":null,\"suffixIcon\":null,\"rows\":null,\"autosize\":null,\"autocomplete\":null,\"name\":null,\"readonly\":null,\"max\":null,\"min\":null,\"step\":null,\"resize\":null,\"autofocus\":null,\"form\":null,\"label\":null,\"tabindex\":null,\"validateEvent\":null,\"showPassword\":null,\"placeholder\":\"use `,`(eng commas) to separate multiple emails, to specify the person you mention in the room\",\"size\":\"small\"},\"field\":\"AtSomeoneInRoom\",\"name\":\"atSomeoneInRoom\",\"type\":\"input\",\"title\":\"atSomeoneInRoom\",\"value\":null,\"validate\":[{\"required\":false,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"Destination\",\"name\":\"destination\",\"type\":\"radio\",\"title\":\"destination\",\"value\":\"roomId\",\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null,\"options\":[{\"label\":\"roomId\",\"value\":\"roomId\",\"disabled\":false},{\"label\":\"personEmail\",\"value\":\"personEmail\",\"disabled\":false},{\"label\":\"personId\",\"value\":\"personId\",\"disabled\":false}]}]','2026-05-11 15:22:25','2026-05-11 15:22:25'),(13,'PagerDuty','alert','[{\"props\":null,\"field\":\"IntegrationKey\",\"name\":\"integrationKey\",\"type\":\"input\",\"title\":\"integrationKey\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null}]','2026-05-11 15:22:25','2026-05-11 15:22:25'),(14,'JAVA','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(15,'JUPYTER','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(16,'SPARK','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(17,'FLINK_STREAM','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(18,'PYTHON','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(19,'DATASYNC','task','[]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(20,'DATA_FACTORY','task','[]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(21,'CHUNJUN','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(22,'REMOTESHELL','task','[{\"props\":null,\"field\":\"name\",\"name\":\"$t(\'Node name\')\",\"type\":\"input\",\"title\":\"$t(\'Node name\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"runFlag\",\"name\":\"RUN_FLAG\",\"type\":\"radio\",\"title\":\"RUN_FLAG\",\"value\":null,\"validate\":null,\"emit\":null,\"options\":[{\"label\":\"NORMAL\",\"value\":\"NORMAL\",\"disabled\":false},{\"label\":\"FORBIDDEN\",\"value\":\"FORBIDDEN\",\"disabled\":false}]}]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(23,'PIGEON','task','[{\"props\":null,\"field\":\"targetJobName\",\"name\":\"targetJobName\",\"type\":\"input\",\"title\":\"targetJobName\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null}]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(24,'SHELL','task','[{\"props\":null,\"field\":\"name\",\"name\":\"$t(\'Node name\')\",\"type\":\"input\",\"title\":\"$t(\'Node name\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"runFlag\",\"name\":\"RUN_FLAG\",\"type\":\"radio\",\"title\":\"RUN_FLAG\",\"value\":null,\"validate\":null,\"emit\":null,\"options\":[{\"label\":\"NORMAL\",\"value\":\"NORMAL\",\"disabled\":false},{\"label\":\"FORBIDDEN\",\"value\":\"FORBIDDEN\",\"disabled\":false}]}]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(25,'PROCEDURE','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(26,'PYTORCH','task','[]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(27,'MR','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(28,'SQOOP','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(29,'K8S','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(30,'SAGEMAKER','task','[]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(31,'SEATUNNEL','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(32,'HTTP','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(33,'DMS','task','[]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(34,'EMR','task','[]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(35,'DATA_QUALITY','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(36,'KUBEFLOW','task','[]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(37,'SQL','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(38,'DVC','task','[{\"props\":null,\"field\":\"name\",\"name\":\"$t(\'Node name\')\",\"type\":\"input\",\"title\":\"$t(\'Node name\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"runFlag\",\"name\":\"RUN_FLAG\",\"type\":\"radio\",\"title\":\"RUN_FLAG\",\"value\":null,\"validate\":null,\"emit\":null,\"options\":[{\"label\":\"NORMAL\",\"value\":\"NORMAL\",\"disabled\":false},{\"label\":\"FORBIDDEN\",\"value\":\"FORBIDDEN\",\"disabled\":false}]}]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(39,'DATAX','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(40,'ZEPPELIN','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(41,'DINKY','task','[]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(42,'MLFLOW','task','[{\"props\":null,\"field\":\"name\",\"name\":\"$t(\'Node name\')\",\"type\":\"input\",\"title\":\"$t(\'Node name\')\",\"value\":null,\"validate\":[{\"required\":true,\"message\":null,\"type\":\"string\",\"trigger\":\"blur\",\"min\":null,\"max\":null}],\"emit\":null},{\"props\":null,\"field\":\"runFlag\",\"name\":\"RUN_FLAG\",\"type\":\"radio\",\"title\":\"RUN_FLAG\",\"value\":null,\"validate\":null,\"emit\":null,\"options\":[{\"label\":\"NORMAL\",\"value\":\"NORMAL\",\"disabled\":false},{\"label\":\"FORBIDDEN\",\"value\":\"FORBIDDEN\",\"disabled\":false}]}]','2026-05-11 15:25:42','2026-05-11 15:25:42'),(43,'OPENMLDB','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(44,'LINKIS','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(45,'HIVECLI','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42'),(46,'FLINK','task','null','2026-05-11 15:25:42','2026-05-11 15:25:42');
/*!40000 ALTER TABLE `t_ds_plugin_define` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_process_definition`
--

DROP TABLE IF EXISTS `t_ds_process_definition`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_process_definition` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'self-increasing id',
  `code` bigint NOT NULL COMMENT 'encoding',
  `name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'process definition name',
  `version` int NOT NULL DEFAULT '1' COMMENT 'process definition version',
  `description` text COLLATE utf8mb3_bin COMMENT 'description',
  `project_code` bigint NOT NULL COMMENT 'project code',
  `release_state` tinyint DEFAULT NULL COMMENT 'process definition release stateï¼š0:offline,1:online',
  `user_id` int DEFAULT NULL COMMENT 'process definition creator id',
  `global_params` text COLLATE utf8mb3_bin COMMENT 'global parameters',
  `flag` tinyint DEFAULT NULL COMMENT '0 not available, 1 available',
  `locations` text COLLATE utf8mb3_bin COMMENT 'Node location information',
  `warning_group_id` int DEFAULT NULL COMMENT 'alert group id',
  `timeout` int DEFAULT '0' COMMENT 'time out, unit: minute',
  `execution_type` tinyint DEFAULT '0' COMMENT 'execution_type 0:parallel,1:serial wait,2:serial discard,3:serial priority',
  `create_time` datetime NOT NULL COMMENT 'create time',
  `update_time` datetime NOT NULL COMMENT 'update time',
  PRIMARY KEY (`id`,`code`),
  UNIQUE KEY `process_unique` (`name`,`project_code`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_process_definition`
--

LOCK TABLES `t_ds_process_definition` WRITE;
/*!40000 ALTER TABLE `t_ds_process_definition` DISABLE KEYS */;
INSERT INTO `t_ds_process_definition` VALUES (1,173134949053760,'demo01',1,'',173134550388032,1,1,'[]',1,'[{\"taskCode\":173134919774528,\"x\":1327,\"y\":686}]',NULL,0,0,'2026-05-11 21:51:39','2026-05-11 21:51:39'),(2,173135002280256,'1',1,'',173134550388032,1,1,'[]',1,'[{\"taskCode\":173134988690752,\"x\":758,\"y\":338}]',NULL,0,0,'2026-05-11 21:52:31','2026-05-11 21:52:31'),(3,173179744097664,'12',1,'',173134550388032,0,1,'[]',1,'[{\"taskCode\":173179728524672,\"x\":211,\"y\":148}]',NULL,0,0,'2026-05-12 10:00:44','2026-05-12 10:00:44'),(5,173184205699456,'daily_user_etl',1,'每日用户全量同步 (DataX → Python → Shell)',173134550388032,1,1,'[]',1,'[{\"taskCode\": 173184205689216, \"x\": 200, \"y\": 200}, {\"taskCode\": 173184205689217, \"x\": 420, \"y\": 200}, {\"taskCode\": 173184205689218, \"x\": 640, \"y\": 200}]',NULL,0,0,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(6,173184206033280,'nightly_cleanup',1,'每晚清理临时文件',173134550388032,0,1,'[]',1,'[{\"taskCode\": 173184206025088, \"x\": 200, \"y\": 200}, {\"taskCode\": 173184206025089, \"x\": 420, \"y\": 200}]',NULL,0,0,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(7,173184206372224,'user_data_export',1,'用户数据导出 (SQL 抽取 + Python 加工)',173134550388032,1,1,'[]',1,'[{\"taskCode\": 173184206360960, \"x\": 200, \"y\": 200}, {\"taskCode\": 173184206360961, \"x\": 420, \"y\": 200}]',NULL,0,0,'2026-05-12 11:13:22','2026-05-12 11:13:22'),(8,173278852484480,'测试01',1,'',173134550388032,0,1,'[]',1,'[{\"taskCode\": 173278852477312, \"x\": 132, \"y\": 60}, {\"taskCode\": 173278852477313, \"x\": 453, \"y\": 238}, {\"taskCode\": 173278852477314, \"x\": 139, \"y\": 237}]',NULL,0,0,'2026-05-13 12:53:49','2026-05-13 12:53:49'),(9,173285883084160,'002',1,'',173134550388032,1,1,'[]',1,'[{\"taskCode\": 173285883079040, \"x\": 191, \"y\": 185}]',NULL,0,0,'2026-05-13 14:48:15','2026-05-13 14:48:15');
/*!40000 ALTER TABLE `t_ds_process_definition` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_process_definition_log`
--

DROP TABLE IF EXISTS `t_ds_process_definition_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_process_definition_log` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'self-increasing id',
  `code` bigint NOT NULL COMMENT 'encoding',
  `name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'process definition name',
  `version` int NOT NULL DEFAULT '1' COMMENT 'process definition version',
  `description` text COLLATE utf8mb3_bin COMMENT 'description',
  `project_code` bigint NOT NULL COMMENT 'project code',
  `release_state` tinyint DEFAULT NULL COMMENT 'process definition release stateï¼š0:offline,1:online',
  `user_id` int DEFAULT NULL COMMENT 'process definition creator id',
  `global_params` text COLLATE utf8mb3_bin COMMENT 'global parameters',
  `flag` tinyint DEFAULT NULL COMMENT '0 not available, 1 available',
  `locations` text COLLATE utf8mb3_bin COMMENT 'Node location information',
  `warning_group_id` int DEFAULT NULL COMMENT 'alert group id',
  `timeout` int DEFAULT '0' COMMENT 'time out,unit: minute',
  `execution_type` tinyint DEFAULT '0' COMMENT 'execution_type 0:parallel,1:serial wait,2:serial discard,3:serial priority',
  `operator` int DEFAULT NULL COMMENT 'operator user id',
  `operate_time` datetime DEFAULT NULL COMMENT 'operate time',
  `create_time` datetime NOT NULL COMMENT 'create time',
  `update_time` datetime NOT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_idx_code_version` (`code`,`version`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_process_definition_log`
--

LOCK TABLES `t_ds_process_definition_log` WRITE;
/*!40000 ALTER TABLE `t_ds_process_definition_log` DISABLE KEYS */;
INSERT INTO `t_ds_process_definition_log` VALUES (1,173134949053760,'demo01',1,'',173134550388032,0,1,'[]',1,'[{\"taskCode\":173134919774528,\"x\":1327,\"y\":686}]',NULL,0,0,1,'2026-05-11 21:51:39','2026-05-11 21:51:39','2026-05-11 21:51:39'),(2,173135002280256,'1',1,'',173134550388032,0,1,'[]',1,'[{\"taskCode\":173134988690752,\"x\":758,\"y\":338}]',NULL,0,0,1,'2026-05-11 21:52:31','2026-05-11 21:52:31','2026-05-11 21:52:31'),(3,173179744097664,'12',1,'',173134550388032,0,1,'[]',1,'[{\"taskCode\":173179728524672,\"x\":211,\"y\":148}]',NULL,0,0,1,'2026-05-12 10:00:44','2026-05-12 10:00:44','2026-05-12 10:00:44'),(5,173184205699456,'daily_user_etl',1,'每日用户全量同步 (DataX → Python → Shell)',173134550388032,0,1,'[]',1,'[{\"taskCode\": 173184205689216, \"x\": 200, \"y\": 200}, {\"taskCode\": 173184205689217, \"x\": 420, \"y\": 200}, {\"taskCode\": 173184205689218, \"x\": 640, \"y\": 200}]',NULL,0,0,1,'2026-05-12 11:13:21','2026-05-12 11:13:21','2026-05-12 11:13:21'),(6,173184206033280,'nightly_cleanup',1,'每晚清理临时文件',173134550388032,0,1,'[]',1,'[{\"taskCode\": 173184206025088, \"x\": 200, \"y\": 200}, {\"taskCode\": 173184206025089, \"x\": 420, \"y\": 200}]',NULL,0,0,1,'2026-05-12 11:13:21','2026-05-12 11:13:21','2026-05-12 11:13:21'),(7,173184206372224,'user_data_export',1,'用户数据导出 (SQL 抽取 + Python 加工)',173134550388032,0,1,'[]',1,'[{\"taskCode\": 173184206360960, \"x\": 200, \"y\": 200}, {\"taskCode\": 173184206360961, \"x\": 420, \"y\": 200}]',NULL,0,0,1,'2026-05-12 11:13:22','2026-05-12 11:13:22','2026-05-12 11:13:22'),(8,173278852484480,'测试01',1,'',173134550388032,0,1,'[]',1,'[{\"taskCode\": 173278852477312, \"x\": 132, \"y\": 60}, {\"taskCode\": 173278852477313, \"x\": 453, \"y\": 238}, {\"taskCode\": 173278852477314, \"x\": 139, \"y\": 237}]',NULL,0,0,1,'2026-05-13 12:53:49','2026-05-13 12:53:49','2026-05-13 12:53:49'),(9,173285883084160,'002',1,'',173134550388032,0,1,'[]',1,'[{\"taskCode\": 173285883079040, \"x\": 191, \"y\": 185}]',NULL,0,0,1,'2026-05-13 14:48:15','2026-05-13 14:48:15','2026-05-13 14:48:15');
/*!40000 ALTER TABLE `t_ds_process_definition_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_process_instance`
--

DROP TABLE IF EXISTS `t_ds_process_instance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_process_instance` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'process instance name',
  `process_definition_code` bigint NOT NULL COMMENT 'process definition code',
  `process_definition_version` int NOT NULL DEFAULT '1' COMMENT 'process definition version',
  `project_code` bigint DEFAULT NULL COMMENT 'project code',
  `state` tinyint DEFAULT NULL COMMENT 'process instance Status: 0 commit succeeded, 1 running, 2 prepare to pause, 3 pause, 4 prepare to stop, 5 stop, 6 fail, 7 succeed, 8 need fault tolerance, 9 kill, 10 wait for thread, 11 wait for dependency to complete',
  `state_history` text COLLATE utf8mb3_bin COMMENT 'state history desc',
  `recovery` tinyint DEFAULT NULL COMMENT 'process instance failover flagï¼š0:normal,1:failover instance',
  `start_time` datetime DEFAULT NULL COMMENT 'process instance start time',
  `end_time` datetime DEFAULT NULL COMMENT 'process instance end time',
  `run_times` int DEFAULT NULL COMMENT 'process instance run times',
  `host` varchar(135) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'process instance host',
  `command_type` tinyint DEFAULT NULL COMMENT 'command type',
  `command_param` text COLLATE utf8mb3_bin COMMENT 'json command parameters',
  `task_depend_type` tinyint DEFAULT NULL COMMENT 'task depend type. 0: only current node,1:before the node,2:later nodes',
  `max_try_times` tinyint DEFAULT '0' COMMENT 'max try times',
  `failure_strategy` tinyint DEFAULT '0' COMMENT 'failure strategy. 0:end the process when node failed,1:continue running the other nodes when node failed',
  `warning_type` tinyint DEFAULT '0' COMMENT 'warning type. 0:no warning,1:warning if process success,2:warning if process failed,3:warning if success',
  `warning_group_id` int DEFAULT NULL COMMENT 'warning group id',
  `schedule_time` datetime DEFAULT NULL COMMENT 'schedule time',
  `command_start_time` datetime DEFAULT NULL COMMENT 'command start time',
  `global_params` text COLLATE utf8mb3_bin COMMENT 'global parameters',
  `flag` tinyint DEFAULT '1' COMMENT 'flag',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_sub_process` int DEFAULT '0' COMMENT 'flag, whether the process is sub process',
  `executor_id` int NOT NULL COMMENT 'executor id',
  `executor_name` varchar(64) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'execute user name',
  `history_cmd` text COLLATE utf8mb3_bin COMMENT 'history commands of process instance operation',
  `process_instance_priority` int DEFAULT '2' COMMENT 'process instance priority. 0 Highest,1 High,2 Medium,3 Low,4 Lowest',
  `worker_group` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'worker group id',
  `environment_code` bigint DEFAULT '-1' COMMENT 'environment code',
  `timeout` int DEFAULT '0' COMMENT 'time out',
  `tenant_code` varchar(64) COLLATE utf8mb3_bin DEFAULT 'default' COMMENT 'tenant code',
  `var_pool` longtext COLLATE utf8mb3_bin COMMENT 'var_pool',
  `dry_run` tinyint DEFAULT '0' COMMENT 'dry run flagï¼š0 normal, 1 dry run',
  `next_process_instance_id` int DEFAULT '0' COMMENT 'serial queue next processInstanceId',
  `restart_time` datetime DEFAULT NULL COMMENT 'process instance restart time',
  `test_flag` tinyint DEFAULT NULL COMMENT 'test flagï¼š0 normal, 1 test run',
  PRIMARY KEY (`id`),
  KEY `process_instance_index` (`process_definition_code`,`id`) USING BTREE,
  KEY `start_time_index` (`start_time`,`end_time`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_process_instance`
--

LOCK TABLES `t_ds_process_instance` WRITE;
/*!40000 ALTER TABLE `t_ds_process_instance` DISABLE KEYS */;
INSERT INTO `t_ds_process_instance` VALUES (2,'daily_user_etl-1-20260512111321946',173184205699456,1,173134550388032,6,'[{\"time\":\"2026-05-12 11:13:21\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"init running\"},{\"time\":\"2026-05-12 11:13:21\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"start a new process\"},{\"time\":\"2026-05-12 11:13:23\",\"state\":\"FAILURE\",\"desc\":\"update by workflow executor\"}]',0,'2026-05-12 11:13:22','2026-05-12 11:13:24',1,'172.18.0.8:5678',0,'{\"schedule_timezone\":\"Asia/Shanghai\"}',2,0,1,0,0,NULL,'2026-05-12 11:13:22',NULL,1,'2026-05-12 03:13:23',0,1,'admin','START_PROCESS',2,'default',-1,0,'default',NULL,0,0,'2026-05-12 11:13:22',0),(3,'daily_user_etl-1-20260512111322957',173184205699456,1,173134550388032,6,'[{\"time\":\"2026-05-12 11:13:22\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"init running\"},{\"time\":\"2026-05-12 11:13:22\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"start a new process\"},{\"time\":\"2026-05-12 11:13:24\",\"state\":\"FAILURE\",\"desc\":\"update by workflow executor\"}]',0,'2026-05-12 11:13:23','2026-05-12 11:13:25',1,'172.18.0.8:5678',0,'{\"schedule_timezone\":\"Asia/Shanghai\"}',2,0,1,0,0,NULL,'2026-05-12 11:13:23',NULL,1,'2026-05-12 03:13:24',0,1,'admin','START_PROCESS',2,'default',-1,0,'default',NULL,0,0,'2026-05-12 11:13:23',0),(4,'nightly_cleanup-1-20260512111323971',173184206033280,1,173134550388032,7,'[{\"time\":\"2026-05-12 11:13:23\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"init running\"},{\"time\":\"2026-05-12 11:13:23\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"start a new process\"},{\"time\":\"2026-05-12 11:13:27\",\"state\":\"SUCCESS\",\"desc\":\"update by workflow executor\"}]',0,'2026-05-12 11:13:24','2026-05-12 11:13:28',1,'172.18.0.8:5678',0,'{\"schedule_timezone\":\"Asia/Shanghai\"}',2,0,1,0,0,NULL,'2026-05-12 11:13:24',NULL,1,'2026-05-12 03:13:27',0,1,'admin','START_PROCESS',2,'default',-1,0,'default','[]',0,0,'2026-05-12 11:13:24',0),(5,'nightly_cleanup-1-20260512111324988',173184206033280,1,173134550388032,7,'[{\"time\":\"2026-05-12 11:13:24\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"init running\"},{\"time\":\"2026-05-12 11:13:24\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"start a new process\"},{\"time\":\"2026-05-12 11:13:28\",\"state\":\"SUCCESS\",\"desc\":\"update by workflow executor\"},{\"time\":\"2026-05-13 14:08:09\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"repeat running a process\"},{\"time\":\"2026-05-13 14:08:13\",\"state\":\"SUCCESS\",\"desc\":\"update by workflow executor\"}]',0,'2026-05-13 14:08:10','2026-05-13 14:08:13',2,'172.18.0.8:5678',7,'{\"schedule_timezone\":\"Asia/Shanghai\"}',2,0,1,0,0,NULL,'2026-05-12 11:13:25',NULL,1,'2026-05-13 06:08:13',0,1,'admin','START_PROCESS,REPEAT_RUNNING',2,'default',-1,0,'default','[]',0,0,'2026-05-13 14:08:10',0),(6,'user_data_export-1-20260512111327002',173184206372224,1,173134550388032,6,'[{\"time\":\"2026-05-12 11:13:27\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"init running\"},{\"time\":\"2026-05-12 11:13:27\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"start a new process\"},{\"time\":\"2026-05-12 11:13:28\",\"state\":\"FAILURE\",\"desc\":\"update by workflow executor\"},{\"time\":\"2026-05-13 14:07:58\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"repeat running a process\"},{\"time\":\"2026-05-13 14:08:00\",\"state\":\"FAILURE\",\"desc\":\"update by workflow executor\"}]',0,'2026-05-13 14:07:59','2026-05-13 14:08:00',2,'172.18.0.8:5678',7,'{}',2,0,1,0,0,NULL,'2026-05-12 11:13:26',NULL,1,'2026-05-13 06:08:00',0,1,'admin','START_PROCESS,REPEAT_RUNNING',2,'default',-1,0,'default',NULL,0,0,'2026-05-13 14:07:59',0),(7,'002-1-20260513151247019',173285883084160,1,173134550388032,6,'[{\"time\":\"2026-05-13 15:12:47\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"init running\"},{\"time\":\"2026-05-13 15:12:47\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"start a new process\"},{\"time\":\"2026-05-13 15:12:48\",\"state\":\"FAILURE\",\"desc\":\"update by workflow executor\"}]',0,'2026-05-13 15:12:47','2026-05-13 15:12:49',1,'172.18.0.8:5678',0,'{}',2,0,1,0,0,NULL,'2026-05-13 15:12:47',NULL,1,'2026-05-13 07:12:48',0,1,'admin','START_PROCESS',2,'default',-1,0,'default',NULL,0,0,'2026-05-13 15:12:47',0),(8,'002-1-20260513151300036',173285883084160,1,173134550388032,6,'[{\"time\":\"2026-05-13 15:13:00\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"init running\"},{\"time\":\"2026-05-13 15:13:00\",\"state\":\"RUNNING_EXECUTION\",\"desc\":\"start a new process\"},{\"time\":\"2026-05-13 15:13:01\",\"state\":\"FAILURE\",\"desc\":\"update by workflow executor\"}]',0,'2026-05-13 15:13:00','2026-05-13 15:13:02',1,'172.18.0.8:5678',0,'{}',2,0,1,0,0,NULL,'2026-05-13 15:12:59',NULL,1,'2026-05-13 07:13:01',0,1,'admin','START_PROCESS',2,'default',-1,0,'default',NULL,0,0,'2026-05-13 15:13:00',0);
/*!40000 ALTER TABLE `t_ds_process_instance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_process_task_relation`
--

DROP TABLE IF EXISTS `t_ds_process_task_relation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_process_task_relation` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'self-increasing id',
  `name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'relation name',
  `project_code` bigint NOT NULL COMMENT 'project code',
  `process_definition_code` bigint NOT NULL COMMENT 'process code',
  `process_definition_version` int NOT NULL COMMENT 'process version',
  `pre_task_code` bigint NOT NULL COMMENT 'pre task code',
  `pre_task_version` int NOT NULL COMMENT 'pre task version',
  `post_task_code` bigint NOT NULL COMMENT 'post task code',
  `post_task_version` int NOT NULL COMMENT 'post task version',
  `condition_type` tinyint DEFAULT NULL COMMENT 'condition type : 0 none, 1 judge 2 delay',
  `condition_params` text COLLATE utf8mb3_bin COMMENT 'condition params(json)',
  `create_time` datetime NOT NULL COMMENT 'create time',
  `update_time` datetime NOT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  KEY `idx_code` (`project_code`,`process_definition_code`),
  KEY `idx_pre_task_code_version` (`pre_task_code`,`pre_task_version`),
  KEY `idx_post_task_code_version` (`post_task_code`,`post_task_version`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_process_task_relation`
--

LOCK TABLES `t_ds_process_task_relation` WRITE;
/*!40000 ALTER TABLE `t_ds_process_task_relation` DISABLE KEYS */;
INSERT INTO `t_ds_process_task_relation` VALUES (1,'',173134550388032,173134949053760,1,0,0,173134919774528,1,0,'{}','2026-05-11 21:51:39','2026-05-11 21:51:39'),(2,'',173134550388032,173135002280256,1,0,0,173134988690752,1,0,'{}','2026-05-11 21:52:31','2026-05-11 21:52:31'),(3,'',173134550388032,173179744097664,1,0,0,173179728524672,1,0,'{}','2026-05-12 10:00:44','2026-05-12 10:00:44'),(6,'',173134550388032,173184205699456,1,0,0,173184205689216,1,0,'{}','2026-05-12 11:13:21','2026-05-12 11:13:21'),(7,'',173134550388032,173184205699456,1,173184205689216,1,173184205689217,1,0,'{}','2026-05-12 11:13:21','2026-05-12 11:13:21'),(8,'',173134550388032,173184205699456,1,173184205689217,1,173184205689218,1,0,'{}','2026-05-12 11:13:21','2026-05-12 11:13:21'),(9,'',173134550388032,173184206033280,1,0,0,173184206025088,1,0,'{}','2026-05-12 11:13:21','2026-05-12 11:13:21'),(10,'',173134550388032,173184206033280,1,173184206025088,1,173184206025089,1,0,'{}','2026-05-12 11:13:21','2026-05-12 11:13:21'),(11,'',173134550388032,173184206372224,1,0,0,173184206360960,1,0,'{}','2026-05-12 11:13:22','2026-05-12 11:13:22'),(12,'',173134550388032,173184206372224,1,173184206360960,1,173184206360961,1,0,'{}','2026-05-12 11:13:22','2026-05-12 11:13:22'),(13,'',173134550388032,173278852484480,1,0,0,173278852477312,1,0,'{}','2026-05-13 12:53:49','2026-05-13 12:53:49'),(14,'',173134550388032,173278852484480,1,173278852477312,1,173278852477313,1,0,'{}','2026-05-13 12:53:49','2026-05-13 12:53:49'),(15,'',173134550388032,173278852484480,1,173278852477312,1,173278852477314,1,0,'{}','2026-05-13 12:53:49','2026-05-13 12:53:49'),(16,'',173134550388032,173285883084160,1,0,0,173285883079040,1,0,'{}','2026-05-13 14:48:15','2026-05-13 14:48:15');
/*!40000 ALTER TABLE `t_ds_process_task_relation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_process_task_relation_log`
--

DROP TABLE IF EXISTS `t_ds_process_task_relation_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_process_task_relation_log` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'self-increasing id',
  `name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'relation name',
  `project_code` bigint NOT NULL COMMENT 'project code',
  `process_definition_code` bigint NOT NULL COMMENT 'process code',
  `process_definition_version` int NOT NULL COMMENT 'process version',
  `pre_task_code` bigint NOT NULL COMMENT 'pre task code',
  `pre_task_version` int NOT NULL COMMENT 'pre task version',
  `post_task_code` bigint NOT NULL COMMENT 'post task code',
  `post_task_version` int NOT NULL COMMENT 'post task version',
  `condition_type` tinyint DEFAULT NULL COMMENT 'condition type : 0 none, 1 judge 2 delay',
  `condition_params` text COLLATE utf8mb3_bin COMMENT 'condition params(json)',
  `operator` int DEFAULT NULL COMMENT 'operator user id',
  `operate_time` datetime DEFAULT NULL COMMENT 'operate time',
  `create_time` datetime NOT NULL COMMENT 'create time',
  `update_time` datetime NOT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  KEY `idx_process_code_version` (`process_definition_code`,`process_definition_version`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_process_task_relation_log`
--

LOCK TABLES `t_ds_process_task_relation_log` WRITE;
/*!40000 ALTER TABLE `t_ds_process_task_relation_log` DISABLE KEYS */;
INSERT INTO `t_ds_process_task_relation_log` VALUES (1,'',173134550388032,173134949053760,1,0,0,173134919774528,1,0,'{}',1,'2026-05-11 21:51:39','2026-05-11 21:51:39','2026-05-11 21:51:39'),(2,'',173134550388032,173135002280256,1,0,0,173134988690752,1,0,'{}',1,'2026-05-11 21:52:31','2026-05-11 21:52:31','2026-05-11 21:52:31'),(3,'',173134550388032,173179744097664,1,0,0,173179728524672,1,0,'{}',1,'2026-05-12 10:00:44','2026-05-12 10:00:44','2026-05-12 10:00:44'),(6,'',173134550388032,173184205699456,1,0,0,173184205689216,1,0,'{}',1,'2026-05-12 11:13:21','2026-05-12 11:13:21','2026-05-12 11:13:21'),(7,'',173134550388032,173184205699456,1,173184205689216,1,173184205689217,1,0,'{}',1,'2026-05-12 11:13:21','2026-05-12 11:13:21','2026-05-12 11:13:21'),(8,'',173134550388032,173184205699456,1,173184205689217,1,173184205689218,1,0,'{}',1,'2026-05-12 11:13:21','2026-05-12 11:13:21','2026-05-12 11:13:21'),(9,'',173134550388032,173184206033280,1,0,0,173184206025088,1,0,'{}',1,'2026-05-12 11:13:21','2026-05-12 11:13:21','2026-05-12 11:13:21'),(10,'',173134550388032,173184206033280,1,173184206025088,1,173184206025089,1,0,'{}',1,'2026-05-12 11:13:21','2026-05-12 11:13:21','2026-05-12 11:13:21'),(11,'',173134550388032,173184206372224,1,0,0,173184206360960,1,0,'{}',1,'2026-05-12 11:13:22','2026-05-12 11:13:22','2026-05-12 11:13:22'),(12,'',173134550388032,173184206372224,1,173184206360960,1,173184206360961,1,0,'{}',1,'2026-05-12 11:13:22','2026-05-12 11:13:22','2026-05-12 11:13:22'),(13,'',173134550388032,173278852484480,1,0,0,173278852477312,1,0,'{}',1,'2026-05-13 12:53:49','2026-05-13 12:53:49','2026-05-13 12:53:49'),(14,'',173134550388032,173278852484480,1,173278852477312,1,173278852477313,1,0,'{}',1,'2026-05-13 12:53:49','2026-05-13 12:53:49','2026-05-13 12:53:49'),(15,'',173134550388032,173278852484480,1,173278852477312,1,173278852477314,1,0,'{}',1,'2026-05-13 12:53:49','2026-05-13 12:53:49','2026-05-13 12:53:49'),(16,'',173134550388032,173285883084160,1,0,0,173285883079040,1,0,'{}',1,'2026-05-13 14:48:15','2026-05-13 14:48:15','2026-05-13 14:48:15');
/*!40000 ALTER TABLE `t_ds_process_task_relation_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_project`
--

DROP TABLE IF EXISTS `t_ds_project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_project` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'project name',
  `code` bigint NOT NULL COMMENT 'encoding',
  `description` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `user_id` int DEFAULT NULL COMMENT 'creator id',
  `flag` tinyint DEFAULT '1' COMMENT '0 not available, 1 available',
  `create_time` datetime NOT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_code` (`code`),
  UNIQUE KEY `unique_name` (`name`),
  KEY `user_id_index` (`user_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_project`
--

LOCK TABLES `t_ds_project` WRITE;
/*!40000 ALTER TABLE `t_ds_project` DISABLE KEYS */;
INSERT INTO `t_ds_project` VALUES (1,'默认项目',173117159418176,'自动重命名验证',1,1,'2026-05-11 17:02:06','2026-05-11 21:48:13'),(2,'监管报送',173134550293824,'金融监管报送类工作流',1,1,'2026-05-11 21:45:09','2026-05-11 21:45:09'),(3,'估值数据导入',173134550388032,'日终估值数据 ETL 任务',1,1,'2026-05-11 21:45:09','2026-05-11 21:45:09');
/*!40000 ALTER TABLE `t_ds_project` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_project_parameter`
--

DROP TABLE IF EXISTS `t_ds_project_parameter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_project_parameter` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `param_name` varchar(255) COLLATE utf8mb3_bin NOT NULL COMMENT 'project parameter name',
  `param_value` text COLLATE utf8mb3_bin NOT NULL COMMENT 'project parameter value',
  `code` bigint NOT NULL COMMENT 'encoding',
  `project_code` bigint NOT NULL COMMENT 'project code',
  `user_id` int DEFAULT NULL COMMENT 'creator id',
  `operator` int DEFAULT NULL COMMENT 'operator user id',
  `create_time` datetime NOT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_project_parameter_name` (`project_code`,`param_name`),
  UNIQUE KEY `unique_project_parameter_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_project_parameter`
--

LOCK TABLES `t_ds_project_parameter` WRITE;
/*!40000 ALTER TABLE `t_ds_project_parameter` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_project_parameter` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_project_preference`
--

DROP TABLE IF EXISTS `t_ds_project_preference`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_project_preference` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `code` bigint NOT NULL COMMENT 'encoding',
  `project_code` bigint NOT NULL COMMENT 'project code',
  `preferences` varchar(512) COLLATE utf8mb3_bin NOT NULL COMMENT 'project preferences',
  `user_id` int DEFAULT NULL COMMENT 'creator id',
  `state` int DEFAULT '1' COMMENT '1 means enabled, 0 means disabled',
  `create_time` datetime NOT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_project_preference_project_code` (`project_code`),
  UNIQUE KEY `unique_project_preference_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_project_preference`
--

LOCK TABLES `t_ds_project_preference` WRITE;
/*!40000 ALTER TABLE `t_ds_project_preference` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_project_preference` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_queue`
--

DROP TABLE IF EXISTS `t_ds_queue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_queue` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `queue_name` varchar(64) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'queue name',
  `queue` varchar(64) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'yarn queue name',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_queue_name` (`queue_name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_queue`
--

LOCK TABLES `t_ds_queue` WRITE;
/*!40000 ALTER TABLE `t_ds_queue` DISABLE KEYS */;
INSERT INTO `t_ds_queue` VALUES (1,'default','default',NULL,NULL);
/*!40000 ALTER TABLE `t_ds_queue` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_relation_datasource_user`
--

DROP TABLE IF EXISTS `t_ds_relation_datasource_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_relation_datasource_user` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `user_id` int NOT NULL COMMENT 'user id',
  `datasource_id` int DEFAULT NULL COMMENT 'data source id',
  `perm` int DEFAULT '1' COMMENT 'limits of authority',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_relation_datasource_user`
--

LOCK TABLES `t_ds_relation_datasource_user` WRITE;
/*!40000 ALTER TABLE `t_ds_relation_datasource_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_relation_datasource_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_relation_namespace_user`
--

DROP TABLE IF EXISTS `t_ds_relation_namespace_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_relation_namespace_user` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `user_id` int NOT NULL COMMENT 'user id',
  `namespace_id` int DEFAULT NULL COMMENT 'namespace id',
  `perm` int DEFAULT '1' COMMENT 'limits of authority',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `namespace_user_unique` (`user_id`,`namespace_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_relation_namespace_user`
--

LOCK TABLES `t_ds_relation_namespace_user` WRITE;
/*!40000 ALTER TABLE `t_ds_relation_namespace_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_relation_namespace_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_relation_process_instance`
--

DROP TABLE IF EXISTS `t_ds_relation_process_instance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_relation_process_instance` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `parent_process_instance_id` int DEFAULT NULL COMMENT 'parent process instance id',
  `parent_task_instance_id` int DEFAULT NULL COMMENT 'parent process instance id',
  `process_instance_id` int DEFAULT NULL COMMENT 'child process instance id',
  PRIMARY KEY (`id`),
  KEY `idx_parent_process_task` (`parent_process_instance_id`,`parent_task_instance_id`),
  KEY `idx_process_instance_id` (`process_instance_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_relation_process_instance`
--

LOCK TABLES `t_ds_relation_process_instance` WRITE;
/*!40000 ALTER TABLE `t_ds_relation_process_instance` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_relation_process_instance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_relation_project_user`
--

DROP TABLE IF EXISTS `t_ds_relation_project_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_relation_project_user` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `user_id` int NOT NULL COMMENT 'user id',
  `project_id` int DEFAULT NULL COMMENT 'project id',
  `perm` int DEFAULT '1' COMMENT 'limits of authority',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_uid_pid` (`user_id`,`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_relation_project_user`
--

LOCK TABLES `t_ds_relation_project_user` WRITE;
/*!40000 ALTER TABLE `t_ds_relation_project_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_relation_project_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_relation_project_worker_group`
--

DROP TABLE IF EXISTS `t_ds_relation_project_worker_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_relation_project_worker_group` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `project_code` bigint NOT NULL COMMENT 'project code',
  `worker_group` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'worker group',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_project_worker_group` (`project_code`,`worker_group`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_relation_project_worker_group`
--

LOCK TABLES `t_ds_relation_project_worker_group` WRITE;
/*!40000 ALTER TABLE `t_ds_relation_project_worker_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_relation_project_worker_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_relation_resources_user`
--

DROP TABLE IF EXISTS `t_ds_relation_resources_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_relation_resources_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT 'user id',
  `resources_id` int DEFAULT NULL COMMENT 'resource id',
  `perm` int DEFAULT '1' COMMENT 'limits of authority',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_relation_resources_user`
--

LOCK TABLES `t_ds_relation_resources_user` WRITE;
/*!40000 ALTER TABLE `t_ds_relation_resources_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_relation_resources_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_relation_rule_execute_sql`
--

DROP TABLE IF EXISTS `t_ds_relation_rule_execute_sql`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_relation_rule_execute_sql` (
  `id` int NOT NULL AUTO_INCREMENT,
  `rule_id` int DEFAULT NULL,
  `execute_sql_id` int DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_relation_rule_execute_sql`
--

LOCK TABLES `t_ds_relation_rule_execute_sql` WRITE;
/*!40000 ALTER TABLE `t_ds_relation_rule_execute_sql` DISABLE KEYS */;
INSERT INTO `t_ds_relation_rule_execute_sql` VALUES (1,1,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(2,3,3,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(3,5,4,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(4,3,8,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(5,6,6,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(6,6,7,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(7,7,9,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(8,7,10,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(9,8,11,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(10,8,12,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(11,9,13,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(12,9,14,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(13,10,15,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(14,1,16,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(15,5,17,'2026-05-11 07:21:45','2026-05-11 07:21:45');
/*!40000 ALTER TABLE `t_ds_relation_rule_execute_sql` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_relation_rule_input_entry`
--

DROP TABLE IF EXISTS `t_ds_relation_rule_input_entry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_relation_rule_input_entry` (
  `id` int NOT NULL AUTO_INCREMENT,
  `rule_id` int DEFAULT NULL,
  `rule_input_entry_id` int DEFAULT NULL,
  `values_map` text COLLATE utf8mb3_bin,
  `index` int DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=163 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_relation_rule_input_entry`
--

LOCK TABLES `t_ds_relation_rule_input_entry` WRITE;
/*!40000 ALTER TABLE `t_ds_relation_rule_input_entry` DISABLE KEYS */;
INSERT INTO `t_ds_relation_rule_input_entry` VALUES (1,1,1,NULL,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(2,1,2,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(3,1,3,NULL,3,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(4,1,4,NULL,4,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(5,1,5,NULL,5,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(6,1,6,'{\"statistics_name\":\"null_count.nulls\"}',6,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(7,1,7,NULL,7,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(8,1,8,NULL,8,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(9,1,9,NULL,9,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(10,1,10,NULL,10,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(11,1,17,'',11,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(12,1,19,NULL,12,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(13,2,1,NULL,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(14,2,2,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(15,2,3,NULL,3,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(16,2,6,'{\"is_show\":\"true\",\"can_edit\":\"true\"}',4,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(17,2,16,NULL,5,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(18,2,4,NULL,6,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(19,2,7,NULL,7,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(20,2,8,NULL,8,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(21,2,9,NULL,9,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(22,2,10,NULL,10,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(24,2,19,NULL,12,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(25,3,1,NULL,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(26,3,2,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(27,3,3,NULL,3,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(28,3,4,NULL,4,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(29,3,11,NULL,5,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(30,3,12,NULL,6,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(31,3,13,NULL,7,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(32,3,14,NULL,8,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(33,3,15,NULL,9,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(34,3,7,NULL,10,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(35,3,8,NULL,11,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(36,3,9,NULL,12,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(37,3,10,NULL,13,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(38,3,17,'{\"comparison_name\":\"total_count.total\"}',14,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(39,3,19,NULL,15,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(40,4,1,NULL,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(41,4,2,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(42,4,3,NULL,3,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(43,4,6,'{\"is_show\":\"true\",\"can_edit\":\"true\"}',4,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(44,4,16,NULL,5,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(45,4,11,NULL,6,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(46,4,12,NULL,7,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(47,4,13,NULL,8,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(48,4,17,'{\"is_show\":\"true\",\"can_edit\":\"true\"}',9,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(49,4,18,NULL,10,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(50,4,7,NULL,11,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(51,4,8,NULL,12,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(52,4,9,NULL,13,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(53,4,10,NULL,14,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(62,3,6,'{\"statistics_name\":\"miss_count.miss\"}',18,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(63,5,1,NULL,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(64,5,2,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(65,5,3,NULL,3,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(66,5,4,NULL,4,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(67,5,5,NULL,5,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(68,5,6,'{\"statistics_name\":\"invalid_length_count.valids\"}',6,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(69,5,24,NULL,7,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(70,5,23,NULL,8,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(71,5,7,NULL,9,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(72,5,8,NULL,10,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(73,5,9,NULL,11,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(74,5,10,NULL,12,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(75,5,17,'',13,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(76,5,19,NULL,14,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(79,6,1,NULL,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(80,6,2,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(81,6,3,NULL,3,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(82,6,4,NULL,4,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(83,6,5,NULL,5,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(84,6,6,'{\"statistics_name\":\"duplicate_count.duplicates\"}',6,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(85,6,7,NULL,7,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(86,6,8,NULL,8,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(87,6,9,NULL,9,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(88,6,10,NULL,10,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(89,6,17,'',11,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(90,6,19,NULL,12,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(93,7,1,NULL,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(94,7,2,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(95,7,3,NULL,3,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(96,7,4,NULL,4,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(97,7,5,NULL,5,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(98,7,6,'{\"statistics_name\":\"regexp_count.regexps\"}',6,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(99,7,25,NULL,5,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(100,7,7,NULL,7,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(101,7,8,NULL,8,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(102,7,9,NULL,9,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(103,7,10,NULL,10,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(104,7,17,NULL,11,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(105,7,19,NULL,12,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(108,8,1,NULL,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(109,8,2,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(110,8,3,NULL,3,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(111,8,4,NULL,4,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(112,8,5,NULL,5,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(113,8,6,'{\"statistics_name\":\"timeliness_count.timeliness\"}',6,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(114,8,26,NULL,8,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(115,8,27,NULL,9,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(116,8,7,NULL,10,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(117,8,8,NULL,11,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(118,8,9,NULL,12,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(119,8,10,NULL,13,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(120,8,17,NULL,14,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(121,8,19,NULL,15,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(124,9,1,NULL,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(125,9,2,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(126,9,3,NULL,3,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(127,9,4,NULL,4,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(128,9,5,NULL,5,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(129,9,6,'{\"statistics_name\":\"enum_count.enums\"}',6,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(130,9,28,NULL,7,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(131,9,7,NULL,8,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(132,9,8,NULL,9,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(133,9,9,NULL,10,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(134,9,10,NULL,11,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(135,9,17,NULL,12,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(136,9,19,NULL,13,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(139,10,1,NULL,1,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(140,10,2,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(141,10,3,NULL,3,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(142,10,4,NULL,4,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(143,10,6,'{\"statistics_name\":\"table_count.total\"}',6,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(144,10,7,NULL,7,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(145,10,8,NULL,8,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(146,10,9,NULL,9,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(147,10,10,NULL,10,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(148,10,17,NULL,11,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(149,10,19,NULL,12,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(150,8,29,NULL,7,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(151,1,30,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(152,2,30,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(153,3,30,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(154,4,30,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(155,5,30,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(156,6,30,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(157,7,30,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(158,8,30,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(159,9,30,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(160,10,30,NULL,2,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(161,3,31,NULL,6,'2026-05-11 07:21:45','2026-05-11 07:21:45'),(162,4,31,NULL,7,'2026-05-11 07:21:45','2026-05-11 07:21:45');
/*!40000 ALTER TABLE `t_ds_relation_rule_input_entry` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_relation_sub_workflow`
--

DROP TABLE IF EXISTS `t_ds_relation_sub_workflow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_relation_sub_workflow` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `parent_workflow_instance_id` bigint NOT NULL,
  `parent_task_code` bigint NOT NULL,
  `sub_workflow_instance_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_parent_workflow_instance_id` (`parent_workflow_instance_id`),
  KEY `idx_parent_task_code` (`parent_task_code`),
  KEY `idx_sub_workflow_instance_id` (`sub_workflow_instance_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_relation_sub_workflow`
--

LOCK TABLES `t_ds_relation_sub_workflow` WRITE;
/*!40000 ALTER TABLE `t_ds_relation_sub_workflow` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_relation_sub_workflow` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_relation_udfs_user`
--

DROP TABLE IF EXISTS `t_ds_relation_udfs_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_relation_udfs_user` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `user_id` int NOT NULL COMMENT 'userid',
  `udf_id` int DEFAULT NULL COMMENT 'udf id',
  `perm` int DEFAULT '1' COMMENT 'limits of authority',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_relation_udfs_user`
--

LOCK TABLES `t_ds_relation_udfs_user` WRITE;
/*!40000 ALTER TABLE `t_ds_relation_udfs_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_relation_udfs_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_resources`
--

DROP TABLE IF EXISTS `t_ds_resources`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_resources` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `alias` varchar(64) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'alias',
  `file_name` varchar(64) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'file name',
  `description` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `user_id` int DEFAULT NULL COMMENT 'user id',
  `type` tinyint DEFAULT NULL COMMENT 'resource type,0:FILEï¼Œ1:UDF',
  `size` bigint DEFAULT NULL COMMENT 'resource size',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  `pid` int DEFAULT NULL,
  `full_name` varchar(128) COLLATE utf8mb3_bin DEFAULT NULL,
  `is_directory` tinyint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `t_ds_resources_un` (`full_name`,`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_resources`
--

LOCK TABLES `t_ds_resources` WRITE;
/*!40000 ALTER TABLE `t_ds_resources` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_resources` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_schedules`
--

DROP TABLE IF EXISTS `t_ds_schedules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_schedules` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `process_definition_code` bigint NOT NULL COMMENT 'process definition code',
  `start_time` datetime NOT NULL COMMENT 'start time',
  `end_time` datetime NOT NULL COMMENT 'end time',
  `timezone_id` varchar(40) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'schedule timezone id',
  `crontab` varchar(255) COLLATE utf8mb3_bin NOT NULL COMMENT 'crontab description',
  `failure_strategy` tinyint NOT NULL COMMENT 'failure strategy. 0:end,1:continue',
  `user_id` int NOT NULL COMMENT 'user id',
  `release_state` tinyint NOT NULL COMMENT 'release state. 0:offline,1:online ',
  `warning_type` tinyint NOT NULL COMMENT 'Alarm type: 0 is not sent, 1 process is sent successfully, 2 process is sent failed, 3 process is sent successfully and all failures are sent',
  `warning_group_id` int DEFAULT NULL COMMENT 'alert group id',
  `process_instance_priority` int DEFAULT '2' COMMENT 'process instance priorityï¼š0 Highest,1 High,2 Medium,3 Low,4 Lowest',
  `worker_group` varchar(255) COLLATE utf8mb3_bin DEFAULT '' COMMENT 'worker group id',
  `tenant_code` varchar(64) COLLATE utf8mb3_bin DEFAULT 'default' COMMENT 'tenant code',
  `environment_code` bigint DEFAULT '-1' COMMENT 'environment code',
  `create_time` datetime NOT NULL COMMENT 'create time',
  `update_time` datetime NOT NULL COMMENT 'update time',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_schedules`
--

LOCK TABLES `t_ds_schedules` WRITE;
/*!40000 ALTER TABLE `t_ds_schedules` DISABLE KEYS */;
INSERT INTO `t_ds_schedules` VALUES (1,173135002280256,'2026-05-11 00:00:00','2126-05-11 00:00:00','Asia/Shanghai','0 0 * * * ? *',1,1,0,0,0,2,'default','default',-1,'2026-05-11 22:45:57','2026-05-11 22:45:57'),(3,173184205699456,'2020-01-01 00:00:00','2099-12-31 23:59:59','Asia/Shanghai','0 0 2 * * ?',1,1,0,0,0,2,'default','default',-1,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(4,173184206033280,'2020-01-01 00:00:00','2099-12-31 23:59:59','Asia/Shanghai','0 30 23 * * ?',1,1,0,0,0,2,'default','default',-1,'2026-05-12 11:13:21','2026-05-12 11:13:21');
/*!40000 ALTER TABLE `t_ds_schedules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_session`
--

DROP TABLE IF EXISTS `t_ds_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_session` (
  `id` varchar(64) COLLATE utf8mb3_bin NOT NULL COMMENT 'key',
  `user_id` int DEFAULT NULL COMMENT 'user id',
  `ip` varchar(45) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'ip',
  `last_login_time` datetime DEFAULT NULL COMMENT 'last login time',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_session`
--

LOCK TABLES `t_ds_session` WRITE;
/*!40000 ALTER TABLE `t_ds_session` DISABLE KEYS */;
INSERT INTO `t_ds_session` VALUES ('120cd5f4-a892-4489-896a-38c924d42d49',1,NULL,'2026-05-13 16:39:56');
/*!40000 ALTER TABLE `t_ds_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_task_definition`
--

DROP TABLE IF EXISTS `t_ds_task_definition`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_task_definition` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'self-increasing id',
  `code` bigint NOT NULL COMMENT 'encoding',
  `name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'task definition name',
  `version` int NOT NULL DEFAULT '1' COMMENT 'task definition version',
  `description` text COLLATE utf8mb3_bin COMMENT 'description',
  `project_code` bigint NOT NULL COMMENT 'project code',
  `user_id` int DEFAULT NULL COMMENT 'task definition creator id',
  `task_type` varchar(50) COLLATE utf8mb3_bin NOT NULL COMMENT 'task type',
  `task_execute_type` int DEFAULT '0' COMMENT 'task execute type: 0-batch, 1-stream',
  `task_params` longtext COLLATE utf8mb3_bin COMMENT 'job custom parameters',
  `flag` tinyint DEFAULT NULL COMMENT '0 not available, 1 available',
  `is_cache` tinyint DEFAULT '0' COMMENT '0 not available, 1 available',
  `task_priority` tinyint DEFAULT '2' COMMENT 'job priority',
  `worker_group` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'worker grouping',
  `environment_code` bigint DEFAULT '-1' COMMENT 'environment code',
  `fail_retry_times` int DEFAULT NULL COMMENT 'number of failed retries',
  `fail_retry_interval` int DEFAULT NULL COMMENT 'failed retry interval',
  `timeout_flag` tinyint DEFAULT '0' COMMENT 'timeout flag:0 close, 1 open',
  `timeout_notify_strategy` tinyint DEFAULT NULL COMMENT 'timeout notification policy: 0 warning, 1 fail',
  `timeout` int DEFAULT '0' COMMENT 'timeout length,unit: minute',
  `delay_time` int DEFAULT '0' COMMENT 'delay execution time,unit: minute',
  `resource_ids` text COLLATE utf8mb3_bin COMMENT 'resource id, separated by comma',
  `task_group_id` int DEFAULT NULL COMMENT 'task group id',
  `task_group_priority` tinyint DEFAULT '0' COMMENT 'task group priority',
  `cpu_quota` int NOT NULL DEFAULT '-1' COMMENT 'cpuQuota(%): -1:Infinity',
  `memory_max` int NOT NULL DEFAULT '-1' COMMENT 'MemoryMax(MB): -1:Infinity',
  `create_time` datetime NOT NULL COMMENT 'create time',
  `update_time` datetime NOT NULL COMMENT 'update time',
  PRIMARY KEY (`id`,`code`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_task_definition`
--

LOCK TABLES `t_ds_task_definition` WRITE;
/*!40000 ALTER TABLE `t_ds_task_definition` DISABLE KEYS */;
INSERT INTO `t_ds_task_definition` VALUES (1,173134919774528,'demo01',1,'',173134550388032,1,'SHELL',0,'{\"localParams\":[],\"rawScript\":\"111\",\"resourceList\":[]}',1,0,2,'default',-1,0,1,0,NULL,0,0,NULL,0,0,-1,-1,'2026-05-11 21:51:39','2026-05-11 21:51:39'),(2,173134988690752,'1',1,'1',173134550388032,1,'SHELL',0,'{\"localParams\":[],\"rawScript\":\"1\",\"resourceList\":[]}',1,0,2,'default',-1,0,1,0,NULL,0,0,NULL,0,0,-1,-1,'2026-05-11 21:52:31','2026-05-11 21:52:31'),(3,173179728524672,'demo02',1,'',173134550388032,1,'SHELL',0,'{\"localParams\":[],\"rawScript\":\"11\",\"resourceList\":[]}',1,0,2,'default',-1,0,1,0,NULL,0,0,NULL,0,0,-1,-1,'2026-05-12 10:00:44','2026-05-12 10:00:44'),(6,173184205689216,'datax_extract',1,'DataX 用户表同步示例(streamreader→streamwriter)',173134550388032,1,'SHELL',0,'{\"rawScript\":\"set -e\\nJOB_FILE=/tmp/datax_job_$$_$(date +%s).json\\ncat > \\\"$JOB_FILE\\\" <<\'PORTAL_DATAX_EOF\'\\n{\\n  \\\"job\\\": {\\n    \\\"content\\\": [\\n      {\\n        \\\"reader\\\": {\\n          \\\"name\\\": \\\"streamreader\\\",\\n          \\\"parameter\\\": {\\n            \\\"sliceRecordCount\\\": 5,\\n            \\\"column\\\": [\\n              {\\n                \\\"type\\\": \\\"string\\\",\\n                \\\"value\\\": \\\"demo-user\\\"\\n              },\\n              {\\n                \\\"type\\\": \\\"long\\\",\\n                \\\"value\\\": 100\\n              }\\n            ]\\n          }\\n        },\\n        \\\"writer\\\": {\\n          \\\"name\\\": \\\"streamwriter\\\",\\n          \\\"parameter\\\": {\\n            \\\"print\\\": true,\\n            \\\"encoding\\\": \\\"UTF-8\\\"\\n          }\\n        }\\n      }\\n    ],\\n    \\\"setting\\\": {\\n      \\\"speed\\\": {\\n        \\\"channel\\\": 1\\n      }\\n    }\\n  }\\n}\\nPORTAL_DATAX_EOF\\necho \\\"[Portal] datax job file: $JOB_FILE\\\"\\npython /opt/datax/bin/datax.py \\\"$JOB_FILE\\\"\\nrm -f \\\"$JOB_FILE\\\"\\n\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,10,0,NULL,0,0,-1,-1,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(7,173184205689217,'transform',1,'Python 数据处理示例 (打印当前时间和环境)',173134550388032,1,'PYTHON',0,'{\"rawScript\":\"import datetime\\nprint(\'[transform] starting at\', datetime.datetime.now())\\nprint(\'[transform] done\')\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,2,0,NULL,0,0,-1,-1,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(8,173184205689218,'alert',1,'工作流末尾汇总日志',173134550388032,1,'SHELL',0,'{\"rawScript\":\"echo \'[summary] pipeline finished\' && date && echo \'OK\'\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,1,0,NULL,0,0,-1,-1,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(9,173184206025088,'cleanup',1,'Shell 清理临时文件示例',173134550388032,1,'SHELL',0,'{\"rawScript\":\"echo \'[cleanup] start\' && date && echo \'[cleanup] done\'\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,1,0,NULL,0,0,-1,-1,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(10,173184206025089,'alert',1,'工作流末尾汇总日志',173134550388032,1,'SHELL',0,'{\"rawScript\":\"echo \'[summary] pipeline finished\' && date && echo \'OK\'\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,1,0,NULL,0,0,-1,-1,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(11,173184206360960,'sql_extract',1,'从 Portal MySQL 抽取用户表',173134550388032,1,'SQL',0,'{\"type\":\"MYSQL\",\"datasource\":3,\"sql\":\"SELECT id, username, created_at FROM sys_user LIMIT 100;\",\"sqlType\":\"0\",\"preStatements\":[],\"postStatements\":[],\"displayRows\":10,\"localParams\":[],\"resourceList\":[]}',1,0,2,'default',-1,0,1,1,NULL,5,0,NULL,0,0,-1,-1,'2026-05-12 11:13:22','2026-05-12 11:13:22'),(12,173184206360961,'transform',1,'Python 数据处理示例 (打印当前时间和环境)',173134550388032,1,'PYTHON',0,'{\"rawScript\":\"import datetime\\nprint(\'[transform] starting at\', datetime.datetime.now())\\nprint(\'[transform] done\')\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,2,0,NULL,0,0,-1,-1,'2026-05-12 11:13:22','2026-05-12 11:13:22'),(13,173278852477312,'123',1,'',173134550388032,1,'SQL',0,'{\"type\":\"MYSQL\",\"datasource\":5,\"sql\":\"SELECT * FROM ads_brand_insight_question\",\"sqlType\":\"0\",\"preStatements\":[],\"postStatements\":[],\"displayRows\":10,\"localParams\":[],\"resourceList\":[]}',1,0,2,'default',-1,0,1,0,NULL,0,0,NULL,0,0,-1,-1,'2026-05-13 12:53:49','2026-05-13 12:53:49'),(14,173278852477313,'transform_user_data',1,'Python 数据处理示例 (打印当前时间和环境)',173134550388032,1,'PYTHON',0,'{\"rawScript\":\"import datetime\\nprint(\'[transform] starting at\', datetime.datetime.now())\\nprint(\'[transform] done\')\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,2,0,NULL,0,0,-1,-1,'2026-05-13 12:53:49','2026-05-13 12:53:49'),(15,173278852477314,'extract_users_from_portal',1,'从 Portal MySQL 抽取用户表',173134550388032,1,'SQL',0,'{\"type\":\"MYSQL\",\"datasource\":3,\"sql\":\"SELECT id, username, created_at FROM sys_user LIMIT 100;\",\"sqlType\":\"0\",\"preStatements\":[],\"postStatements\":[],\"displayRows\":10,\"localParams\":[],\"resourceList\":[]}',1,0,2,'default',-1,0,1,1,NULL,5,0,NULL,0,0,-1,-1,'2026-05-13 12:53:49','2026-05-13 12:53:49'),(16,173285883079040,'123',1,'',173134550388032,1,'SQL',0,'{\"type\":\"MYSQL\",\"datasource\":5,\"sql\":\"SELECT * FROM ads_brand_insight_question\",\"sqlType\":\"0\",\"preStatements\":[],\"postStatements\":[],\"displayRows\":10,\"localParams\":[],\"resourceList\":[]}',1,0,2,'default',-1,0,1,0,NULL,0,0,NULL,0,0,-1,-1,'2026-05-13 14:48:15','2026-05-13 14:48:15');
/*!40000 ALTER TABLE `t_ds_task_definition` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_task_definition_log`
--

DROP TABLE IF EXISTS `t_ds_task_definition_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_task_definition_log` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'self-increasing id',
  `code` bigint NOT NULL COMMENT 'encoding',
  `name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'task definition name',
  `version` int NOT NULL DEFAULT '1' COMMENT 'task definition version',
  `description` text COLLATE utf8mb3_bin COMMENT 'description',
  `project_code` bigint NOT NULL COMMENT 'project code',
  `user_id` int DEFAULT NULL COMMENT 'task definition creator id',
  `task_type` varchar(50) COLLATE utf8mb3_bin NOT NULL COMMENT 'task type',
  `task_execute_type` int DEFAULT '0' COMMENT 'task execute type: 0-batch, 1-stream',
  `task_params` longtext COLLATE utf8mb3_bin COMMENT 'job custom parameters',
  `flag` tinyint DEFAULT NULL COMMENT '0 not available, 1 available',
  `is_cache` tinyint DEFAULT '0' COMMENT '0 not available, 1 available',
  `task_priority` tinyint DEFAULT '2' COMMENT 'job priority',
  `worker_group` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'worker grouping',
  `environment_code` bigint DEFAULT '-1' COMMENT 'environment code',
  `fail_retry_times` int DEFAULT NULL COMMENT 'number of failed retries',
  `fail_retry_interval` int DEFAULT NULL COMMENT 'failed retry interval',
  `timeout_flag` tinyint DEFAULT '0' COMMENT 'timeout flag:0 close, 1 open',
  `timeout_notify_strategy` tinyint DEFAULT NULL COMMENT 'timeout notification policy: 0 warning, 1 fail',
  `timeout` int DEFAULT '0' COMMENT 'timeout length,unit: minute',
  `delay_time` int DEFAULT '0' COMMENT 'delay execution time,unit: minute',
  `resource_ids` text COLLATE utf8mb3_bin COMMENT 'resource id, separated by comma',
  `operator` int DEFAULT NULL COMMENT 'operator user id',
  `task_group_id` int DEFAULT NULL COMMENT 'task group id',
  `task_group_priority` tinyint DEFAULT '0' COMMENT 'task group priority',
  `operate_time` datetime DEFAULT NULL COMMENT 'operate time',
  `cpu_quota` int NOT NULL DEFAULT '-1' COMMENT 'cpuQuota(%): -1:Infinity',
  `memory_max` int NOT NULL DEFAULT '-1' COMMENT 'MemoryMax(MB): -1:Infinity',
  `create_time` datetime NOT NULL COMMENT 'create time',
  `update_time` datetime NOT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  KEY `idx_code_version` (`code`,`version`),
  KEY `idx_project_code` (`project_code`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_task_definition_log`
--

LOCK TABLES `t_ds_task_definition_log` WRITE;
/*!40000 ALTER TABLE `t_ds_task_definition_log` DISABLE KEYS */;
INSERT INTO `t_ds_task_definition_log` VALUES (1,173134919774528,'demo01',1,'',173134550388032,1,'SHELL',0,'{\"localParams\":[],\"rawScript\":\"111\",\"resourceList\":[]}',1,0,2,'default',-1,0,1,0,NULL,0,0,NULL,1,0,0,'2026-05-11 21:51:39',-1,-1,'2026-05-11 21:51:39','2026-05-11 21:51:39'),(2,173134988690752,'1',1,'1',173134550388032,1,'SHELL',0,'{\"localParams\":[],\"rawScript\":\"1\",\"resourceList\":[]}',1,0,2,'default',-1,0,1,0,NULL,0,0,NULL,1,0,0,'2026-05-11 21:52:31',-1,-1,'2026-05-11 21:52:31','2026-05-11 21:52:31'),(3,173179728524672,'demo02',1,'',173134550388032,1,'SHELL',0,'{\"localParams\":[],\"rawScript\":\"11\",\"resourceList\":[]}',1,0,2,'default',-1,0,1,0,NULL,0,0,NULL,1,0,0,'2026-05-12 10:00:44',-1,-1,'2026-05-12 10:00:44','2026-05-12 10:00:44'),(6,173184205689216,'datax_extract',1,'DataX 用户表同步示例(streamreader→streamwriter)',173134550388032,1,'SHELL',0,'{\"rawScript\":\"set -e\\nJOB_FILE=/tmp/datax_job_$$_$(date +%s).json\\ncat > \\\"$JOB_FILE\\\" <<\'PORTAL_DATAX_EOF\'\\n{\\n  \\\"job\\\": {\\n    \\\"content\\\": [\\n      {\\n        \\\"reader\\\": {\\n          \\\"name\\\": \\\"streamreader\\\",\\n          \\\"parameter\\\": {\\n            \\\"sliceRecordCount\\\": 5,\\n            \\\"column\\\": [\\n              {\\n                \\\"type\\\": \\\"string\\\",\\n                \\\"value\\\": \\\"demo-user\\\"\\n              },\\n              {\\n                \\\"type\\\": \\\"long\\\",\\n                \\\"value\\\": 100\\n              }\\n            ]\\n          }\\n        },\\n        \\\"writer\\\": {\\n          \\\"name\\\": \\\"streamwriter\\\",\\n          \\\"parameter\\\": {\\n            \\\"print\\\": true,\\n            \\\"encoding\\\": \\\"UTF-8\\\"\\n          }\\n        }\\n      }\\n    ],\\n    \\\"setting\\\": {\\n      \\\"speed\\\": {\\n        \\\"channel\\\": 1\\n      }\\n    }\\n  }\\n}\\nPORTAL_DATAX_EOF\\necho \\\"[Portal] datax job file: $JOB_FILE\\\"\\npython /opt/datax/bin/datax.py \\\"$JOB_FILE\\\"\\nrm -f \\\"$JOB_FILE\\\"\\n\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,10,0,NULL,1,0,0,'2026-05-12 11:13:21',-1,-1,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(7,173184205689217,'transform',1,'Python 数据处理示例 (打印当前时间和环境)',173134550388032,1,'PYTHON',0,'{\"rawScript\":\"import datetime\\nprint(\'[transform] starting at\', datetime.datetime.now())\\nprint(\'[transform] done\')\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,2,0,NULL,1,0,0,'2026-05-12 11:13:21',-1,-1,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(8,173184205689218,'alert',1,'工作流末尾汇总日志',173134550388032,1,'SHELL',0,'{\"rawScript\":\"echo \'[summary] pipeline finished\' && date && echo \'OK\'\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,1,0,NULL,1,0,0,'2026-05-12 11:13:21',-1,-1,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(9,173184206025088,'cleanup',1,'Shell 清理临时文件示例',173134550388032,1,'SHELL',0,'{\"rawScript\":\"echo \'[cleanup] start\' && date && echo \'[cleanup] done\'\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,1,0,NULL,1,0,0,'2026-05-12 11:13:21',-1,-1,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(10,173184206025089,'alert',1,'工作流末尾汇总日志',173134550388032,1,'SHELL',0,'{\"rawScript\":\"echo \'[summary] pipeline finished\' && date && echo \'OK\'\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,1,0,NULL,1,0,0,'2026-05-12 11:13:21',-1,-1,'2026-05-12 11:13:21','2026-05-12 11:13:21'),(11,173184206360960,'sql_extract',1,'从 Portal MySQL 抽取用户表',173134550388032,1,'SQL',0,'{\"type\":\"MYSQL\",\"datasource\":3,\"sql\":\"SELECT id, username, created_at FROM sys_user LIMIT 100;\",\"sqlType\":\"0\",\"preStatements\":[],\"postStatements\":[],\"displayRows\":10,\"localParams\":[],\"resourceList\":[]}',1,0,2,'default',-1,0,1,1,NULL,5,0,NULL,1,0,0,'2026-05-12 11:13:22',-1,-1,'2026-05-12 11:13:22','2026-05-12 11:13:22'),(12,173184206360961,'transform',1,'Python 数据处理示例 (打印当前时间和环境)',173134550388032,1,'PYTHON',0,'{\"rawScript\":\"import datetime\\nprint(\'[transform] starting at\', datetime.datetime.now())\\nprint(\'[transform] done\')\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,2,0,NULL,1,0,0,'2026-05-12 11:13:22',-1,-1,'2026-05-12 11:13:22','2026-05-12 11:13:22'),(13,173278852477312,'123',1,'',173134550388032,1,'SQL',0,'{\"type\":\"MYSQL\",\"datasource\":5,\"sql\":\"SELECT * FROM ads_brand_insight_question\",\"sqlType\":\"0\",\"preStatements\":[],\"postStatements\":[],\"displayRows\":10,\"localParams\":[],\"resourceList\":[]}',1,0,2,'default',-1,0,1,0,NULL,0,0,NULL,1,0,0,'2026-05-13 12:53:49',-1,-1,'2026-05-13 12:53:49','2026-05-13 12:53:49'),(14,173278852477313,'transform_user_data',1,'Python 数据处理示例 (打印当前时间和环境)',173134550388032,1,'PYTHON',0,'{\"rawScript\":\"import datetime\\nprint(\'[transform] starting at\', datetime.datetime.now())\\nprint(\'[transform] done\')\",\"resourceList\":[],\"localParams\":[]}',1,0,2,'default',-1,0,1,1,NULL,2,0,NULL,1,0,0,'2026-05-13 12:53:49',-1,-1,'2026-05-13 12:53:49','2026-05-13 12:53:49'),(15,173278852477314,'extract_users_from_portal',1,'从 Portal MySQL 抽取用户表',173134550388032,1,'SQL',0,'{\"type\":\"MYSQL\",\"datasource\":3,\"sql\":\"SELECT id, username, created_at FROM sys_user LIMIT 100;\",\"sqlType\":\"0\",\"preStatements\":[],\"postStatements\":[],\"displayRows\":10,\"localParams\":[],\"resourceList\":[]}',1,0,2,'default',-1,0,1,1,NULL,5,0,NULL,1,0,0,'2026-05-13 12:53:49',-1,-1,'2026-05-13 12:53:49','2026-05-13 12:53:49'),(16,173285883079040,'123',1,'',173134550388032,1,'SQL',0,'{\"type\":\"MYSQL\",\"datasource\":5,\"sql\":\"SELECT * FROM ads_brand_insight_question\",\"sqlType\":\"0\",\"preStatements\":[],\"postStatements\":[],\"displayRows\":10,\"localParams\":[],\"resourceList\":[]}',1,0,2,'default',-1,0,1,0,NULL,0,0,NULL,1,0,0,'2026-05-13 14:48:15',-1,-1,'2026-05-13 14:48:15','2026-05-13 14:48:15');
/*!40000 ALTER TABLE `t_ds_task_definition_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_task_group`
--

DROP TABLE IF EXISTS `t_ds_task_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_task_group` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'task_group name',
  `description` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `group_size` int NOT NULL COMMENT 'group size',
  `use_size` int DEFAULT '0' COMMENT 'used size',
  `user_id` int DEFAULT NULL COMMENT 'creator id',
  `project_code` bigint DEFAULT '0' COMMENT 'project code',
  `status` tinyint DEFAULT '1' COMMENT '0 not available, 1 available',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_task_group`
--

LOCK TABLES `t_ds_task_group` WRITE;
/*!40000 ALTER TABLE `t_ds_task_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_task_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_task_group_queue`
--

DROP TABLE IF EXISTS `t_ds_task_group_queue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_task_group_queue` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `task_id` int DEFAULT NULL COMMENT 'taskintanceid',
  `task_name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'TaskInstance name',
  `group_id` int DEFAULT NULL COMMENT 'taskGroup id',
  `process_id` int DEFAULT NULL COMMENT 'processInstace id',
  `priority` int DEFAULT '0' COMMENT 'priority',
  `status` tinyint DEFAULT '-1' COMMENT '-1: waiting  1: running  2: finished',
  `force_start` tinyint DEFAULT '0' COMMENT 'is force start 0 NO ,1 YES',
  `in_queue` tinyint DEFAULT '0' COMMENT 'ready to get the queue by other task finish 0 NO ,1 YES',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_t_ds_task_group_queue_in_queue` (`in_queue`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_task_group_queue`
--

LOCK TABLES `t_ds_task_group_queue` WRITE;
/*!40000 ALTER TABLE `t_ds_task_group_queue` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_task_group_queue` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_task_instance`
--

DROP TABLE IF EXISTS `t_ds_task_instance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_task_instance` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'task name',
  `task_type` varchar(50) COLLATE utf8mb3_bin NOT NULL COMMENT 'task type',
  `task_execute_type` int DEFAULT '0' COMMENT 'task execute type: 0-batch, 1-stream',
  `task_code` bigint NOT NULL COMMENT 'task definition code',
  `task_definition_version` int NOT NULL DEFAULT '1' COMMENT 'task definition version',
  `process_instance_id` int DEFAULT NULL COMMENT 'process instance id',
  `process_instance_name` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'process instance name',
  `project_code` bigint DEFAULT NULL COMMENT 'project code',
  `state` tinyint DEFAULT NULL COMMENT 'Status: 0 commit succeeded, 1 running, 2 prepare to pause, 3 pause, 4 prepare to stop, 5 stop, 6 fail, 7 succeed, 8 need fault tolerance, 9 kill, 10 wait for thread, 11 wait for dependency to complete',
  `submit_time` datetime DEFAULT NULL COMMENT 'task submit time',
  `start_time` datetime DEFAULT NULL COMMENT 'task start time',
  `end_time` datetime DEFAULT NULL COMMENT 'task end time',
  `host` varchar(135) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'host of task running on',
  `execute_path` varchar(200) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'task execute path in the host',
  `log_path` longtext COLLATE utf8mb3_bin COMMENT 'task log path',
  `alert_flag` tinyint DEFAULT NULL COMMENT 'whether alert',
  `retry_times` int DEFAULT '0' COMMENT 'task retry times',
  `pid` int DEFAULT NULL COMMENT 'pid of task',
  `app_link` text COLLATE utf8mb3_bin COMMENT 'yarn app id',
  `task_params` longtext COLLATE utf8mb3_bin COMMENT 'job custom parameters',
  `flag` tinyint DEFAULT '1' COMMENT '0 not available, 1 available',
  `is_cache` tinyint DEFAULT '0' COMMENT '0 not available, 1 available',
  `cache_key` varchar(200) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'cache_key',
  `retry_interval` int DEFAULT NULL COMMENT 'retry interval when task failed ',
  `max_retry_times` int DEFAULT NULL COMMENT 'max retry times',
  `task_instance_priority` int DEFAULT NULL COMMENT 'task instance priority:0 Highest,1 High,2 Medium,3 Low,4 Lowest',
  `worker_group` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'worker group id',
  `environment_code` bigint DEFAULT '-1' COMMENT 'environment code',
  `environment_config` text COLLATE utf8mb3_bin COMMENT 'this config contains many environment variables config',
  `executor_id` int DEFAULT NULL,
  `executor_name` varchar(64) COLLATE utf8mb3_bin DEFAULT NULL,
  `first_submit_time` datetime DEFAULT NULL COMMENT 'task first submit time',
  `delay_time` int DEFAULT '0' COMMENT 'task delay execution time',
  `var_pool` longtext COLLATE utf8mb3_bin COMMENT 'var_pool',
  `task_group_id` int DEFAULT NULL COMMENT 'task group id',
  `dry_run` tinyint DEFAULT '0' COMMENT 'dry run flag: 0 normal, 1 dry run',
  `cpu_quota` int NOT NULL DEFAULT '-1' COMMENT 'cpuQuota(%): -1:Infinity',
  `memory_max` int NOT NULL DEFAULT '-1' COMMENT 'MemoryMax(MB): -1:Infinity',
  `test_flag` tinyint DEFAULT NULL COMMENT 'test flagï¼š0 normal, 1 test run',
  PRIMARY KEY (`id`),
  KEY `process_instance_id` (`process_instance_id`) USING BTREE,
  KEY `idx_code_version` (`task_code`,`task_definition_version`) USING BTREE,
  KEY `idx_cache_key` (`cache_key`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_task_instance`
--

LOCK TABLES `t_ds_task_instance` WRITE;
/*!40000 ALTER TABLE `t_ds_task_instance` DISABLE KEYS */;
INSERT INTO `t_ds_task_instance` VALUES (2,'datax_extract','SHELL',0,173184205689216,1,2,'daily_user_etl-1-20260512111321946',173134550388032,6,'2026-05-12 11:13:22','2026-05-12 11:13:22','2026-05-12 11:13:23','172.18.0.8:1234','/tmp/dolphinscheduler/exec/process/root/173134550388032/173184205699456_1/2/2','/opt/dolphinscheduler/logs/20260512/173184205699456/1/2/2.log',0,0,12144,NULL,'{\"rawScript\":\"set -e\\nJOB_FILE=/tmp/datax_job_$$_$(date +%s).json\\ncat > \\\"$JOB_FILE\\\" <<\'PORTAL_DATAX_EOF\'\\n{\\n  \\\"job\\\": {\\n    \\\"content\\\": [\\n      {\\n        \\\"reader\\\": {\\n          \\\"name\\\": \\\"streamreader\\\",\\n          \\\"parameter\\\": {\\n            \\\"sliceRecordCount\\\": 5,\\n            \\\"column\\\": [\\n              {\\n                \\\"type\\\": \\\"string\\\",\\n                \\\"value\\\": \\\"demo-user\\\"\\n              },\\n              {\\n                \\\"type\\\": \\\"long\\\",\\n                \\\"value\\\": 100\\n              }\\n            ]\\n          }\\n        },\\n        \\\"writer\\\": {\\n          \\\"name\\\": \\\"streamwriter\\\",\\n          \\\"parameter\\\": {\\n            \\\"print\\\": true,\\n            \\\"encoding\\\": \\\"UTF-8\\\"\\n          }\\n        }\\n      }\\n    ],\\n    \\\"setting\\\": {\\n      \\\"speed\\\": {\\n        \\\"channel\\\": 1\\n      }\\n    }\\n  }\\n}\\nPORTAL_DATAX_EOF\\necho \\\"[Portal] datax job file: $JOB_FILE\\\"\\npython /opt/datax/bin/datax.py \\\"$JOB_FILE\\\"\\nrm -f \\\"$JOB_FILE\\\"\\n\",\"resourceList\":[],\"localParams\":[],\"conditionResult\":\"null\",\"dependence\":\"null\",\"switchResult\":\"null\",\"waitStartTimeout\":null}',1,0,NULL,1,0,2,'default',-1,NULL,1,'admin','2026-05-12 11:13:22',0,'[]',0,0,-1,-1,0),(3,'datax_extract','SHELL',0,173184205689216,1,3,'daily_user_etl-1-20260512111322957',173134550388032,6,'2026-05-12 11:13:23','2026-05-12 11:13:23','2026-05-12 11:13:24','172.18.0.8:1234','/tmp/dolphinscheduler/exec/process/root/173134550388032/173184205699456_1/3/3','/opt/dolphinscheduler/logs/20260512/173184205699456/1/3/3.log',0,0,12166,NULL,'{\"rawScript\":\"set -e\\nJOB_FILE=/tmp/datax_job_$$_$(date +%s).json\\ncat > \\\"$JOB_FILE\\\" <<\'PORTAL_DATAX_EOF\'\\n{\\n  \\\"job\\\": {\\n    \\\"content\\\": [\\n      {\\n        \\\"reader\\\": {\\n          \\\"name\\\": \\\"streamreader\\\",\\n          \\\"parameter\\\": {\\n            \\\"sliceRecordCount\\\": 5,\\n            \\\"column\\\": [\\n              {\\n                \\\"type\\\": \\\"string\\\",\\n                \\\"value\\\": \\\"demo-user\\\"\\n              },\\n              {\\n                \\\"type\\\": \\\"long\\\",\\n                \\\"value\\\": 100\\n              }\\n            ]\\n          }\\n        },\\n        \\\"writer\\\": {\\n          \\\"name\\\": \\\"streamwriter\\\",\\n          \\\"parameter\\\": {\\n            \\\"print\\\": true,\\n            \\\"encoding\\\": \\\"UTF-8\\\"\\n          }\\n        }\\n      }\\n    ],\\n    \\\"setting\\\": {\\n      \\\"speed\\\": {\\n        \\\"channel\\\": 1\\n      }\\n    }\\n  }\\n}\\nPORTAL_DATAX_EOF\\necho \\\"[Portal] datax job file: $JOB_FILE\\\"\\npython /opt/datax/bin/datax.py \\\"$JOB_FILE\\\"\\nrm -f \\\"$JOB_FILE\\\"\\n\",\"resourceList\":[],\"localParams\":[],\"conditionResult\":\"null\",\"dependence\":\"null\",\"switchResult\":\"null\",\"waitStartTimeout\":null}',1,0,NULL,1,0,2,'default',-1,NULL,1,'admin','2026-05-12 11:13:23',0,'[]',0,0,-1,-1,0),(4,'cleanup','SHELL',0,173184206025088,1,4,'nightly_cleanup-1-20260512111323971',173134550388032,7,'2026-05-12 11:13:24','2026-05-12 11:13:24','2026-05-12 11:13:25','172.18.0.8:1234','/tmp/dolphinscheduler/exec/process/root/173134550388032/173184206033280_1/4/4','/opt/dolphinscheduler/logs/20260512/173184206033280/1/4/4.log',0,0,12191,NULL,'{\"rawScript\":\"echo \'[cleanup] start\' && date && echo \'[cleanup] done\'\",\"resourceList\":[],\"localParams\":[],\"conditionResult\":\"null\",\"dependence\":\"null\",\"switchResult\":\"null\",\"waitStartTimeout\":null}',1,0,NULL,1,0,2,'default',-1,NULL,1,'admin','2026-05-12 11:13:24',0,'[]',0,0,-1,-1,0),(5,'cleanup','SHELL',0,173184206025088,1,5,'nightly_cleanup-1-20260512111324988',173134550388032,7,'2026-05-12 11:13:25','2026-05-12 11:13:25','2026-05-12 11:13:26','172.18.0.8:1234','/tmp/dolphinscheduler/exec/process/root/173134550388032/173184206033280_1/5/5','/opt/dolphinscheduler/logs/20260512/173184206033280/1/5/5.log',0,0,12211,NULL,'{\"rawScript\":\"echo \'[cleanup] start\' && date && echo \'[cleanup] done\'\",\"resourceList\":[],\"localParams\":[],\"conditionResult\":\"null\",\"dependence\":\"null\",\"switchResult\":\"null\",\"waitStartTimeout\":null}',0,0,NULL,1,0,2,'default',-1,NULL,1,'admin','2026-05-12 11:13:25',0,'[]',0,0,-1,-1,0),(6,'alert','SHELL',0,173184206025089,1,4,'nightly_cleanup-1-20260512111323971',173134550388032,7,'2026-05-12 11:13:26','2026-05-12 11:13:26','2026-05-12 11:13:27','172.18.0.8:1234','/tmp/dolphinscheduler/exec/process/root/173134550388032/173184206033280_1/4/6','/opt/dolphinscheduler/logs/20260512/173184206033280/1/4/6.log',0,0,12227,NULL,'{\"rawScript\":\"echo \'[summary] pipeline finished\' && date && echo \'OK\'\",\"resourceList\":[],\"localParams\":[],\"conditionResult\":\"null\",\"dependence\":\"null\",\"switchResult\":\"null\",\"waitStartTimeout\":null}',1,0,NULL,1,0,2,'default',-1,NULL,1,'admin','2026-05-12 11:13:26',0,'[]',0,0,-1,-1,0),(7,'alert','SHELL',0,173184206025089,1,5,'nightly_cleanup-1-20260512111324988',173134550388032,7,'2026-05-12 11:13:27','2026-05-12 11:13:27','2026-05-12 11:13:28','172.18.0.8:1234','/tmp/dolphinscheduler/exec/process/root/173134550388032/173184206033280_1/5/7','/opt/dolphinscheduler/logs/20260512/173184206033280/1/5/7.log',0,0,12239,NULL,'{\"rawScript\":\"echo \'[summary] pipeline finished\' && date && echo \'OK\'\",\"resourceList\":[],\"localParams\":[],\"conditionResult\":\"null\",\"dependence\":\"null\",\"switchResult\":\"null\",\"waitStartTimeout\":null}',0,0,NULL,1,0,2,'default',-1,NULL,1,'admin','2026-05-12 11:13:27',0,'[]',0,0,-1,-1,0),(8,'sql_extract','SQL',0,173184206360960,1,6,'user_data_export-1-20260512111327002',173134550388032,6,'2026-05-12 11:13:27','2026-05-12 11:13:27','2026-05-12 11:13:27','172.18.0.8:1234','/tmp/dolphinscheduler/exec/process/root/173134550388032/173184206372224_1/6/8','/opt/dolphinscheduler/logs/20260512/173184206372224/1/6/8.log',0,0,0,NULL,'{\"type\":\"MYSQL\",\"datasource\":3,\"sql\":\"SELECT id, username, created_at FROM sys_user LIMIT 100;\",\"sqlType\":\"0\",\"preStatements\":[],\"postStatements\":[],\"displayRows\":10,\"localParams\":[],\"resourceList\":[],\"conditionResult\":\"null\",\"dependence\":\"null\",\"switchResult\":\"null\",\"waitStartTimeout\":null}',0,0,NULL,1,0,2,'default',-1,NULL,1,'admin','2026-05-12 11:13:27',0,NULL,0,0,-1,-1,0),(9,'sql_extract','SQL',0,173184206360960,1,6,'user_data_export-1-20260512111327002',173134550388032,6,'2026-05-13 14:07:59','2026-05-13 14:07:59','2026-05-13 14:07:59','172.18.0.8:1234','/tmp/dolphinscheduler/exec/process/root/173134550388032/173184206372224_1/6/9','/opt/dolphinscheduler/logs/20260513/173184206372224/1/6/9.log',0,0,0,NULL,'{\"type\":\"MYSQL\",\"datasource\":3,\"sql\":\"SELECT id, username, created_at FROM sys_user LIMIT 100;\",\"sqlType\":\"0\",\"preStatements\":[],\"postStatements\":[],\"displayRows\":10,\"localParams\":[],\"resourceList\":[],\"conditionResult\":\"null\",\"dependence\":\"null\",\"switchResult\":\"null\",\"waitStartTimeout\":null}',1,0,NULL,1,0,2,'default',-1,NULL,1,NULL,'2026-05-13 14:07:59',0,NULL,0,0,-1,-1,0),(10,'cleanup','SHELL',0,173184206025088,1,5,'nightly_cleanup-1-20260512111324988',173134550388032,7,'2026-05-13 14:08:10','2026-05-13 14:08:10','2026-05-13 14:08:11','172.18.0.8:1234','/tmp/dolphinscheduler/exec/process/root/173134550388032/173184206033280_1/5/10','/opt/dolphinscheduler/logs/20260513/173184206033280/1/5/10.log',0,0,36136,NULL,'{\"rawScript\":\"echo \'[cleanup] start\' && date && echo \'[cleanup] done\'\",\"resourceList\":[],\"localParams\":[],\"conditionResult\":\"null\",\"dependence\":\"null\",\"switchResult\":\"null\",\"waitStartTimeout\":null}',1,0,NULL,1,0,2,'default',-1,NULL,1,NULL,'2026-05-13 14:08:10',0,'[]',0,0,-1,-1,0),(11,'alert','SHELL',0,173184206025089,1,5,'nightly_cleanup-1-20260512111324988',173134550388032,7,'2026-05-13 14:08:11','2026-05-13 14:08:11','2026-05-13 14:08:12','172.18.0.8:1234','/tmp/dolphinscheduler/exec/process/root/173134550388032/173184206033280_1/5/11','/opt/dolphinscheduler/logs/20260513/173184206033280/1/5/11.log',0,0,36146,NULL,'{\"rawScript\":\"echo \'[summary] pipeline finished\' && date && echo \'OK\'\",\"resourceList\":[],\"localParams\":[],\"conditionResult\":\"null\",\"dependence\":\"null\",\"switchResult\":\"null\",\"waitStartTimeout\":null}',1,0,NULL,1,0,2,'default',-1,NULL,1,NULL,'2026-05-13 14:08:11',0,'[]',0,0,-1,-1,0),(12,'123','SQL',0,173285883079040,1,7,'002-1-20260513151247019',173134550388032,6,'2026-05-13 15:12:47','2026-05-13 15:12:47','2026-05-13 15:12:47','172.18.0.8:1234','/tmp/dolphinscheduler/exec/process/root/173134550388032/173285883084160_1/7/12','/opt/dolphinscheduler/logs/20260513/173285883084160/1/7/12.log',0,0,0,NULL,'{\"type\":\"MYSQL\",\"datasource\":5,\"sql\":\"SELECT * FROM ads_brand_insight_question\",\"sqlType\":\"0\",\"preStatements\":[],\"postStatements\":[],\"displayRows\":10,\"localParams\":[],\"resourceList\":[],\"conditionResult\":\"null\",\"dependence\":\"null\",\"switchResult\":\"null\",\"waitStartTimeout\":null}',1,0,NULL,1,0,2,'default',-1,NULL,1,'admin','2026-05-13 15:12:47',0,NULL,0,0,-1,-1,0),(13,'123','SQL',0,173285883079040,1,8,'002-1-20260513151300036',173134550388032,6,'2026-05-13 15:13:00','2026-05-13 15:13:00','2026-05-13 15:13:00','172.18.0.8:1234','/tmp/dolphinscheduler/exec/process/root/173134550388032/173285883084160_1/8/13','/opt/dolphinscheduler/logs/20260513/173285883084160/1/8/13.log',0,0,0,NULL,'{\"type\":\"MYSQL\",\"datasource\":5,\"sql\":\"SELECT * FROM ads_brand_insight_question\",\"sqlType\":\"0\",\"preStatements\":[],\"postStatements\":[],\"displayRows\":10,\"localParams\":[],\"resourceList\":[],\"conditionResult\":\"null\",\"dependence\":\"null\",\"switchResult\":\"null\",\"waitStartTimeout\":null}',1,0,NULL,1,0,2,'default',-1,NULL,1,'admin','2026-05-13 15:13:00',0,NULL,0,0,-1,-1,0);
/*!40000 ALTER TABLE `t_ds_task_instance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_tenant`
--

DROP TABLE IF EXISTS `t_ds_tenant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_tenant` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `tenant_code` varchar(64) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'tenant code',
  `description` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `queue_id` int DEFAULT NULL COMMENT 'queue id',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_tenant_code` (`tenant_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_tenant`
--

LOCK TABLES `t_ds_tenant` WRITE;
/*!40000 ALTER TABLE `t_ds_tenant` DISABLE KEYS */;
INSERT INTO `t_ds_tenant` VALUES (-1,'default','default tenant',1,'2026-05-11 07:21:44','2026-05-11 07:21:44');
/*!40000 ALTER TABLE `t_ds_tenant` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_trigger_relation`
--

DROP TABLE IF EXISTS `t_ds_trigger_relation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_trigger_relation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `trigger_type` int NOT NULL DEFAULT '0' COMMENT '0 process 1 task',
  `trigger_code` bigint NOT NULL,
  `job_id` bigint NOT NULL,
  `create_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `t_ds_trigger_relation_UN` (`trigger_type`,`job_id`,`trigger_code`),
  KEY `t_ds_trigger_relation_trigger_code_IDX` (`trigger_code`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_trigger_relation`
--

LOCK TABLES `t_ds_trigger_relation` WRITE;
/*!40000 ALTER TABLE `t_ds_trigger_relation` DISABLE KEYS */;
INSERT INTO `t_ds_trigger_relation` VALUES (1,2,173183949730176,1,'2026-05-12 11:09:11','2026-05-12 11:09:11'),(2,0,173183949730176,1,'2026-05-12 11:09:12','2026-05-12 11:09:12'),(3,2,173184206505344,2,'2026-05-12 11:13:22','2026-05-12 11:13:22'),(4,0,173184206505344,2,'2026-05-12 11:13:22','2026-05-12 11:13:22'),(5,2,173184207631744,3,'2026-05-12 11:13:23','2026-05-12 11:13:23'),(6,0,173184207631744,3,'2026-05-12 11:13:23','2026-05-12 11:13:23'),(7,2,173184208765312,4,'2026-05-12 11:13:24','2026-05-12 11:13:24'),(8,0,173184208765312,4,'2026-05-12 11:13:24','2026-05-12 11:13:24'),(9,2,173184209896832,5,'2026-05-12 11:13:25','2026-05-12 11:13:25'),(10,0,173184209896832,5,'2026-05-12 11:13:25','2026-05-12 11:13:25'),(11,2,173184211019136,6,'2026-05-12 11:13:26','2026-05-12 11:13:26'),(12,0,173184211019136,6,'2026-05-12 11:13:27','2026-05-12 11:13:27'),(13,2,173287390215552,9,'2026-05-13 15:12:47','2026-05-13 15:12:47'),(14,0,173287390215552,7,'2026-05-13 15:12:47','2026-05-13 15:12:47'),(15,2,173287402685824,10,'2026-05-13 15:12:59','2026-05-13 15:12:59'),(16,0,173287402685824,8,'2026-05-13 15:13:00','2026-05-13 15:13:00');
/*!40000 ALTER TABLE `t_ds_trigger_relation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_udfs`
--

DROP TABLE IF EXISTS `t_ds_udfs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_udfs` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'key',
  `user_id` int NOT NULL COMMENT 'user id',
  `func_name` varchar(255) COLLATE utf8mb3_bin NOT NULL COMMENT 'UDF function name',
  `class_name` varchar(255) COLLATE utf8mb3_bin NOT NULL COMMENT 'class of udf',
  `type` tinyint NOT NULL COMMENT 'Udf function type',
  `arg_types` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'arguments types',
  `database` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'data base',
  `description` varchar(255) COLLATE utf8mb3_bin DEFAULT NULL,
  `resource_id` int NOT NULL COMMENT 'resource id',
  `resource_name` varchar(255) COLLATE utf8mb3_bin NOT NULL COMMENT 'resource name',
  `create_time` datetime NOT NULL COMMENT 'create time',
  `update_time` datetime NOT NULL COMMENT 'update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_func_name` (`func_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_udfs`
--

LOCK TABLES `t_ds_udfs` WRITE;
/*!40000 ALTER TABLE `t_ds_udfs` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_udfs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_user`
--

DROP TABLE IF EXISTS `t_ds_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_user` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'user id',
  `user_name` varchar(64) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'user name',
  `user_password` varchar(64) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'user password',
  `user_type` tinyint DEFAULT NULL COMMENT 'user type, 0:administratorï¼Œ1:ordinary user',
  `email` varchar(64) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'email',
  `phone` varchar(11) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'phone',
  `tenant_id` int DEFAULT '-1' COMMENT 'tenant id',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  `queue` varchar(64) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'queue',
  `state` tinyint DEFAULT '1' COMMENT 'state 0:disable 1:enable',
  `time_zone` varchar(32) COLLATE utf8mb3_bin DEFAULT NULL COMMENT 'time zone',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_name_unique` (`user_name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_user`
--

LOCK TABLES `t_ds_user` WRITE;
/*!40000 ALTER TABLE `t_ds_user` DISABLE KEYS */;
INSERT INTO `t_ds_user` VALUES (1,'admin','7ad2410b2f4c074479a8937a28a22b8f',0,'xxx@qq.com','',-1,'2026-05-11 07:21:44','2026-05-11 07:21:44',NULL,1,NULL);
/*!40000 ALTER TABLE `t_ds_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_version`
--

DROP TABLE IF EXISTS `t_ds_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_version` (
  `id` int NOT NULL AUTO_INCREMENT,
  `version` varchar(63) COLLATE utf8mb3_bin NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `version_UNIQUE` (`version`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin COMMENT='version';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_version`
--

LOCK TABLES `t_ds_version` WRITE;
/*!40000 ALTER TABLE `t_ds_version` DISABLE KEYS */;
INSERT INTO `t_ds_version` VALUES (1,'3.3.0');
/*!40000 ALTER TABLE `t_ds_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_ds_worker_group`
--

DROP TABLE IF EXISTS `t_ds_worker_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_ds_worker_group` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'id',
  `name` varchar(255) COLLATE utf8mb3_bin NOT NULL COMMENT 'worker group name',
  `addr_list` text COLLATE utf8mb3_bin COMMENT 'worker addr list. split by [,]',
  `create_time` datetime DEFAULT NULL COMMENT 'create time',
  `update_time` datetime DEFAULT NULL COMMENT 'update time',
  `description` text COLLATE utf8mb3_bin COMMENT 'description',
  `other_params_json` text COLLATE utf8mb3_bin COMMENT 'other params json',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_ds_worker_group`
--

LOCK TABLES `t_ds_worker_group` WRITE;
/*!40000 ALTER TABLE `t_ds_worker_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_ds_worker_group` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-13  9:01:13
