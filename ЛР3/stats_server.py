"""Сервер gRPC с потоковыми методами."""
import time
from concurrent import futures

import grpc
import stats_pb2
import stats_pb2_grpc


class StatsServicer(stats_pb2_grpc.StatsServicer):
    def Countdown(self, request, context):
        if request.start < 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "start must be >= 0")
        for value in range(request.start, -1, -1):
            if not context.is_active():          # клиент отменил вызов
                print("Countdown: клиент отключился", flush=True)
                return
            yield stats_pb2.CountdownReply(value=value)
            time.sleep(0.2)

    def Sum(self, request_iterator, context):
        total, count = 0.0, 0
        for number in request_iterator:          # читаем поток до конца
            total += number.value
            count += 1
        return stats_pb2.SumReply(total=total, count=count)

    def RunningAverage(self, request_iterator, context):
        total = 0.0
        for count, number in enumerate(request_iterator, start=1):
            total += number.value
            yield stats_pb2.AverageReply(average=total / count, count=count)


def serve(port: int = 50053) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    stats_pb2_grpc.add_StatsServicer_to_server(StatsServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    return server


if __name__ == "__main__":
    serve().wait_for_termination()
