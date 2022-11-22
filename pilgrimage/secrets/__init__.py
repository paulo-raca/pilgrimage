import json
import logging
import os
import pkgutil
from typing import Any

logger = logging.getLogger(__name__)


def get_secret(secret: str) -> Any:
    secret_path = f"{secret}/{secret}.json"
    try:
        data = pkgutil.get_data(__package__, secret_path)
    except Exception:
        data = None

    if data is not None:
        logger.debug(f"Using {secret} credentials JSON from package")
        return json.loads(data)

    abspath = os.path.abspath(f"secrets/{secret_path}")
    if os.path.isfile(abspath):
        with open(abspath, "r") as f:
            logger.debug(f"Using {secret} credentials JSON from filesystem")
            return json.loads(f.read())

    logger.error(f"Couldn't find {secret} credentials")
    return None
