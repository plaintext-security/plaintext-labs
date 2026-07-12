"""Config & secrets via pydantic-settings — never hardcoded, never in the code.

Loads from the environment (and a .env if present). Module 04 uses these keys to
talk to threat-intel APIs; here we just prove secrets come from the boundary too.
"""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SIFT_", env_file=".env", extra="ignore")

    vt_api_key: str = Field(default="", description="VirusTotal API key (from SIFT_VT_API_KEY)")
    log_level: str = Field(default="INFO")
