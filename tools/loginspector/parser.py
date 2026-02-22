import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

# Regex to remove ANSI escape sequences
ANSI_ESCAPE_PATTERN = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# Regex to parse the WebOS loguru format:
# YYYY-MM-DD HH:mm:ss | LEVEL | module:function:line | extra | message
# e.g.: 2026-02-22 08:35:12 | INFO     | src.main:start:42 | {} | Server started
LOG_PATTERN = re.compile(
    r'^(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)\s*\|\s*'
    r'(?P<level>[A-Z\s]+?)\s*\|\s*'
    r'(?P<context>[^|]+?)\s*\|\s*'
    r'(?P<extra>[^|]+?)\s*\|\s*'
    r'(?P<message>.*)$',
    re.DOTALL  # Allow message to contain newlines (though usually they are on next lines until a new timestamp)
)

# Markers for session splitting
SESSION_MARKERS = [
    "🚀 Starting WebOS Server",
    "Started server process",
    "Uvicorn running on",
    "Logging initialized"
]

@dataclass
class LogEntry:
    time: str
    level: str
    context: str
    extra: str
    message: str
    source_file: str
    session_id: int
    raw_text: str

class LogParser:
    def __init__(self):
        self.current_session_id = 0
        self.current_entry: Optional[LogEntry] = None

    def clean_ansi(self, text: str) -> str:
        return ANSI_ESCAPE_PATTERN.sub('', text)

    def is_session_start(self, text: str) -> bool:
        for marker in SESSION_MARKERS:
            if marker in text:
                return True
        return False

    def parse_line(self, raw_line: str, source_file: str) -> Optional[LogEntry]:
        """
        Parses a single line. If it matches the log pattern, returns a new LogEntry.
        If it doesn't match, it might be a continuation of the previous log (e.g. traceback).
        In a stream, we usually buffer these. For simplicity, we just return None for continuations
        in this stateless call, but the caller should append to the last entry's message.
        """
        clean_line = self.clean_ansi(raw_line).rstrip('\n')
        
        # Check for session split markers
        if self.is_session_start(clean_line):
            self.current_session_id += 1

        # 1. Try Loguru custom (with extra dict)
        match = LOG_PATTERN.match(clean_line)
        if match:
            return LogEntry(
                time=match.group("time").strip(),
                level=match.group("level").strip(),
                context=match.group("context").strip(),
                extra=match.group("extra").strip(),
                message=match.group("message"),
                source_file=source_file,
                session_id=self.current_session_id,
                raw_text=clean_line
            )

        # 1.5 Try Loguru standard (without extra, using dash before message)
        # e.g.: 2026-02-22 08:57:17.053 | DEBUG    | src.core._load_module:97 - Loading module
        loguru_std_match = re.match(r'^(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)\s*\|\s*(?P<level>[A-Z\s]+?)\s*\|\s*(?P<context>[^|]+?)\s*-\s*(?P<message>.*)$', clean_line)
        if loguru_std_match:
            return LogEntry(
                time=loguru_std_match.group("time").strip(),
                level=loguru_std_match.group("level").strip(),
                context=loguru_std_match.group("context").strip(),
                extra="",
                message=loguru_std_match.group("message"),
                source_file=source_file,
                session_id=self.current_session_id,
                raw_text=clean_line
            )

        # 2. Try TaskIQ format
        # [2026-02-22 08:57:00,299][taskiq.worker][INFO   ][MainProcess] Pid of a main process
        taskiq_match = re.match(r'^\[(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\]\[(?P<context>[^\]]+)\]\[(?P<level>[^\]]+)\]\[[^\]]+\]\s*(?P<message>.*)$', clean_line)
        if taskiq_match:
            return LogEntry(
                time=taskiq_match.group("time").replace(",", "."),
                level=taskiq_match.group("level").strip(),
                context=taskiq_match.group("context").strip(),
                extra="",
                message=taskiq_match.group("message"),
                source_file=source_file,
                session_id=self.current_session_id,
                raw_text=clean_line
            )

        # 3. Try Uvicorn standard
        # INFO:     Will watch for changes in these directories:
        uvicorn_match = re.match(r'^(?P<level>[A-Z]+):\s+(?P<message>.*)$', clean_line)
        if uvicorn_match:
            import datetime
            return LogEntry(
                time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                level=uvicorn_match.group("level").strip(),
                context="uvicorn",
                extra="",
                message=uvicorn_match.group("message"),
                source_file=source_file,
                session_id=self.current_session_id,
                raw_text=clean_line
            )

        return None
