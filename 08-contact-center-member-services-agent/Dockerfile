# Agent 08 — container image honoring the AgentCore Runtime contract (ARM64, /invocations + /ping).
FROM --platform=linux/arm64 python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 EXTRACT_MODE=demo PYTHONPATH=/app:/app/platform_core

COPY platform_core /app/platform_core
COPY governance /app/governance
COPY 08-contact-center-member-services-agent /app/08-contact-center-member-services-agent

RUN pip install --no-cache-dir -e /app/platform_core \
 && pip install --no-cache-dir langgraph>=0.2 streamlit>=1.36

EXPOSE 8080 8501
CMD ["python", "/app/08-contact-center-member-services-agent/agent/serve.py"]
