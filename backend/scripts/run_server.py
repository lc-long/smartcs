"""Run the SmartCS backend server."""

import uvicorn

from backend.app.core.config.settings import get_settings


def main():
    settings = get_settings()
    uvicorn.run(
        "backend.app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
