# app/domain/interfaces/parser.py
from typing import Protocol, Generic, TypeVar

T = TypeVar("T")

class Parser(Protocol, Generic[T]):
    def parse(self, html: str) -> T: ...