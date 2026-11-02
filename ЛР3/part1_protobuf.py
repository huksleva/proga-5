"""Часть 1. Protocol Buffers без gRPC (п. 1.3–1.7 практики)."""
import json
import timeit
from datetime import datetime, timezone

from google.protobuf import json_format
from google.protobuf.timestamp_pb2 import Timestamp

from library.v1 import library_pb2


def section(title: str) -> None:
    print(f"\n=== {title} ===")


section("1.3 Создаём сообщение")
book = library_pb2.Book(id=1, title="Solaris", genre=library_pb2.GENRE_FICTION)
book.authors.add(name="Stanisław Lem", birth_year=1921)
book.attributes["language"] = "pl"
book.attributes["publisher"] = "MON"
book.published_at.FromDatetime(datetime(1961, 1, 1, tzinfo=timezone.utc))
book.isbn = "978-0-15-602760-1"
print(book)

section("1.4 Сериализация и разбор")
data = book.SerializeToString()
print(type(data).__name__, len(data), "байт")
print(data.hex(" "))
restored = library_pb2.Book.FromString(data)
print("Объекты равны:", restored == book)
print("Заголовок после разбора:", restored.title)

section("1.5 Сравнение с JSON")
as_json = json_format.MessageToJson(book, indent=None)
print(as_json)
print()
print("JSON:    ", len(as_json.encode()), "байт")
print("protobuf:", len(data), "байт")
print(json_format.MessageToDict(book, preserving_proto_field_name=True)["published_at"])

catalog = library_pb2.Catalog()
for i in range(1, 1001):
    item = catalog.books.add(id=i, title=f"Book #{i}", genre=library_pb2.GENRE_SCIENCE)
    item.authors.add(name=f"Author {i % 50}", birth_year=1900 + i % 100)
    item.attributes["language"] = "en"

proto_bytes = catalog.SerializeToString()
catalog_dict = json_format.MessageToDict(catalog, preserving_proto_field_name=True)
json_bytes = json.dumps(catalog_dict).encode()

print(f"\nКаталог из 1000 книг:")
print(f"protobuf: {len(proto_bytes):>7} байт")
print(f"JSON:     {len(json_bytes):>7} байт  (в {len(json_bytes) / len(proto_bytes):.1f} раза больше)")

n = 200
t_proto_dump = timeit.timeit(catalog.SerializeToString, number=n) / n * 1000
t_json_dump = timeit.timeit(lambda: json.dumps(catalog_dict), number=n) / n * 1000
t_proto_load = timeit.timeit(lambda: library_pb2.Catalog.FromString(proto_bytes), number=n) / n * 1000
t_json_load = timeit.timeit(lambda: json.loads(json_bytes), number=n) / n * 1000
print(f"Сериализация: protobuf {t_proto_dump:.3f} мс, json {t_json_dump:.3f} мс")
print(f"Разбор:       protobuf {t_proto_load:.3f} мс, json {t_json_load:.3f} мс")

section("1.6 Значения по умолчанию и наличие поля")
empty = library_pb2.Book()
print(repr(empty.title), empty.id, empty.genre, list(empty.authors), dict(empty.attributes))
print("Пустое сообщение занимает", len(empty.SerializeToString()), "байт")
print("published_at задано?", empty.HasField("published_at"))

author = library_pb2.Author(name="Lem")
print("birth_year задано?", author.HasField("birth_year"))
author.birth_year = 0
print("birth_year задано после присваивания 0?", author.HasField("birth_year"))

try:
    empty.HasField("title")
except ValueError as error:
    print("ValueError:", error)

section("1.7 oneof и проверка типов")
b = library_pb2.Book(title="Solaris", isbn="978-0-15-602760-1")
print("Задано:", b.WhichOneof("source"))
b.ebook_url = "https://example.com/solaris.epub"
print("Задано:", b.WhichOneof("source"), "| isbn теперь:", repr(b.isbn))

for value in ("1", 2**70, 1.5):
    try:
        b.id = value
    except (TypeError, ValueError) as error:
        print(f"{value!r:>25} → {type(error).__name__}: {error}")

try:
    b.published_at = Timestamp()
except (AttributeError, TypeError) as error:   # старые версии protobuf — AttributeError, новые — TypeError
    print(f"{type(error).__name__}:", error)
b.published_at.CopyFrom(Timestamp(seconds=0))   # так правильно
print(b.published_at.ToDatetime())
