"""Клиент gRPC для сервиса helloworld.Greeter."""
import logging

import grpc
import helloworld_pb2
import helloworld_pb2_grpc


def run() -> None:
    print("Will try to greet world ...")
    # Канал — соединение с сервером; with закрывает его по завершении
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = helloworld_pb2_grpc.GreeterStub(channel)
        response = stub.SayHello(helloworld_pb2.HelloRequest(name="you"), timeout=5)
        print("Greeter client received:", response.message)
        response = stub.SayHelloAgain(helloworld_pb2.HelloRequest(name="you"), timeout=5)
        print("Greeter client received:", response.message)
        # Аргумент — сообщение ЗАПРОСА MyNameRequest с полем name
        response = stub.SayMyName(helloworld_pb2.MyNameRequest(name="Heisenberg"), timeout=5)
        print(response.message)
        response = stub.SayGoodbye(helloworld_pb2.GoodbyeRequest(name="you"), timeout=5)
        print("Greeter client received:", response.message)


if __name__ == "__main__":
    logging.basicConfig()
    run()
