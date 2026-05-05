from __future__ import annotations

import re
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()

CHINESE_PHONE_PATTERN = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
CHINESE_ID_PATTERN = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
BANK_CARD_PATTERN = re.compile(r"(?<!\d)\d{12,19}(?!\d)")
IP_PATTERN = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")


@dataclass
class RedactionConfig:
    mask_phone: bool = True
    mask_id: bool = True
    mask_email: bool = True
    mask_bank_card: bool = True
    mask_ip: bool = True
    mask_custom: bool = True


class PIIRedactor:
    def __init__(self, config: RedactionConfig | None = None):
        self.config = config or RedactionConfig()

    def redact(self, text: str) -> str:
        if not text:
            return text

        result = text

        if self.config.mask_id:
            result = CHINESE_ID_PATTERN.sub("[身份证号]", result)

        if self.config.mask_bank_card:
            result = BANK_CARD_PATTERN.sub("[银行卡号]", result)

        if self.config.mask_phone:
            result = CHINESE_PHONE_PATTERN.sub("[手机号]", result)

        if self.config.mask_email:
            result = EMAIL_PATTERN.sub("[邮箱]", result)

        if self.config.mask_ip:
            result = IP_PATTERN.sub("[IP地址]", result)

        return result

    def redact_dict(self, data: dict) -> dict:
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.redact(value)
            elif isinstance(value, dict):
                result[key] = self.redact_dict(value)
            elif isinstance(value, list):
                result[key] = [self.redact(v) if isinstance(v, str) else v for v in value]
            else:
                result[key] = value
        return result


_redactor: PIIRedactor | None = None


def get_redactor() -> PIIRedactor:
    global _redactor
    if _redactor is None:
        _redactor = PIIRedactor()
    return _redactor
