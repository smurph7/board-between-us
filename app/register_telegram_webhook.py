from app.config import get_settings
from app.services.telegram_service import register_telegram_webhook


def main() -> None:
    """Register the configured public Telegram webhook."""
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not configured")
    if not settings.telegram_webhook_secret:
        raise SystemExit("TELEGRAM_WEBHOOK_SECRET is not configured")
    if not settings.app_base_url.startswith("https://"):
        raise SystemExit("APP_BASE_URL must be a public HTTPS URL")

    registered = register_telegram_webhook(
        bot_token=settings.telegram_bot_token,
        app_base_url=settings.app_base_url,
        webhook_secret=settings.telegram_webhook_secret,
    )
    if not registered:
        raise SystemExit("Telegram webhook registration failed")
    print("Telegram webhook registered")


if __name__ == "__main__":
    main()
