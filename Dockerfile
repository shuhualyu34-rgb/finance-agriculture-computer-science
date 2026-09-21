# 基础镜像可覆盖:网络受限时可用镜像源,如
# docker-compose build --build-arg BASE_IMAGE=docker.1ms.run/library/python:3.12-slim
ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY bigscreen/ bigscreen/

EXPOSE 8010

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8010"]
