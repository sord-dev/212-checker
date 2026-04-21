FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# clone https://github.com/sord-dev/212-mcp.git into mcp directory
RUN git clone https://github.com/sord-dev/212-mcp.git mcp/212-mcp

# Create conky directory for output
RUN mkdir -p /app/conky

# Expose port
EXPOSE 8080

# Run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]