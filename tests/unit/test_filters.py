import pytest
from src.core.filters import FilterCriteria, Operator, Criterion

def test_filter_criteria_fluent_api():
    criteria = FilterCriteria().where("age", Operator.GT, 21).where("status", Operator.EQ, "active")
    
    assert len(criteria.criteria) == 2
    assert criteria.criteria[0].field == "age"
    assert criteria.criteria[0].operator == Operator.GT
    assert criteria.criteria[0].value == 21
    assert criteria.criteria[1].field == "status"
    assert criteria.criteria[1].value == "active"

def test_filter_criteria_eq_helper():
    criteria = FilterCriteria.eq("email", "test@example.com")
    assert len(criteria.criteria) == 1
    assert criteria.criteria[0].operator == Operator.EQ
    assert criteria.criteria[0].value == "test@example.com"

def test_filter_criteria_serialization():
    criteria = FilterCriteria(limit=10, offset=0, sort_by="name", descending=True)
    criteria.where("category", Operator.IN, ["electronics", "books"])
    
    data = criteria.model_dump()
    assert data["limit"] == 10
    assert data["sort_by"] == "name"
    assert data["descending"] is True
    assert data["criteria"][0]["operator"] == "in"
