from enum import Enum
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field

class Operator(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NIN = "nin"
    LIKE = "like"
    ILIKE = "ilike"

class Criterion(BaseModel):
    """A single filtering rule."""
    field: str
    operator: Operator = Operator.EQ
    value: Any

class FilterCriteria(BaseModel):
    """Collection of criteria for querying data."""
    criteria: List[Criterion] = Field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    sort_by: Optional[str] = None
    descending: bool = False

    def where(self, field: str, operator: Operator, value: Any) -> "FilterCriteria":
        """Fluent API for adding criteria."""
        self.criteria.append(Criterion(field=field, operator=operator, value=value))
        return self

    @classmethod
    def eq(cls, field: str, value: Any) -> "FilterCriteria":
        """Helper for simple equality filter."""
        return cls(criteria=[Criterion(field=field, operator=Operator.EQ, value=value)])
