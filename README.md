# compass-stock-agent

Automated stock chart analysis via screenshots. Feed it a screenshot of your trading platform and get ranked allocations, technical analysis, and position reviews — powered by a local vision-capable LLM.

## Features

- **Single chart analysis** — Read ticker, price, trend, RSI, Bollinger Bands, volume, support/resistance, risk level
- **Multi-chart ranking** — Feed 2+ charts, get a ranked list with capital allocation
- **Position review** — Check if your current positions align with what the charts are saying
- **macOS screencapture** — One-shot capture with window delay for switching
- **Clipboard support** — Paste a screenshot from Cmd+Shift+4 and analyze it
- **Free-form text output** — No JSON parsing overhead, shows LLM reasoning trace

## Installation

```bash
# Install the generators framework (dependency)
pip install git+https://github.com/belarusian/generators.git

# Install this package
pip install git+https://github.com/belarusian/compass-stock-agent.git
```

## Usage

### CLI

```bash
# Analyze a single chart screenshot
stock chart.png

# Rank multiple charts and allocate $100K
stock chart1.png chart2.png chart3.png

# Capture screen and analyze (3s delay to switch windows)
stock --capture

# Analyze a screenshot from clipboard (Cmd+Shift+4, then Cmd+C)
stock --clipboard

# Position review — check if your holdings match the charts
stock --review positions.png

# Custom capital
stock --capital 250000 chart.png

# Suppress progress output
stock --quiet chart.png

# Custom LLM endpoint
stock --url http://your-llm/v1 --model gpt-4o chart.png
```

### Library

```python
from compass.stock_agent import StockAgent, config

agent = StockAgent()

# Single chart
result = await agent.analyze_screenshot("chart.png")

# Multi-chart ranking
result = await agent.analyze_multiple(["chart1.png", "chart2.png"])

# Full agent loop with capture
result = await agent.run(total_capital=100_000)

# Position review
result = await agent.review_positions("positions.png")
```

## LLM Support

Works with any OpenAI-compatible endpoint that supports vision (image + text input):

- **Local**: Your own qwen3 / LLaMA / GPT-oss instance
- **OpenAI**: `--url https://api.openai.com/v1 --model gpt-4o`
- **Anthropic**: Via compatible proxy
- **Google**: `--url https://generativelanguage.googleapis.com/v1beta/openai --model gemini-2.0-flash-exp`

Configuration via env vars:
```bash
STOCK_AGENT_LLM_URL=http://10.106.1.89:8080/v1
STOCK_AGENT_LLM_MODEL=gpt-oss
STOCK_AGENT_MAX_TOKENS=4096
STOCK_AGENT_TEMPERATURE=0.1
```

## Architecture

```
screencapture → resize/compress → base64 → LLM (vision) → free-form text
```

- Screenshots are resized to 1024px max to keep payloads small (~150KB JPEG)
- LLM reasoning trace is shown inline during analysis
- No JSON schema parsing — the LLM outputs natural language analysis
- Image compression uses JPEG quality 85 (visually identical for charts)

## License

MIT
