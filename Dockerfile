FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN mkdir -p /app/data
ENV PORT=8000 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "server.py"]
