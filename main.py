from core.registry import registry

import systems.moves


move_engine = registry.get("moves")

# print(move_engine)
# print(move_engine.move_set)

# for id, move in move_engine.move_set:
#     print(move.amount)
#     print(id, move, sep="\n\n:", end="\n\n" + "="*80 + "\n\n")

# print(move_engine.move_set["random_slash"])
move_engine.execute("ultimate_chaos_blast")