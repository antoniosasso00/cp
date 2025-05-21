from fastapi.responses import ORJSONResponse
from fastapi.middleware.gzip import GZipMiddleware
import orjson
import logging
from typing import Any

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configurazione ORJSON
class CustomORJSONResponse(ORJSONResponse):
    def render(self, content: Any) -> bytes:
        return orjson.dumps(
            content,
            option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_NON_STR_KEYS
        )

# Configurazione middleware
MIDDLEWARE_CONFIG = {
    "gzip": {
        "minimum_size": 1000,  # Comprimi risposte > 1KB
    }
}

# Configurazione database
DB_CONFIG = {
    "pool_size": 20,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 1800,  # Ricicla connessioni ogni 30 minuti
}

# Configurazione cache
CACHE_CONFIG = {
    "ttl": 300,  # 5 minuti
    "max_size": 1000,  # Massimo 1000 elementi in cache
} 