"""
JSON schemas for structured stock analysis output.

These schemas are used to force the LLM to return consistent, parseable
results that the engine can act on programmatically.
"""

# Schema for analyzing a SINGLE stock chart
SINGLE_STOCK_SCHEMA = {
    "type": "object",
    "properties": {
        "symbol": {
            "type": "string",
            "description": "Stock ticker symbol"
        },
        "price": {
            "type": "number",
            "description": "Current price from the chart"
        },
        "trend": {
            "type": "string",
            "enum": ["bullish", "bearish", "neutral", "consolidating"],
            "description": "Overall trend direction"
        },
        "momentum": {
            "type": "string",
            "enum": ["strong", "moderate", "weak", "declining"],
            "description": "Momentum assessment"
        },
        "rsi": {
            "type": "number",
            "description": "RSI value if visible on chart, null otherwise"
        },
        "rsi_signal": {
            "type": "string",
            "enum": ["overbought", "bullish", "neutral", "bearish", "oversold", "unknown"],
            "description": "RSI-based signal"
        },
        "bollinger_position": {
            "type": "string",
            "enum": ["above_upper", "at_upper", "mid_upper", "middle", "mid_lower", "at_lower", "below_lower", "unknown"],
            "description": "Where price sits relative to Bollinger Bands"
        },
        "bb_overbought": {
            "type": "boolean",
            "description": "Whether Bollinger Bands indicate overbought condition"
        },
        "volume_assessment": {
            "type": "string",
            "enum": ["expanding", "stable", "declining", "spike", "unknown"],
            "description": "Volume trend observation"
        },
        "support_level": {
            "type": "number",
            "description": "Estimated support level (price), null if unsure"
        },
        "resistance_level": {
            "type": "number",
            "description": "Estimated resistance level (price), null if unsure"
        },
        "catalysts": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Visible catalysts (earnings dates, news, patterns)"
        },
        "risk_level": {
            "type": "string",
            "enum": ["low", "medium", "high", "very_high"],
            "description": "Overall risk assessment"
        },
        "notes": {
            "type": "string",
            "description": "Brief free-form observations"
        }
    },
    "required": ["symbol", "price", "trend", "momentum", "rsi_signal",
                 "bollinger_position", "bb_overbought", "risk_level", "notes"]
}

# Schema for ranking multiple stocks and allocating capital
MULTI_STOCK_SCHEMA = {
    "type": "object",
    "properties": {
        "ranking": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rank": {"type": "integer", "description": "1-based rank position"},
                    "symbol": {"type": "string"},
                    "confidence": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "very_high"],
                        "description": "Confidence in this ranking"
                    },
                    "reason": {"type": "string", "description": "Why this stock is ranked here"}
                },
                "required": ["rank", "symbol", "confidence", "reason"]
            },
            "description": "Ranked list of stocks from best to worst opportunity"
        },
        "allocation": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "percentage": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Percentage of total capital to allocate"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["buy", "hold", "reduce", "skip"],
                        "description": "Recommended action"
                    },
                    "notes": {"type": "string"}
                },
                "required": ["symbol", "percentage", "action", "notes"]
            },
            "description": "Capital allocation for each stock"
        },
        "total_allocated_pct": {
            "type": "number",
            "description": "Sum of all allocation percentages"
        },
        "cash_reserve_pct": {
            "type": "number",
            "description": "Remaining percentage as cash reserve"
        },
        "summary": {
            "type": "string",
            "description": "Overall market assessment and strategy rationale"
        }
    },
    "required": ["ranking", "allocation", "total_allocated_pct", "cash_reserve_pct", "summary"]
}

# Schema for position review (comparing current holdings vs analysis)
POSITION_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "positions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "current_action": {
                        "type": "string",
                        "enum": ["overweight", "correct", "underweight", "should_close"],
                        "description": "Whether current position size is appropriate"
                    },
                    "recommendation": {
                        "type": "string",
                        "enum": ["add", "hold", "reduce", "close"],
                        "description": "What action to take"
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "How urgent the action is"
                    },
                    "reason": {"type": "string"}
                },
                "required": ["symbol", "current_action", "recommendation", "urgency", "reason"]
            }
        },
        "summary": {"type": "string"}
    },
    "required": ["positions", "summary"]
}
