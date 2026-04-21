"""Portfolio pipeline orchestration."""
import sys
import os
import tempfile
from datetime import datetime
from typing import Dict, Any
import logging

# Add MCP path for Trading212 client import
sys.path.insert(0, './mcp/212-mcp')

try:
    from app.clients.trading212 import Trading212API
except ImportError:
    # Fallback for different import paths
    from clients.trading212 import Trading212API

from .config import settings
from .summariser import PortfolioSummariser

logger = logging.getLogger(__name__)


class PortfolioPipeline:
    """Orchestrates the full portfolio monitoring pipeline."""
    
    def __init__(self):
        self.trading212_client = None
        self.summariser = PortfolioSummariser()
    
    def _get_trading212_client(self) -> Trading212API:
        """Get or create Trading212 client instance."""
        if self.trading212_client is None:
            self.trading212_client = Trading212API(
                config_path=settings.trading212_config_path
            )
        return self.trading212_client
    
    async def fetch_portfolio_data(self) -> Dict[str, Any]:
        """Fetch balance and positions from Trading212."""
        try:
            client = self._get_trading212_client()
            
            logger.info("Fetching balance from Trading212")
            balance = client.get_balance()
            
            logger.info("Fetching positions from Trading212")
            positions = client.get_positions()
            
            return {
                "balance": balance,
                "positions": positions,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch Trading212 data: {str(e)}")
            raise
    
    async def run(self) -> str:
        """Execute the full pipeline and return summary."""
        try:
            # Fetch portfolio data
            portfolio_data = await self.fetch_portfolio_data()
            
            # Generate summary via Ollama
            summary = await self.summariser.generate_summary(portfolio_data)
            
            # Write to output file
            await self.write_output(summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            raise
    
    async def write_output(self, summary: str):
        """Write summary to conky output file atomically."""
        try:
            output_path = settings.output_path
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Atomic write using temp file
            with tempfile.NamedTemporaryFile(
                mode='w', 
                dir=os.path.dirname(output_path),
                delete=False
            ) as temp_file:
                temp_file.write(summary)
                temp_path = temp_file.name
            
            # Atomic rename
            os.rename(temp_path, output_path)
            logger.info(f"Output written to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to write output: {str(e)}")
            # Clean up temp file if it exists
            try:
                os.unlink(temp_path)
            except:
                pass
            raise
    
    async def write_fallback_message(self, error_msg: str):
        """Write fallback error message to output file."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        fallback = f"portfolio update failed at {timestamp}\nerror: {error_msg[:100]}"
        
        try:
            await self.write_output(fallback)
        except Exception as e:
            logger.error(f"Failed to write fallback message: {str(e)}")