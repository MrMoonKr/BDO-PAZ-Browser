from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

import pytest

from _common.lookup_index import IndexKind
from tests.framework import (
    DeclaredCountTest,
    HandlerCase,
    HandlerResult,
    RangeTest,
    SchemaTest,
    TargetTest,
    case_id,
    header_count,
    run_case,
)

# Granbill grants card 304; Goyoung (47280) and a later copy (59998) both grant
# card 2043, so the name is shown once.
_KNOWLEDGE_CHARACTERS = {304: (43433,), 2043: (47280, 59998)}

CASE = HandlerCase(
    handler_name="mentalcard.dbss",
    data_file="mentalcard.dbss",
    companion_files={"mentalcardoffset.dbss": "mentalcardoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Knowledge Name", "Category Name"],
    internal_path="gamecommondata/binary/mentalcard.dbss",
    lookup_indexes={IndexKind.KNOWLEDGE_CHARACTERS: _KNOWLEDGE_CHARACTERS},
    tests=[
        SchemaTest(required_keys=["entry_id", "entry_name", "node_id", "node_name", "min_favor", "max_favor", "interest", "icon_path", "obtain", "learned_from", "position", "position_text"]),
        DeclaredCountTest(declared=header_count()),
        RangeTest(col="min_favor", min_val=0, max_val=math.inf),
        RangeTest(col="max_favor", min_val=0, max_val=math.inf),
        RangeTest(col="interest", min_val=0, max_val=math.inf),
        TargetTest(
            col="entry_id",
            value=15055,
            expected={
                "entry_name": "Altar of Blood - The 11th Illusion",
                "node_id": 24114,
                "node_name": "Altar of Blood",
                "icon_path": "ui_texture/ui_artwork/ic_09812.dds",
                "obtain": "Altar of Blood",
                # Not in the installed index.
                "learned_from": [],
                # All zero means no position.
                "position_text": "",
            },
        ),
        TargetTest(
            col="entry_id",
            value=304,
            expected={
                "entry_name": "Granbill",
                "node_id": 155,
                "node_name": "Elionism & the Delphe Knights",
                "icon_path": "ui_texture/ui_artwork/ic_00304.dds",
                "obtain": "Delphe Knights Quartermaster",
                "learned_from": ["Granbill"],
                "position_text": "-133004, 2729, -46023",
            },
        ),
        TargetTest(col="entry_id", value=2043, expected={"learned_from": ["Goyoung"]}),
        TargetTest(
            col="entry_id",
            value=3030,
            expected={
                "entry_name": "Iliya Island",
                "position_text": "159209, -7831, 292072",
            },
        ),
    ],
)


@pytest.fixture(scope="module")
def mentalcard_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_mentalcard_dbss(spec: Any, mentalcard_result: HandlerResult) -> None:
    mentalcard_result.check(spec)
