"""The Mem0 update bridge reads a reply exactly as the pinned Mem0 SDK does.

Mem0 1.0.11 parses its update reply with json.loads(remove_code_blocks(reply), strict=False)
(mem0/memory/main.py). Claude Haiku wraps JSON in a ```json fence; the bridge must accept
that, as Mem0 itself does, and still reject a reply that is not JSON once unwrapped.
"""

from copy import deepcopy
from datetime import datetime
from importlib import metadata
import json
import socket
import tempfile

import pytest

from tracemem.resolver import ModelReply, ResolverConfig, ResolverError
from tracemem.schema import Candidate, ScenarioMeta
from tracemem.systems import mem0_baseline
from tracemem.systems.mem0_baseline import Mem0Backend

ACTION = {"memory": [{"id": "0", "text": "BERT is confirmed", "event": "ADD"}]}


class Client:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(deepcopy(kwargs["messages"]))
        return self.replies.pop(0)


@pytest.fixture(autouse=True)
def no_network(monkeypatch, tmp_path):
    def blocked(*args, **kwargs):
        raise AssertionError("Mem0 offline tests must not open network connections")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))


@pytest.fixture
def backend_with():
    try:
        version = metadata.version("mem0ai")
    except metadata.PackageNotFoundError:
        pytest.skip("optional mem0ai SDK not installed")
    if version != mem0_baseline.MEM0_VERSION:
        pytest.skip("offline native SDK tests require the pinned Mem0 version")
    opened = []

    def create(*contents):
        client = Client(*(ModelReply(content, input_tokens=5, output_tokens=2) for content in contents))
        config = ResolverConfig(model="offline-shared-model", timeout_seconds=12.0, max_attempts=2,
                                max_completion_tokens=678)
        backend = Mem0Backend(ScenarioMeta(scenario_id="fixture", project_id="synthetic-project"), config, client)
        opened.append(backend)
        return backend, client
    yield create
    for backend in opened:
        backend.close()


def add(backend):
    backend.add(Candidate(candidate_id="model.main@S1-T1", project_id="synthetic-project", item="model.main",
                          value="BERT", source_turn_ids=["S1-T1"], speaker="Speaker", text="We confirm BERT."),
                datetime(2026, 1, 5, 10, 1))


# Haiku's reply as saved on 26 Oct (spacing kept), and two other fences remove_code_blocks accepts.
FENCED = [
    '```json\n{\n    "memory" : [\n        {\n            "id" : "0",\n            "text" : "BERT is confirmed",\n'
    '            "event" : "ADD"\n        }\n    ]\n}\n```',
    "```\n" + json.dumps(ACTION) + "\n```",
    "  ```JSON\n" + json.dumps(ACTION) + "\n```  ",
]


@pytest.mark.parametrize("content", FENCED)
def test_a_fenced_reply_is_applied_on_the_first_attempt(backend_with, content):
    backend, client = backend_with(content)
    add(backend)
    assert [event["status"] for event in backend.events()] == ["applied"]
    assert len(client.calls) == 1
    assert len(backend._store.data) == 1
    assert all("BERT is confirmed" in record.value for record in backend.records())


@pytest.mark.parametrize("content", FENCED + [json.dumps(ACTION)])
def test_the_bridge_reads_a_reply_as_the_sdk_does(content):
    from mem0.memory.utils import remove_code_blocks
    native = json.loads(remove_code_blocks(content), strict=False)
    assert mem0_baseline._parse_update_reply(content) == native


@pytest.mark.parametrize("content", ["```json\nnot json\n```", "Here is the update: " + json.dumps(ACTION)])
def test_a_reply_that_is_not_json_once_unwrapped_still_fails(backend_with, content):
    backend, client = backend_with(content, content)
    with pytest.raises(ResolverError, match="update response must be JSON"):
        add(backend)
    assert len(client.calls) == 2
    assert backend._store.data == {}
