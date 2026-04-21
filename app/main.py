"""FastAPI application for portfolio pipeline."""
from fastapi import FastAPI, HTTPException
from datetime import datetime
import logging
from .pipeline import PortfolioPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Portfolio Pipeline",
    description="Self-hosted pipeline for Trading212 portfolio monitoring",
    version="1.0.0"
)

pipeline = PortfolioPipeline()


@app.get("/health")
async def health_check():
    """Health check endpoint for uptime monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "portfolio-pipeline"
    }


@app.post("/summary")
async def generate_summary():
    """
    Trigger full portfolio pipeline:
    1. Fetch balance and positions from Trading212
    2. Generate summary via Ollama LLM
    3. Write output to conky file
    
    Returns the generated summary string.
    """
    try:
        logger.info("Portfolio summary requested")
        summary = await pipeline.run()
        logger.info("Portfolio summary generated successfully")
        return {
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        # Write fallback message to output file
        await pipeline.write_fallback_message(f"Pipeline error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Pipeline failed: {str(e)}"
        )