from .common import *

@dataclass
class SoundEntry:
    offset: int
    sound_id: int
    source_id: int
    file_size: int
    override_fx: bool
