# Agent 01 — container image honoring the AgentCore Runtime contract
# (ARM64, HTTP /invocations + /ping). Also runs the Streamlit demo.
FROM --platform=linux/arm64 python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 EXTRACT_MODE=demo PYTHONPATH=/app:/app/platform_core

COPY platform_core /app/platform_core
COPY governance /app/governance
COPY 01-revenue-cycle-denial-agent /app/01-revenue-cycle-denial-agent

RUN pip install --no-cache-dir -e /app/platform_core \
 && pip install --no-cache-dir langgraph>=0.2 streamlit>=1.36

EXPOSE 8080 8501
# Runtime contract entrypoint (serve.py provides /invocations + /ping):
CMD ["python", "/app/01-revenue-cycle-denial-agent/agent/serve.py"]
