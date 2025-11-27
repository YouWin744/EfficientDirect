from typing import Dict, Tuple, NewType, TypedDict, Any, NamedTuple

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


def print_schedule(schedule: 'Schedule', full_details: bool = True):
    time_steps = sorted(schedule.keys())

    if not time_steps:
        if full_details:
            print("empty schedule")
        return

    if full_details:
        print("=" * 60)
        print('print schedule begin')
        print("=" * 45)

    T_B = 0

    for t in time_steps:
        step_schedule = schedule[t]

        if full_details:
            if t > 1:
                print("")
            print(f"t = {t}")

        u_t = 0

        dest_nodes = sorted(step_schedule.keys())

        for u in dest_nodes:
            entry = step_schedule[u]
            load_U = entry['load_U']
            transfers = entry['transfers']
            u_t = max(u_t, load_U)

            if full_details:
                # if t > 1 and u == dest_nodes[0]:
                #     print("")

                # print(f"t = {t}")
                print(f"    to {u}: (U = {load_U:.4f})")

                sorted_transfers = sorted(
                    transfers.items(), key=lambda item: (item[0][0], item[0][1]))

                for transfer_key, fraction in sorted_transfers:
                    print(
                        f"        from {transfer_key.from_node}, via {transfer_key.via_node}, load={fraction:.4f}")

        T_B += u_t

    if full_details:
        print("=" * 45)

    print(f"total T: {len(time_steps)}, total U: {T_B:.4f}")

    if full_details:
        print('print schedule end')
        print("=" * 60)
