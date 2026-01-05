from __future__ import annotations

import pytest

from halligan.runtime.errors import ParseError, ValidationError
from halligan.runtime.parser import parse_json_from_response
from halligan.runtime.schemas import validate_stage1


def test_parse_json_direct():
    data = parse_json_from_response('{"a": 1}')
    assert data == {"a": 1}


def test_parse_json_fenced():
    data = parse_json_from_response('```json\n{"a": 1}\n```')
    assert data == {"a": 1}


def test_parse_json_extracted():
    data = parse_json_from_response('prefix\n{"a": 1}\nsuffix')
    assert data == {"a": 1}


def test_parse_json_missing():
    with pytest.raises(ParseError):
        parse_json_from_response("no json here")


def test_validate_stage1_happy_path():
    payload = {
        "descriptions": ["d0", "d1"],
        "relations": [{"from": 0, "to": 1, "relationship": "r"}],
        "objective": "click then submit",
    }
    result = validate_stage1(payload, frames=2)
    assert result.objective
    assert result.descriptions == ["d0", "d1"]
    assert len(result.relations) == 1


def test_validate_stage1_length_mismatch():
    payload = {
        "descriptions": ["only one"],
        "relations": [],
        "objective": "x",
    }
    with pytest.raises(ValidationError):
        validate_stage1(payload, frames=2)
