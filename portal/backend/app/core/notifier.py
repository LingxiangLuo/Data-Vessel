"""通知发送工具 — 支持邮件、飞书/钉钉/企微 Webhook"""
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx

logger = logging.getLogger(__name__)


def _get_smtp_config() -> dict:
    """从 sys_config 表读取 SMTP 配置，降级到环境变量"""
    try:
        from app.core.database import SessionLocal
        from app.models.sys_config import SysConfig
        db = SessionLocal()
        try:
            row = db.query(SysConfig).filter(SysConfig.key == "smtp_config").first()
            if row and row.value:
                return row.value
        finally:
            db.close()
    except Exception:
        pass
    return {
        "host": os.getenv("SMTP_HOST", "smtp.163.com"),
        "port": int(os.getenv("SMTP_PORT", "465")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "use_ssl": os.getenv("SMTP_SSL", "true").lower() == "true",
        "sender_name": os.getenv("SMTP_SENDER_NAME", "数据中台"),
    }


async def send_feishu_webhook(webhook_url: str, title: str, content: str) -> bool:
    """发送飞书机器人消息（富文本卡片）"""
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "red",
            },
            "elements": [
                {"tag": "markdown", "content": content},
            ],
        },
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0 or data.get("StatusCode") == 0:
                    return True
                logger.warning(f"飞书 Webhook 返回错误: {data}")
                return False
            logger.warning(f"飞书 Webhook HTTP {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"飞书 Webhook 发送失败: {e}")
        return False


async def send_dingtalk_webhook(webhook_url: str, title: str, content: str, secret: str = None) -> bool:
    """发送钉钉机器人消息（Markdown 卡片）"""
    import time
    import hmac
    import hashlib
    import base64
    import urllib.parse

    headers = {}
    url = webhook_url
    if secret:
        timestamp = str(round(time.time() * 1000))
        sign_str = f"{timestamp}\n{secret}"
        sign = base64.b64encode(
            hmac.new(secret.encode("utf-8"), sign_str.encode("utf-8"), digestmod=hashlib.sha256).digest()
        ).decode("utf-8")
        url = f"{webhook_url}&timestamp={timestamp}&sign={urllib.parse.quote_plus(sign)}"

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": f"## {title}\n\n{content}",
        },
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("errcode") == 0:
                    return True
                logger.warning(f"钉钉 Webhook 返回错误: {data}")
                return False
            logger.warning(f"钉钉 Webhook HTTP {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"钉钉 Webhook 发送失败: {e}")
        return False


async def send_wecom_webhook(webhook_url: str, title: str, content: str) -> bool:
    """发送企业微信机器人消息（Markdown）"""
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"## {title}\n{content}",
        },
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("errcode") == 0:
                    return True
                logger.warning(f"企微 Webhook 返回错误: {data}")
                return False
            logger.warning(f"企微 Webhook HTTP {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"企微 Webhook 发送失败: {e}")
        return False


def send_email(to: str, subject: str, body: str, smtp_config: dict = None) -> bool:
    """发送邮件通知"""
    config = smtp_config or _get_smtp_config()
    if not config.get("user"):
        logger.warning("SMTP 未配置，跳过邮件发送")
        return False
    sender_name = config.get("sender_name", "数据中台")
    from_addr = f"{sender_name} <{config['user']}>"
    try:
        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html", "utf-8"))
        if config.get("use_ssl", True):
            server = smtplib.SMTP_SSL(config["host"], config["port"], timeout=10)
        else:
            server = smtplib.SMTP(config["host"], config["port"], timeout=10)
            server.starttls()
        server.login(config["user"], config["password"])
        server.sendmail(config["user"], [to], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False


def _load_channels(channel_ids: list) -> list:
    """从数据库加载通知渠道配置"""
    try:
        from app.core.database import SessionLocal
        from app.models.sys_notify_channel import SysNotifyChannel
        db = SessionLocal()
        try:
            return (
                db.query(SysNotifyChannel)
                .filter(
                    SysNotifyChannel.id.in_(channel_ids),
                    SysNotifyChannel.enabled == True,
                )
                .all()
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"加载通知渠道失败: {e}")
        return []


async def _send_via_channel(channel, title: str, content: str) -> bool:
    """根据渠道类型调用对应的发送函数"""
    cfg = channel.config or {}

    if channel.type == "feishu_webhook":
        url = cfg.get("webhook_url", "")
        if not url:
            logger.warning(f"渠道 {channel.name} 飞书 Webhook URL 为空")
            return False
        return await send_feishu_webhook(url, title, content)

    elif channel.type == "dingtalk_webhook":
        url = cfg.get("webhook_url", "")
        if not url:
            logger.warning(f"渠道 {channel.name} 钉钉 Webhook URL 为空")
            return False
        return await send_dingtalk_webhook(url, title, content, secret=cfg.get("secret"))

    elif channel.type == "wecom_webhook":
        url = cfg.get("webhook_url", "")
        if not url:
            logger.warning(f"渠道 {channel.name} 企微 Webhook URL 为空")
            return False
        return await send_wecom_webhook(url, title, content)

    elif channel.type == "email":
        emails = cfg.get("email", [])
        if isinstance(emails, str):
            emails = [emails]
        if not emails:
            logger.warning(f"渠道 {channel.name} 邮箱列表为空")
            return False
        html_body = content.replace("\n", "<br>")
        ok_all = True
        for email in emails:
            if not send_email(email, title, html_body):
                ok_all = False
        return ok_all

    else:
        logger.warning(f"渠道 {channel.name} 不支持的类型: {channel.type}")
        return False


async def notify(rule, event: dict) -> bool:
    """根据规则配置的通知渠道分发通知

    优先使用 notify_channel_ids（新），降级到 notify_type + notify_config（旧）。

    Args:
        rule: AlertRule 对象
        event: {"workflow_name": str, "status": str, "time": str, "duration": int}
    """
    wf_name = event.get("workflow_name", "未知工作流")
    status = event.get("status", "FAILURE")
    run_time = event.get("time", "")
    duration = event.get("duration")

    title = f"⚠ 告警: {wf_name} {status}"
    content = (
        f"**工作流**: {wf_name}\n"
        f"**状态**: {status}\n"
        f"**时间**: {run_time}\n"
    )
    if duration is not None:
        content += f"**耗时**: {duration}s\n"
    content += f"**规则**: {rule.name}"

    # 1. 新逻辑 — notify_channel_ids
    channel_ids = getattr(rule, "notify_channel_ids", None)
    if not channel_ids and isinstance(rule.notify_config, dict):
        # 兼容 dict 中的 channel_ids（前端可能放在 notify_config 里）
        channel_ids = rule.notify_config.get("channel_ids")

    if channel_ids:
        channels = _load_channels(channel_ids)
        if not channels:
            logger.warning(f"规则 {rule.name} 未找到可用通知渠道: {channel_ids}")
            return False
        ok_count = 0
        for ch in channels:
            try:
                if await _send_via_channel(ch, title, content):
                    ok_count += 1
            except Exception as e:
                logger.error(f"渠道 {ch.name} 发送失败: {e}")
        return ok_count > 0

    # 2. 旧逻辑 — 降级兼容现有 notify_type + notify_config
    config = rule.notify_config or {}
    if isinstance(config, dict) and "channel_ids" in config:
        config = {k: v for k, v in config.items() if k != "channel_ids"}

    if rule.notify_type == "feishu_webhook":
        url = config.get("webhook_url", "")
        if not url:
            logger.warning(f"规则 {rule.name} 飞书 Webhook URL 为空")
            return False
        return await send_feishu_webhook(url, title, content)

    elif rule.notify_type == "dingtalk_webhook":
        url = config.get("webhook_url", "")
        if not url:
            logger.warning(f"规则 {rule.name} 钉钉 Webhook URL 为空")
            return False
        return await send_dingtalk_webhook(url, title, content, secret=config.get("secret"))

    elif rule.notify_type == "wecom_webhook":
        url = config.get("webhook_url", "")
        if not url:
            logger.warning(f"规则 {rule.name} 企微 Webhook URL 为空")
            return False
        return await send_wecom_webhook(url, title, content)

    elif rule.notify_type == "email":
        email = config.get("email", "")
        if not email:
            logger.warning(f"规则 {rule.name} 邮箱地址为空")
            return False
        html_body = content.replace("\n", "<br>")
        return send_email(email, title, html_body)

    logger.warning(f"规则 {rule.name} 无有效通知配置")
    return False


async def test_channel(channel_id: int) -> bool:
    """测试单个通知渠道是否可达"""
    try:
        from app.core.database import SessionLocal
        from app.models.sys_notify_channel import SysNotifyChannel
        db = SessionLocal()
        try:
            ch = db.query(SysNotifyChannel).filter(SysNotifyChannel.id == channel_id).first()
            if not ch:
                return False
            return await _send_via_channel(ch, "🔔 测试通知", "这是一条测试消息，通知渠道配置正确。")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"测试渠道失败: {e}")
        return False
