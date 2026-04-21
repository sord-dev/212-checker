# Portfolio Pipeline

Self-hosted FastAPI service that pulls Trading212 portfolio data, summarizes it via Ollama LLM, and outputs to conky desktop display.

## Setup

1. **Configure Trading212 credentials**:
   ```bash
   # Edit the config file with your API credentials
   vim mcp/212-mcp/config/trading212_config.json
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your market thesis and any custom paths
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

4. **Pull Ollama model**:
   ```bash
   docker-compose exec ollama ollama pull phi3:mini
   ```

## Usage

### Manual trigger
```bash
curl -X POST http://localhost:8080/summary
```

### Health check
```bash
curl http://localhost:8080/health
```

### Cron setup (on host machine)
```bash
# Add to crontab -e
# Market open (8:00 AM London time, Mon-Fri)
0 8 * * 1-5 curl -X POST http://picxibox:8080/summary

# Market close (4:30 PM London time, Mon-Fri) 
30 16 * * 1-5 curl -X POST http://picxibox:8080/summary
```

## Conky Integration

Output file: `./conky/portfolio.txt`

Example conky config (`~/.config/conky/portfolio.conf`):
```lua
conky.config = {
    alignment = 'top_right',
    gap_x = 20,
    gap_y = 20,
    update_interval = 60,
}

conky.text = [[
${font}${color}portfolio
${hr}
${execp cat /home/picxi/Desktop/projects/picxibox/212checker/conky/portfolio.txt}
]]
```

Run alongside existing conky:
```bash
conky -c ~/.config/conky/portfolio.conf &
```

## Architecture

- **FastAPI service** (port 8080): `/summary` and `/health` endpoints
- **Ollama LLM** (port 11434): `phi3:mini` model for summarization
- **Trading212 client**: Imported from `mcp/212-mcp` git submodule
- **Output**: Atomic file writes to `conky/portfolio.txt`

## Error handling

- API failures write fallback messages instead of leaving stale data
- Service dependencies managed via docker-compose
- Structured logging to stdout for container environments

## Development

```bash
# Local development
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# View logs
docker-compose logs -f pipeline
docker-compose logs -f ollama
```