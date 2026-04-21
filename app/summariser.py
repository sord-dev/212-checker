"""Portfolio summarisation using Ollama LLM."""
import asyncio
import requests
from datetime import datetime
from typing import Dict, Any
import logging

from .config import settings

logger = logging.getLogger(__name__)


class PortfolioSummariser:
    """Handles portfolio data summarisation via Ollama."""
    
    def __init__(self):
        self.ollama_url = f"{settings.ollama_host}/api/generate"
        self.model = settings.ollama_model
    
    def build_prompt(self, portfolio_data: Dict[str, Any], market_status: str) -> str:
        """Build the prompt for Ollama based on portfolio data."""
        balance = portfolio_data["balance"]
        positions = portfolio_data["positions"]
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        
        # Extract balance information
        total_value = balance.get("totalValue", 0)
        available_cash = balance.get("availableToTrade", 0)
        unrealized_pnl = balance.get("unrealizedProfitLoss", 0)
        
        # Build positions summary
        positions_text = []
        if isinstance(positions, list):
            for position in positions[:10]:  # Limit to top 10 positions
                ticker = position.get("ticker", "Unknown")
                current_value = position.get("currentValue", 0)
                ppl = position.get("ppl", 0)
                positions_text.append(f"{ticker} | £{current_value:.2f} | p&l: £{ppl:.2f}")
        
        positions_summary = "\n".join(positions_text) if positions_text else "No positions found"
        
        system_prompt = f"""you are a portfolio monitor for a personal investor.
the investor's thesis is: {settings.market_thesis}
flag only what is genuinely worth paying attention to.
respond in 280 characters or less. no markdown. plain text only."""
        
        user_prompt = f"""market {market_status} summary — {timestamp}

balance:
total: £{total_value:.2f}
cash available: £{available_cash:.2f}
unrealised p&l: £{unrealized_pnl:.2f}

positions:
{positions_summary}

anything to flag?"""
        
        return system_prompt, user_prompt
    
    async def call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Call Ollama API to generate summary."""
        try:
            payload = {
                "model": self.model,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 300
                }
            }
            
            logger.info(f"Calling Ollama at {self.ollama_url}")
            
            # Use asyncio.to_thread for async HTTP call
            response = await asyncio.to_thread(
                requests.post,
                self.ollama_url,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            summary = result.get("response", "").strip()
            
            if not summary:
                raise ValueError("Empty response from Ollama")
            
            logger.info(f"Generated summary: {len(summary)} characters")
            return summary
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {str(e)}")
            raise Exception(f"LLM service unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"Ollama call failed: {str(e)}")
            raise
    
    async def generate_summary(self, portfolio_data: Dict[str, Any]) -> str:
        """Generate portfolio summary using LLM."""
        try:
            # Determine market status based on time (simplified)
            current_hour = datetime.utcnow().hour
            market_status = "open" if 8 <= current_hour <= 16 else "close"
            
            # Build prompts
            system_prompt, user_prompt = self.build_prompt(portfolio_data, market_status)
            
            # Call Ollama
            summary = await self.call_ollama(system_prompt, user_prompt)
            
            return summary
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            raise