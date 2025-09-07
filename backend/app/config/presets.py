from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass(frozen=True)
class ParamPreset:
    id: str
    label: str
    description: str
    params: Dict[str, Any]  # temperature, max_tokens, top_p, stop, etc.

PRESETS: List[ParamPreset] = [
    ParamPreset(
        id="precise",
        label="Precise",
        description="Low creativity, deterministic answers.",
        params={"temperature": 0.2, "top_p": 1.0}
    ),
    ParamPreset(
        id="balanced",
        label="Balanced",
        description="General purpose default.",
        params={"temperature": 0.7, "top_p": 1.0}
    ),
    ParamPreset(
        id="creative",
        label="Creative",
        description="Higher creativity for brainstorming.",
        params={"temperature": 0.9, "top_p": 1.0}
    ),
    ParamPreset(
        id="short",
        label="Short",
        description="Keep responses brief.",
        params={"max_tokens": 128}
    ),
    ParamPreset(
        id="medium",
        label="Medium",
        description="Balanced response length.",
        params={"max_tokens": 512}
    ),
    ParamPreset(
        id="long",
        label="Long",
        description="Long-form responses.",
        params={"max_tokens": 2048}
    ),
]

STOP_SNIPPETS: List[ParamPreset] = [
    ParamPreset(id="stop_triple_hash", label="Stop ###", description="Stop at ###", params={"stop": "###"}),
    ParamPreset(id="stop_md_rule", label="Stop ---", description="Stop at horizontal rule", params={"stop": "---"}),
    ParamPreset(id="stop_double_nl", label="Stop \\n\\n", description="Stop at blank line", params={"stop": "\n\n"}),
]
