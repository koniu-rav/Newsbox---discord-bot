# Newsbox Discord Bot - Agent Guidelines & Rules

## Project Overview
Newsbox is an automated Discord bot delivering daily macro briefings, economic calendar insights, and AI-powered market sentiment (DXY, EUR/USD, DAX, BTC) at 8:00 AM.
Built with Python (asyncio), Discord.py, and Google Gemini API (`google-genai` / `google-generativeai`).

## Architectural Principles
1. **Separation of Concerns**:
   - `cogs/`: Handles Discord UI, commands, and interaction listeners. No business logic or external network calls directly in cogs.
   - `services/`: Encapsulates all third-party integrations (Gemini API, financial/macro market data, economic calendar, news scraping) and business logic.
   - `utils/`: Reusable formatting, embed builders, and structured logging.
   - `config.py`: Centralized strongly-typed settings (via `pydantic-settings` or dataclasses).
2. **Asynchronous & Non-blocking**:
   - All I/O operations must be `async` (using `aiohttp` or async client libraries).
   - Use `asyncio.to_thread` only for unavoidable synchronous libraries.
3. **Robust Error Handling & Resilience**:
   - External APIs (Gemini, Market data, News feeds) must have retry logic with graceful degradation so Discord commands and scheduled briefings do not crash.
4. **Token Optimization**:
   - Keep prompt payloads sent to Gemini concise and structured.
   - Limit raw data injection by pre-filtering/normalizing news articles and market ticks before passing them to the LLM.

