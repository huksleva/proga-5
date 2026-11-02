"""Сервер gRPC: реализация сервиса helloworld.Greeter."""
import logging
from concurrent import futures

import grpc
import helloworld_pb2
import helloworld_pb2_grpc


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        return helloworld_pb2.HelloReply(message=f"Hello, {request.name}!")

    def SayHelloAgain(self, request, context):
        return helloworld_pb2.HelloReply(message=f"Hello again, {request.name}!")

    def SayMyName(self, request, context):
        return helloworld_pb2.MyNameReply(
            message=f"— You're {request.name}.\n— You're goddamn right."
        )

    def SayGoodbye(self, request, context):
        return helloworld_pb2.GoodbyeReply(message=f"Goodbye, {request.name}!")


def serve(port: int = 50051) -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port(f"[::]:{port}")   # [::] — все сетевые интерфейсы
    server.start()                             # не блокирует
    print(f"Server started, listening on {port}", flush=True)
    server.wait_for_termination()              # блокирует до остановки процесса


if __name__ == "__main__":
    logging.basicConfig()
    serve()
