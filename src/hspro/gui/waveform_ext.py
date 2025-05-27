from dataclasses import dataclass

from hspro_api import Waveform


@dataclass
class WaveformExt:
    waveform: Waveform
    color: str
