from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

import structlog

logger = structlog.get_logger()


class SentimentLevel(str, Enum):
    POSITIVE = "positive"      # 满意、友好
    NEUTRAL = "neutral"        # 正常
    SLIGHTLY_NEGATIVE = "slightly_negative"  # 略微不满
    NEGATIVE = "negative"      # 不满
    VERY_NEGATIVE = "very_negative"  # 非常不满、愤怒


@dataclass
class SentimentResult:
    level: SentimentLevel
    score: float  # -1.0 到 1.0
    keywords: list[str]
    should_escalate: bool
    escalation_reason: str | None = None


class SentimentAnalyzer:
    """情绪分析器 - 基于关键词和模式匹配"""

    # 情绪关键词
    POSITIVE_KEYWORDS = [
        "谢谢", "感谢", "好的", "明白", "清楚", "满意", "不错", "很好",
        "太好了", "辛苦了", "麻烦了", "感谢帮助",
        "thanks", "thank you", "good", "great", "excellent", "satisfied",
    ]

    NEGATIVE_KEYWORDS = [
        "不满", "投诉", "差评", "垃圾", "骗人", "坑", "坑人",
        "服务差", "态度差", "不专业", "效率低",
        "angry", "terrible", "bad", "poor", "horrible", "unacceptable",
        "disappointed", "frustrated", "annoyed", "upset",
    ]

    VERY_NEGATIVE_KEYWORDS = [
        "愤怒", "气死", "忍无可忍", "无法忍受", "太过分了",
        "我要投诉", "找你们领导", "曝光", "律师", "法院",
        "消协", "12315", "工商",
        "furious", "outraged", "unbelievable", "worst", "disgusting",
        "want to complain", "speak to manager", "sue", "lawyer",
    ]

    ESCALATION_KEYWORDS = [
        "转人工", "找人工", "人工客服", "真人", "经理", "主管",
        "领导", "上级", "投诉",
        "transfer to human", "human agent", "manager", "supervisor",
        "escalate", "complaint",
    ]

    # 重复问题模式
    REPEATED_QUESTION_PATTERNS = [
        r".*第.*次.*问.*",
        r".*说了.*遍.*",
        r".*怎么.*还不.*",
        r".*到底.*能不能.*",
        r".*什么时候.*才.*",
    ]

    def analyze(self, messages: list[str]) -> SentimentResult:
        """分析消息列表的情绪"""
        if not messages:
            return SentimentResult(
                level=SentimentLevel.NEUTRAL,
                score=0.0,
                keywords=[],
                should_escalate=False,
            )

        # 合并所有消息
        all_text = " ".join(messages)

        # 检测关键词
        found_positive = [kw for kw in self.POSITIVE_KEYWORDS if kw in all_text]
        found_negative = [kw for kw in self.NEGATIVE_KEYWORDS if kw in all_text]
        found_very_negative = [kw for kw in self.VERY_NEGATIVE_KEYWORDS if kw in all_text]
        found_escalation = [kw for kw in self.ESCALATION_KEYWORDS if kw in all_text]

        # 计算情绪分数
        score = 0.0
        score += len(found_positive) * 0.2
        score -= len(found_negative) * 0.3
        score -= len(found_very_negative) * 0.5

        # 限制在 -1.0 到 1.0
        score = max(-1.0, min(1.0, score))

        # 检测重复问题
        is_repeated = False
        for pattern in self.REPEATED_QUESTION_PATTERNS:
            if re.search(pattern, all_text):
                is_repeated = True
                break

        # 检测消息频率（短时间内多次发送相同内容）
        if len(messages) >= 3:
            last_three = messages[-3:]
            if len(set(last_three)) == 1:  # 三条消息完全相同
                is_repeated = True

        # 确定情绪级别
        if found_very_negative or (is_repeated and score < -0.3):
            level = SentimentLevel.VERY_NEGATIVE
        elif found_negative or (is_repeated and score < 0):
            level = SentimentLevel.NEGATIVE
        elif score < -0.2:
            level = SentimentLevel.SLIGHTLY_NEGATIVE
        elif score > 0.2:
            level = SentimentLevel.POSITIVE
        else:
            level = SentimentLevel.NEUTRAL

        # 判断是否需要升级
        should_escalate = False
        escalation_reason = None

        if found_escalation:
            should_escalate = True
            escalation_reason = "用户明确要求人工客服"
        elif level == SentimentLevel.VERY_NEGATIVE:
            should_escalate = True
            escalation_reason = "用户情绪非常不满，建议人工介入"
        elif level == SentimentLevel.NEGATIVE and is_repeated:
            should_escalate = True
            escalation_reason = "用户多次重复问题且情绪不满"

        all_keywords = found_positive + found_negative + found_very_negative + found_escalation

        logger.info(
            "sentiment_analyzed",
            level=level.value,
            score=score,
            should_escalate=should_escalate,
            keywords=all_keywords,
        )

        return SentimentResult(
            level=level,
            score=score,
            keywords=all_keywords,
            should_escalate=should_escalate,
            escalation_reason=escalation_reason,
        )


_analyzer: SentimentAnalyzer | None = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer
