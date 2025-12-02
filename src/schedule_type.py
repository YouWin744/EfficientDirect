from typing import Dict, NewType, TypedDict, Any, NamedTuple

Node = Any
TimeStep = NewType('TimeStep', int)
Fraction = NewType('Fraction', float)


class TransferKey(NamedTuple):
    from_node: Node
    via_node: Node


TransferMap = Dict[TransferKey, Fraction]


class ScheduleEntry(TypedDict):
    load_U: float
    transfers: TransferMap


Schedule = Dict[TimeStep, Dict[Node, ScheduleEntry]]
