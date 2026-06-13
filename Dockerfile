FROM python:3.12-slim

WORKDIR /app

RUN groupadd -r chatbot && useradd -r -g chatbot chatbot && \
    mkdir -p /app/database /app/datos && \
    chown -R chatbot:chatbot /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

COPY --chown=chatbot:chatbot . .

EXPOSE 5000

USER chatbot

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:$PORT/salud')" || exit 1

CMD gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -
