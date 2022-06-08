/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- 様々なフラグを管理するテーブル。
CREATE TABLE IF NOT EXISTS `flag_control` (
  `flag_name` text DEFAULT NULL,
  `flag` tinyint(4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 一日一回占い用のテーブル。現在未使用
CREATE TABLE IF NOT EXISTS `fortune` (
  `id` bigint(11) unsigned NOT NULL,
  `fortune_flag` tinyint(11) DEFAULT NULL,
  `fortune_result` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 予約投稿機能に関するテーブル
CREATE TABLE IF NOT EXISTS `future_send` (
  `id` bigint(11) unsigned NOT NULL,
  `text` text DEFAULT NULL,
  `time` text DEFAULT NULL,
  `channel_id` bigint(11) DEFAULT NULL,
  `message_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- アイドルデータ
CREATE TABLE IF NOT EXISTS `idol_data` (
  `name` text DEFAULT NULL,
  `birthday` text DEFAULT NULL,
  `element` text DEFAULT NULL,
  `age` int(11) DEFAULT NULL,
  `blood_type` text DEFAULT NULL,
  `birthplace` text DEFAULT NULL,
  `hand` text DEFAULT NULL,
  `hobby` text DEFAULT NULL,
  `cv` text DEFAULT NULL,
  `done` tinyint(11) DEFAULT NULL,
  `height` int(11) DEFAULT NULL,
  `rumor1` text DEFAULT NULL,
  `rumor2` text DEFAULT NULL,
  `rumor3` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 音楽再生機能のキュー
CREATE TABLE IF NOT EXISTS `music` (
  `name` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- なおすきカウントを保存する
CREATE TABLE IF NOT EXISTS `naosuki_count` (
  `count` bigint(11) unsigned NOT NULL,
  PRIMARY KEY (`count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- なおすきスロットに関するデータ。現在未使用
CREATE TABLE IF NOT EXISTS `naosuki_record` (
  `id` bigint(11) unsigned NOT NULL,
  `time` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 読み上げ機能の調教データを保存する
CREATE TABLE IF NOT EXISTS `read_se_convert` (
  `word` text DEFAULT NULL,
  `yomi` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 読み上げるテキストのキュー
CREATE TABLE IF NOT EXISTS `read_text` (
  `user_id` bigint(20) DEFAULT NULL,
  `text_id` bigint(20) DEFAULT NULL,
  `text` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 読み上げ機能のSEを保存する
CREATE TABLE IF NOT EXISTS `read_text_se` (
  `word` text DEFAULT NULL,
  `sound_path` text DEFAULT NULL,
  `volume` double DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 取得したツイートを一時保存するテーブル
CREATE TABLE IF NOT EXISTS `Twitter_log` (
  `tweet_id` text DEFAULT NULL,
  `screen_id` text DEFAULT NULL,
  `user` text DEFAULT NULL,
  `text` text DEFAULT NULL,
  `icon` text DEFAULT NULL,
  `media1` text DEFAULT NULL,
  `media2` text DEFAULT NULL,
  `media3` text DEFAULT NULL,
  `media4` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ユーザーデータを保存する
CREATE TABLE IF NOT EXISTS `user_data` (
  `id` bigint(11) DEFAULT NULL,
  `gold` bigint(11) DEFAULT NULL,
  `birthday` text DEFAULT NULL,
  `naosuki` tinyint(11) DEFAULT NULL,
  `vc_notification` tinyint(11) DEFAULT NULL,
  `mayuge_coin` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ユーザーのサーバー参加日を保存する
CREATE TABLE IF NOT EXISTS `user_join` (
  `id` bigint(11) unsigned NOT NULL,
  `year` int(11) DEFAULT NULL,
  `month` int(11) DEFAULT NULL,
  `day` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ボイスチャットの通知機能に関するテーブル
CREATE TABLE IF NOT EXISTS `vc_notification` (
  `id` bigint(11) unsigned NOT NULL,
  `members` int(11) DEFAULT NULL,
  `reset` tinyint(11) DEFAULT NULL,
  `vc_notification` tinyint(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
