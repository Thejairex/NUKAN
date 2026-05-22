from dataclasses import dataclass


@dataclass(frozen=True)
class Pagination:
    page: int
    has_next: bool
