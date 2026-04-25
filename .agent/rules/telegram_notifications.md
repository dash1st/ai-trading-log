# User Preference: Trading Bot Notifications

## Rule: Stock Name Inclusion
- **Requirement**: ALWAYS include the stock name (Korean name) alongside the stock code in all Telegram notifications (Buy, Sell, Balance, Status).
- **Rationale**: The user does not recognize stocks by their 6-digit codes alone.
- **Implementation**: Use the `STOCK_NAMES` mapping from `quant_analyzer.py` to resolve names before sending messages.

## Rule: Avoid Code-Only Identification
- Never send messages that only contain the ticker code (e.g., "005930"). Always format as "삼성전자 (005930)".
