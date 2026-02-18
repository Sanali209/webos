from taskiq import TaskiqMiddleware, TaskiqMessage
from typing import Any, Optional
from contextvars import ContextVar
import uuid

# Context variables for the request cycle
user_id_context: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
trace_id_context: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

class ContextPropagationMiddleware(TaskiqMiddleware):
    """
    Middleware to propagate context variables from the producer to the worker.
    """
    def pre_send(self, message: TaskiqMessage) -> TaskiqMessage:
        # Inject context into message headers
        message.labels["user_id"] = user_id_context.get()
        # Ensure trace_id is a string, generate if missing
        trace_id = trace_id_context.get()
        if not trace_id:
            trace_id = str(uuid.uuid4())
            trace_id_context.set(trace_id)
        message.labels["trace_id"] = trace_id
        return message

    def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        # Restore context in the worker
        user_id_context.set(message.labels.get("user_id"))
        trace_id_context.set(message.labels.get("trace_id", str(uuid.uuid4())))
        return message
