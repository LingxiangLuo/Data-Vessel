#!/usr/bin/env python3
"""
存量 alert_rule 数据迁移脚本
把旧的 notify_type + notify_config 转成 sys_notify_channel 记录，并回填 notify_channel_ids

用法:
    python scripts/migrate_alert_channels.py
    python scripts/migrate_alert_channels.py --dry-run   # 只打印，不写库
"""
import argparse
import json
import os
import sys

# 允许直接运行（不在容器内）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'portal', 'backend'))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:password@127.0.0.1:3306/portal_db'
)


def migrate(dry_run: bool = False):
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # 查出所有还没有 notify_channel_ids 的旧规则
        rows = conn.execute(text(
            "SELECT id, name, notify_type, notify_config "
            "FROM alert_rule "
            "WHERE (notify_channel_ids IS NULL OR JSON_LENGTH(notify_channel_ids) = 0) "
            "  AND notify_type IS NOT NULL AND notify_type != '' "
            "ORDER BY id"
        )).fetchall()

        if not rows:
            print("没有需要迁移的规则，退出。")
            return

        print(f"找到 {len(rows)} 条需要迁移的规则\n")

        # 用于去重：(type, config_json) -> channel_id
        channel_cache: dict[tuple, int] = {}

        for row in rows:
            rule_id, rule_name, notify_type, notify_config = row
            if isinstance(notify_config, str):
                try:
                    notify_config = json.loads(notify_config)
                except Exception:
                    notify_config = {}
            notify_config = notify_config or {}

            # 构造渠道 config
            if notify_type == 'email':
                email_val = notify_config.get('email', '')
                if isinstance(email_val, list):
                    emails = email_val
                else:
                    emails = [e.strip() for e in email_val.split(',') if e.strip()]
                if not emails:
                    print(f"  规则#{rule_id} [{rule_name}] 邮箱为空，跳过")
                    continue
                ch_config = {'email': emails}
                ch_name = f"邮件-{','.join(emails[:2])}{'...' if len(emails) > 2 else ''}"
            elif notify_type in ('feishu_webhook', 'dingtalk_webhook', 'wecom_webhook'):
                url = notify_config.get('webhook_url', '').strip()
                if not url:
                    print(f"  规则#{rule_id} [{rule_name}] Webhook URL 为空，跳过")
                    continue
                ch_config = {'webhook_url': url}
                if notify_type == 'dingtalk_webhook' and notify_config.get('secret'):
                    ch_config['secret'] = notify_config['secret']
                type_label = {'feishu_webhook': '飞书', 'dingtalk_webhook': '钉钉', 'wecom_webhook': '企微'}[notify_type]
                ch_name = f"{type_label}-{url[-20:]}"
            else:
                print(f"  规则#{rule_id} [{rule_name}] 不支持的类型 {notify_type}，跳过")
                continue

            cache_key = (notify_type, json.dumps(ch_config, sort_keys=True))

            if cache_key in channel_cache:
                channel_id = channel_cache[cache_key]
                print(f"  规则#{rule_id} [{rule_name}] 复用已有渠道 #{channel_id}")
            else:
                # 先查库里有没有完全相同的渠道
                existing = conn.execute(text(
                    "SELECT id FROM sys_notify_channel WHERE type = :t AND config = :c LIMIT 1"
                ), {'t': notify_type, 'c': json.dumps(ch_config, ensure_ascii=False)}).fetchone()

                if existing:
                    channel_id = existing[0]
                    print(f"  规则#{rule_id} [{rule_name}] 匹配到已有渠道 #{channel_id}")
                else:
                    if dry_run:
                        channel_id = -1
                        print(f"  [DRY-RUN] 将创建渠道: type={notify_type} name={ch_name}")
                    else:
                        result = conn.execute(text(
                            "INSERT INTO sys_notify_channel (name, type, config, enabled) "
                            "VALUES (:name, :type, :config, 1)"
                        ), {
                            'name': ch_name,
                            'type': notify_type,
                            'config': json.dumps(ch_config, ensure_ascii=False),
                        })
                        conn.commit()
                        channel_id = result.lastrowid
                        print(f"  规则#{rule_id} [{rule_name}] 创建新渠道 #{channel_id} [{ch_name}]")

                channel_cache[cache_key] = channel_id

            if dry_run:
                print(f"  [DRY-RUN] 将更新规则#{rule_id} notify_channel_ids=[{channel_id}]")
            else:
                conn.execute(text(
                    "UPDATE alert_rule SET notify_channel_ids = :ids WHERE id = :rid"
                ), {'ids': json.dumps([channel_id]), 'rid': rule_id})
                conn.commit()
                print(f"  规则#{rule_id} [{rule_name}] 已回填 notify_channel_ids=[{channel_id}]")

    print("\n迁移完成。")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='迁移 alert_rule 通知配置到渠道表')
    parser.add_argument('--dry-run', action='store_true', help='只打印，不写库')
    args = parser.parse_args()
    migrate(dry_run=args.dry_run)
