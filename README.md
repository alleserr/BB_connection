# BB Connection

Локальная аналитическая система для Bybit Spot:

- загружает OHLCV свечи с Bybit;
- валидирует данные;
- считает индикаторы и производные признаки локально в Python;
- собирает стабильный snapshot JSON;
- отдаёт результат через MCP HTTP server для ChatGPT.

Ключевой принцип проекта: **Python считает, ChatGPT интерпретирует**.

## Что входит в MVP

- рынок: `spot`
- таймфреймы: `5m`, `15m`, `1h`, `4h`
- индикаторы:
  - `EMA 20`
  - `EMA 50`
  - `EMA 200`
  - `RSI 14`
  - `ATR 14`
  - `relative_volume`
  - `session VWAP` со сбросом в `00:00 UTC`
  - `distance_to_vwap_pct`
- MCP tools:
  - `analyze_symbol`
  - `compare_symbols`
  - `scan_watchlist`
  - `get_raw_snapshot`

## Архитектура

Слои реализации:

1. `BybitClient` получает свечи из `GET /v5/market/kline`.
2. `ValidationService` проверяет OHLCV перед любыми расчётами.
3. `IndicatorService` считает индикаторы на `pandas/numpy`.
4. `FeatureService` строит булевы признаки, состояния и flags.
5. `SnapshotService` собирает типизированный JSON snapshot.
6. `ToolHandlers` и `FastMCP` публикуют это через Streamable HTTP transport.

Бизнес-логика не смешана с MCP transport: весь analytics pipeline можно тестировать без запуска сервера.

## Структура проекта

```text
app/
  config.py
  logging_setup.py
  main.py
  exceptions.py
  models/
  services/
  utils/
  mcp/
tests/
.env.example
requirements.txt
README.md
```

## Установка

Требования:

- Python `3.11+`
- `pip`
- `cloudflared` для публичного подключения ChatGPT к локальному MCP

Пример локальной установки:

```bash
/opt/homebrew/bin/python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Конфигурация

Создайте `.env` на основе `.env.example`.

Поддерживаемые переменные:

- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`
- `BYBIT_BASE_URL`
- `DEFAULT_BARS_LIMIT`
- `MAX_BARS_LIMIT`
- `LOG_LEVEL`
- `USE_TESTNET`
- `MCP_HOST`
- `MCP_PORT`
- `MCP_PUBLIC_BASE_URL`
- `CLOUDFLARE_TUNNEL_ENABLED`

Для MVP публичные market endpoints могут работать без API key, но поля под ключи уже предусмотрены на будущее.

## Быстрый локальный запуск

Локальный разовый анализ:

```bash
.venv/bin/python -m app.main analyze --symbol BTCUSDT --timeframe 1h
```

Запуск MCP HTTP server:

```bash
.venv/bin/python -m app.main serve-mcp --host 127.0.0.1 --port 8000
```

Проверка health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

MCP transport публикуется по пути:

```text
http://127.0.0.1:8000/mcp
```

## Формат ответа tool'ов

Успех:

```json
{
  "status": "ok",
  "data": {
    "symbol": "BTCUSDT",
    "timeframe": "1h"
  }
}
```

Ошибка:

```json
{
  "status": "error",
  "error": {
    "code": "INSUFFICIENT_DATA",
    "message": "Not enough candles to compute the required indicators",
    "details": {}
  }
}
```

## MCP Tools

### `analyze_symbol`

Вход:

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "bars_limit": 300
}
```

### `compare_symbols`

Вход:

```json
{
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
  "timeframe": "15m",
  "bars_limit": 300
}
```

### `scan_watchlist`

Вход:

```json
{
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
  "timeframe": "1h",
  "scan_mode": "balanced",
  "bars_limit": 300
}
```

Особенности:

- в MVP поддерживается только `scan_mode="balanced"`
- любой другой режим вернёт ошибку `unsupported_scan_mode`
- scoring rule-based и объяснимый

Баланс скоринга строится на:

- направлении тренда
- силе тренда
- состоянии RSI
- relative volume
- позиции цены относительно VWAP
- setup flags
- risk flags

### `get_raw_snapshot`

Вход:

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h"
}
```

