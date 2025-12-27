from core.registry import registry

import systems.moves
import systems.fighters


move_engine = registry.get("moves")
fighter_engine = registry.get("fighters")

# # print(move_engine)
# # print(move_engine.move_set)

# # for id, move in move_engine.move_set:
# #     print(move.amount)
# #     print(id, move, sep="\n\n:", end="\n\n" + "="*80 + "\n\n")

# move_engine.execute("ultimate_chaos_blast")

fighter_engine = registry.get("fighters")

print(fighter_engine.fighter_set["fighter_002"])