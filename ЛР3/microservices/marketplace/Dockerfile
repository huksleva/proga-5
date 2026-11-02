FROM python:3.12-slim

WORKDIR /service/marketplace

COPY marketplace/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY protos/ /service/protos/
COPY marketplace/ .
RUN python -m grpc_tools.protoc -I ../protos --python_out=. --pyi_out=. \
    --grpc_python_out=. ../protos/recommendations.proto

EXPOSE 8000
CMD ["uvicorn", "marketplace:app", "--host", "0.0.0.0", "--port", "8000"]