## Cloudflare Tunnel

Базовый MVP-сценарий:

1. Поднять MCP локально на `localhost`.
2. Опубликовать его через `cloudflared`.
3. Подключить публичный URL в ChatGPT как MCP endpoint.

Пример:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Если `cloudflared` выдал публичный адрес вида:

```text
https://example-subdomain.trycloudflare.com
```

то MCP endpoint для подключения будет:

```text
https://example-subdomain.trycloudflare.com/mcp
```

## Railway Deploy

Для постоянного удалённого endpoint проект можно деплоить на Railway напрямую из GitHub.

В репозитории уже добавлен `railway.toml`, поэтому Railway получает:

- явный `startCommand`
- `healthcheckPath=/health`
- restart policy
- запуск на `0.0.0.0:$PORT`

Что нужно задать в Railway Variables:

- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`
- `BYBIT_BASE_URL`
- `DEFAULT_BARS_LIMIT`
- `MAX_BARS_LIMIT`
- `LOG_LEVEL`
- `USE_TESTNET`
- `MCP_HOST=0.0.0.0`
- `MCP_PORT=${{PORT}}` или просто не задавать `MCP_PORT`, если Railway передаёт порт только через start command
- `MCP_PUBLIC_BASE_URL=https://<your-service-domain>`

После успешного deploy MCP endpoint будет:

```text
https://<your-service-domain>/mcp
```

Если Railway не определяет старт автоматически, это уже закрыто через `railway.toml`.

## Тесты

Запуск тестов:

```bash
.venv/bin/pytest
```

Что покрыто:

- нормализация ответа Bybit
- валидация OHLCV
- расчёт EMA / RSI / ATR
- производные признаки и flags
- сборка snapshot
- MCP tool handlers
- end-to-end pipeline с мокнутым Bybit client
- правило "нет валидных данных — нет аналитики"

## Известные ограничения

- MVP работает только с `spot`
- не выполняет автоторговлю и не отправляет ордера
- `scan_mode` пока только `balanced`
- `scan_watchlist` использует прозрачный rule-based scoring, а не сложную модель
- live-запросы к Bybit зависят от доступности API для вашего IP/региона

## Важное про Bybit API и 403

Bybit официально указывает, что некоторые IP/регионы могут получать `403 Forbidden`, а для части стран нужно использовать отдельные mainnet hostnames. См. официальные материалы:

- [Bybit Integration Guidance](https://bybit-exchange.github.io/docs/v5/guide)
- [Bybit Get Kline](https://bybit-exchange.github.io/docs/v5/market/kline)
- [Bybit Rate Limit Rules](https://bybit-exchange.github.io/docs/v5/rate-limit)
- [Bybit Error Codes](https://bybit-exchange.github.io/docs/v5/error)

Практически это означает:

- если `https://api.bybit.com` недоступен из вашего региона, задайте корректный `BYBIT_BASE_URL`
- для некоторых регионов Bybit сам указывает отдельные hostnames, например `api.bybit.kz`, `api.bybit.tr`, `api.bybit.nl`
- если API отвечает `403`, ядро вернёт структурированную ошибку `BYBIT_ACCESS_FORBIDDEN`, а не выдуманный snapshot

## Текущее состояние проекта

На текущем этапе реализованы:

- рабочий Python analytics core
- MCP HTTP server на FastMCP / Streamable HTTP
- типизированные модели запросов и snapshot-ответов
- тестовый контур
- README и `.env.example`

Локальная проверка в этой среде:

- `pytest` проходит полностью
- MCP server успешно стартует и отвечает на `/health`
- живой запрос к Bybit из текущей среды упирается в внешний `403` по IP/региону, поэтому для реального market data нужен доступный Bybit endpoint с разрешённого IP
