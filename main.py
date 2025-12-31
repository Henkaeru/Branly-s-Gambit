import random
from time import sleep
from core.registry import registry

import systems.battle
from systems.battle.schema import Battle


# move_engine = registry.get("moves")
# fighter_engine = registry.get("fighters")

# # # print(move_engine)
# # # print(move_engine.move_set)

# # # for id, move in move_engine.move_set:
# # #     print(move.amount)
# # #     print(id, move, sep="\n\n:", end="\n\n" + "="*80 + "\n\n")

# # move_engine.execute("ultimate_chaos_blast")

# fighter_engine = registry.get("fighters")


# ryu = fighter_engine.fighter_set["fighter_001"]
# ken = fighter_engine.fighter_set["fighter_002"]

# move_engine.execute(ryu.moves[2])

battle_engine = registry.get("battle")
battle_engine.start(Battle.from_sides(
    id="1v1_match",
    sides=[
        ["fighter_001"],
        ["fighter_002"]
    ]
))
for battle_log in battle_engine.battle.current_context.get_next_logs():
    print(f"{battle_log}")

print(f"{battle_engine.battle.current_context.sides[0][0].current_fighter.name} HP: {battle_engine.battle.current_context.sides[0][0].current_stats.hp} SHIELD: {battle_engine.battle.current_context.sides[0][0].current_stats.shield} CHARGE: {battle_engine.battle.current_context.sides[0][0].current_stats.charge}")
print(f"{battle_engine.battle.current_context.sides[1][0].current_fighter.name} HP: {battle_engine.battle.current_context.sides[1][0].current_stats.hp} SHIELD: {battle_engine.battle.current_context.sides[1][0].current_stats.shield} CHARGE: {battle_engine.battle.current_context.sides[1][0].current_stats.charge}")
while(battle_engine.step()):
    for battle_log in battle_engine.battle.current_context.get_next_logs():
        print(f"├── {battle_log}")
    print(f"{battle_engine.battle.current_context.sides[0][0].current_fighter.name} HP: {battle_engine.battle.current_context.sides[0][0].current_stats.hp} SHIELD: {battle_engine.battle.current_context.sides[0][0].current_stats.shield} CHARGE: {battle_engine.battle.current_context.sides[0][0].current_stats.charge}")
    print(f"{battle_engine.battle.current_context.sides[1][0].current_fighter.name} HP: {battle_engine.battle.current_context.sides[1][0].current_stats.hp} SHIELD: {battle_engine.battle.current_context.sides[1][0].current_stats.shield} CHARGE: {battle_engine.battle.current_context.sides[1][0].current_stats.charge}")
    sleep(1)  # just to slow down the output for readability

for battle_log in battle_engine.battle.current_context.get_next_logs():
    print(f"└── {battle_log}")
print('\n')
print("Final Logs:")
for log in battle_engine.battle.current_context.log_history:
    print(f"├── {log}")
print("└── End of logs.")
