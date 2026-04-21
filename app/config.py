"""Configuration management for portfolio pipeline."""
import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    trading212_config_path: str = "./mcp/212-mcp/config/trading212_config.json"
    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "phi3:mini"
    output_path: str = "./conky/portfolio.txt"
    market_thesis: str = "Conservative long-term growth strategy."
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()