"""Часть 2. Как устроены байты (п. 2.1–2.3 практики) + упражнение 2."""
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

import encoding_demo_pb2 as ed
from evolution.v1 import user_pb2 as user_v1
from evolution.v2 import user_pb2 as user_v2
from library.v1 import library_pb2

WIRE_TYPES = {0: "VARINT", 1: "I64", 2: "LEN", 5: "I32"}


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def read_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Читает varint начиная с позиции pos. Возвращает (значение, новая позиция)."""
    result = shift = 0
    while True:
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift     # младшие 7 бит — полезные данные
        if not byte & 0x80:                   # старший бит 0 — последний байт числа
            return result, pos
        shift += 7


def dump_fields(data: bytes, indent: str = "") -> None:
    """Печатает поля сообщения без знания схемы."""
    pos = 0
    while pos < len(data):
        key, pos = read_varint(data, pos)
        field_number, wire_type = key >> 3, key & 0b111
        if wire_type == 0:
            value, pos = read_varint(data, pos)
        elif wire_type == 1:
            value, pos = data[pos:pos + 8], pos + 8
        elif wire_type == 2:
            length, pos = read_varint(data, pos)
            value, pos = data[pos:pos + length], pos + length
        elif wire_type == 5:
            value, pos = data[pos:pos + 4], pos + 4
        else:
            raise ValueError(f"Неподдерживаемый wire type {wire_type}")
        print(f"{indent}поле {field_number:>2}  {WIRE_TYPES[wire_type]:<6}  {value!r}")


section("2.1 Разбираем сообщение вручную")
from datetime import datetime, timezone

book = library_pb2.Book(id=1, title="Solaris", genre=library_pb2.GENRE_FICTION)
book.authors.add(name="Stanisław Lem", birth_year=1921)
book.attributes["language"] = "pl"
book.attributes["publisher"] = "MON"
book.published_at.FromDatetime(datetime(1961, 1, 1, tzinfo=timezone.utc))
book.isbn = "978-0-15-602760-1"

dump_fields(book.SerializeToString())
print("Вложенное сообщение автора:")
dump_fields(book.authors[0].SerializeToString(), indent="  ")

section("2.2 Varint, zigzag и упакованные списки")
examples = {
    "a = 150": ed.Demo(a=150),
    "b = 'testing'": ed.Demo(b="testing"),
    "negative = -1 (int32)": ed.Demo(negative=-1),
    "zigzag = -1 (sint32)": ed.Demo(zigzag=-1),
    "zigzag = 1 (sint32)": ed.Demo(zigzag=1),
    "nums = [1, 2, 300]": ed.Demo(nums=[1, 2, 300]),
    "a = 300 (упражнение 2)": ed.Demo(a=300),
}
for title, message in examples.items():
    raw = message.SerializeToString()
    print(f"{title:<24} {len(raw):>2} байт: {raw.hex(' ')}")

section("2.3 Эволюция схемы")
# Прямая совместимость: старый код читает данные нового
new_bytes = user_v2.User(id=1, name="Ann", email="ann@example.com").SerializeToString()
old_view = user_v1.User.FromString(new_bytes)
print("v1 читает данные v2:", repr(str(old_view)))
print("email старому коду неизвестен, но сохранён:", old_view.SerializeToString() == new_bytes)
print("После пересылки через старый код:", repr(str(user_v2.User.FromString(old_view.SerializeToString()))))

# Обратная совместимость: новый код читает данные старого
old_bytes = user_v1.User(id=2, name="Bob", nickname="bobby").SerializeToString()
new_view = user_v2.User.FromString(old_bytes)
print("v2 читает данные v1:", repr(str(new_view)), "email =", repr(new_view.email))

# Несовместимое изменение: тип поля 2 со string на int32
FieldProto = descriptor_pb2.FieldDescriptorProto
broken_file = descriptor_pb2.FileDescriptorProto(name="broken.proto", package="broken", syntax="proto3")
broken_message = broken_file.message_type.add(name="User")
broken_message.field.add(name="id", number=1, type=FieldProto.TYPE_INT64, label=FieldProto.LABEL_OPTIONAL)
broken_message.field.add(name="name", number=2, type=FieldProto.TYPE_INT32, label=FieldProto.LABEL_OPTIONAL)

pool = descriptor_pool.DescriptorPool()
pool.Add(broken_file)
BrokenUser = message_factory.GetMessageClass(pool.FindMessageTypeByName("broken.User"))

broken = BrokenUser.FromString(user_v1.User(id=3, name="Eve").SerializeToString())
print("Несовместимое изменение типа: id =", broken.id, "| name =", broken.name, "(ошибки нет, данные потеряны)")
