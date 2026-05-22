from pydantic import BaseModel


class PaginationSchema(BaseModel):
    page: int
    has_next: bool
