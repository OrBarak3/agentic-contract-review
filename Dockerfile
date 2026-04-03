FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY contract_review_langgraph/ ./contract_review_langgraph/
COPY api/ ./api/
COPY policies/ ./policies/

RUN pip install --no-cache-dir -e ".[api]"

RUN mkdir -p runtime/audit runtime/reports

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
