from dataclasses import dataclass
from typing import Optional

@dataclass
class RedisParams:
    host: str
    port: int
    username: Optional[str]
    password: str
    db: int
