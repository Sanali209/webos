import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from tools.loginspector.parser import LogParser, LOG_PATTERN

def test_clean_ansi():
    parser = LogParser()
    raw = "\x1b[32m2026-02-22 08:35:12\x1b[0m | \x1b[1mINFO\x1b[0m | message"
    clean = parser.clean_ansi(raw)
    assert clean == "2026-02-22 08:35:12 | INFO | message"

def test_parse_valid_line():
    parser = LogParser()
    line = "2026-02-22 08:35:12.123 | INFO     | src.main:start:42 | {'user_id': 5} | Server started cleanly"
    entry = parser.parse_line(line, "test.log")
    
    assert entry is not None
    assert entry.time == "2026-02-22 08:35:12.123"
    assert "INFO" in entry.level
    assert entry.context == "src.main:start:42"
    assert entry.extra == "{'user_id': 5}"
    assert entry.message == "Server started cleanly"
    assert entry.source_file == "test.log"

def test_parse_invalid_line():
    parser = LogParser()
    line = "This is just a random traceback line without standard format"
    entry = parser.parse_line(line, "test.log")
    assert entry is None

def test_session_splitting():
    parser = LogParser()
    assert parser.current_session_id == 0
    
    # Normal line
    parser.parse_line("2026-02-22 08:35:12 | INFO | ctx | ext | normal line", "t.log")
    assert parser.current_session_id == 0
    
    # Session marker
    parser.parse_line("2026-02-22 08:36:00 | INFO | ctx | ext | 🚀 Starting WebOS Server...", "t.log")
    assert parser.current_session_id == 1

def test_parse_taskiq_line():
    parser = LogParser()
    line = "[2026-02-22 08:57:00,299][taskiq.worker][INFO   ][MainProcess] Pid of a main process: 26968"
    entry = parser.parse_line(line, "t.log")
    assert entry is not None
    assert entry.time == "2026-02-22 08:57:00.299"
    assert entry.level == "INFO"
    assert entry.context == "taskiq.worker"
    assert entry.message == "[MainProcess] Pid of a main process: 26968"

def test_parse_uvicorn_line():
    parser = LogParser()
    line = "INFO:     Will watch for changes in these directories: ['D:\\github\\webos']"
    entry = parser.parse_line(line, "t.log")
    assert entry is not None
    assert entry.level == "INFO"
    assert entry.context == "uvicorn"
    assert entry.message == "Will watch for changes in these directories: ['D:\\github\\webos']"
