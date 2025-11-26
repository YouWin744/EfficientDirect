from typing import Dict, Tuple, NewType, TypedDict, Any

Node = Any
TimeStep = NewType('TimeStep', int)
Fraction = NewType('Fraction', float)
TransferKey = Tuple[Node, Node]  # (from, via)
TransferMap = Dict[TransferKey, Fraction]


class ScheduleEntry(TypedDict):
    load_U: float
    transfers: TransferMap


Schedule = Dict[TimeStep, Dict[Node, ScheduleEntry]]


def print_schedule(schedule: Schedule):

    time_steps = sorted(schedule.keys())

    if not time_steps:
        print("empty schedule")
        return

    print("=" * 60)
    print('print schedule begin')
    print("=" * 45)

    T_B = 0

    for t in time_steps:
        step_schedule = schedule[t]

        if t > 1:
            print("")
        print(f"t = {t}")

        dest_nodes = sorted(step_schedule.keys())

        u_t = 0

        for u in dest_nodes:
            entry = step_schedule[u]
            load_U = entry['load_U']
            transfers = entry['transfers']
            u_t = max(u_t, load_U)

            print(f"    to {u}: (U = {load_U:.4f})")

            sorted_transfers = sorted(
                transfers.items(), key=lambda item: (item[0][0], item[0][1]))

            for (v, w), fraction in sorted_transfers:
                print(f"        from {v}, via {w}, load={fraction:.4f}")

        T_B += u_t

    print("=" * 45)
    print(f"total U: {T_B:.4f}")
    print('print schedule end')
    print("=" * 60)
