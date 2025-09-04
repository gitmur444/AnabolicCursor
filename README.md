# AnabolicCursor - OpenAI API Proxy

Прокси-сервер для Cursor IDE, совместимый с OpenAI API. Перехватывает и логирует все запросы между Cursor и OpenAI для анализа и отладки.

## Быстрый старт

### 1. Установка и запуск

```bash
cd AnabolicCursor

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Запустить прокси
uvicorn app:app --host 0.0.0.0 --port 8787 --reload
```

### 2. Настройка Cursor

В Cursor IDE:
1. Откройте **Settings** → **Models** → **Advanced**
2. **Override OpenAI Base URL**: `http://localhost:8787`
3. **Model**: выберите или введите кастомную модель (например, `my-agent`)

### 3. Конфигурация (опционально)

```bash
# Алиасы моделей
export MODEL_ALIASES="my-agent=gpt-5,custom-gpt=gpt-4"

# API ключ (если не передается через Cursor)
export OPENAI_API_KEY=sk-...
```

## Просмотр логов

### Основной способ
Все логи сохраняются в файл:
```bash
tail -f logs/proxy.log | jq .
```

### Мониторинг (BETA)
Дополнительно доступен стек Grafana + Loki:

```bash
# Запустить мониторинг
docker-compose up -d

# Открыть Grafana
open http://localhost:3000
# Логин: admin / admin
```

В Grafana добавьте Loki data source: `http://loki:3100`

Примеры запросов:
```
{job="proxy"} | json | event="incoming_request"
{job="proxy"} | json | event="response" 
{job="proxy"} | json | model="gpt-5"
```

## Структура логов

Каждое событие логируется в JSON формате:

```json
{
  "event": "incoming_request",
  "timestamp": 1756971574,
  "data": {
    "model": "gpt-5",
    "message_count": 3,
    "has_tool_results": false,
    "stream": true,
    "tools_available": true,
    "full_payload": { ... }
  }
}
```

### События:
- `incoming_request` - запрос от Cursor
- `forwarded_request` - запрос к OpenAI  
- `response` - ответ от OpenAI
- `retry_scheduled` - повторные попытки при rate limits
- `error` - ошибки

## Возможности

- ✅ **Полное логирование** всех запросов/ответов
- ✅ **Поддержка streaming** (Server-Sent Events)
- ✅ **Автоматические retry** при rate limits (429)
- ✅ **Анализ tool calls** от модели
- ✅ **Безопасность** - маскировка API ключей в логах
- ✅ **Алиасы моделей** для удобства
- ✅ **JSON форматирование** с отступами

## Требования

- Python 3.10+
- Cursor IDE
- OpenAI API ключ

## Документация

Подробное описание архитектуры и модулей: [STRUCTURE.md](STRUCTURE.md)