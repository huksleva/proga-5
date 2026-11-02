FROM python:3.12-slim

WORKDIR /service/recommendations

COPY recommendations/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY protos/ /service/protos/
COPY recommendations/ .
RUN python -m grpc_tools.protoc -I ../protos --python_out=. --pyi_out=. \
    --grpc_python_out=. ../protos/recommendations.proto

EXPOSE 50051
CMD ["python", "recommendations.py"]
