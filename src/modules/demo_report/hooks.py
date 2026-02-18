from src.core.hooks import hookimpl
from .tasks import generate_report_task

@hookimpl
def register_tasks(broker):
    """
    This hook is called by the ModuleLoader to register tasks.
    """
    # Simply importing the task module often registers it with the broker
    # if it's decorated with @broker.task.
    pass
