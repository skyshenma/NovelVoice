
from typing import Dict, Any

# Prevent circular import if TTSProcessor is not needed for type hinting immediately
# or use TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.tts_engine import TTSProcessor

class GlobalState:
    active_processors: Dict[str, Any] = {} # Key: book_name, Value: TTSProcessor instance
    active_packers: Dict[str, str] = {} # Key: book_name, Value: status ("packing", "cancelling")
    cancel_events: Dict[str, Any] = {} # Key: book_name, Value: threading.Event
    concurrency: int = 2

state = GlobalState()
