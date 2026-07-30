# Board Between Us

A shared visual chess notepad for two people playing an asynchronous game.

## Development

Create and activate a virtual environment, then install the project:

```bash
python -m pip install -e ".[dev]"
```

Run the tests:
```bash
python -m pytest
```
Run the application:
```bash
python -m app.main
```

## Telegram

Configure these environment variables to enable Telegram:

```text
APP_BASE_URL=https://your-public-app.example
TELEGRAM_BOT_TOKEN=...
TELEGRAM_BOT_USERNAME=...
TELEGRAM_WEBHOOK_SECRET=...
```

`APP_BASE_URL` must be the public HTTPS application URL. Generate a webhook
secret containing only letters, numbers, underscores, and hyphens, then register
the webhook after deployment:

```bash
python -m app.register_telegram_webhook
```
