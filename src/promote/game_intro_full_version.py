# This file contains the game introduction for the Werewolf game, detailing roles, phases, and rules.
# It is used to provide context and setup for the game, ensuring all players understand their roles
# and the game mechanics.
# The description in this files is used for future state. The implementation of the game logic is still missing.
# The active introduction is in game_intro.py.

game_intro = {
    "game_name": "Werewolf",
    "description": "Social deduction game where hidden-role werewolves try to eliminate villagers while villagers try to identify them.",
    "roles": {
        "villager": {
            "alignment": "good",
            "abilities": [],
            "goal": "Identify and eliminate all werewolves."
        },
        "werewolf": {
            "alignment": "evil",
            "count": "depends on total players (typically 1/4 of players)",
            "abilities": ["eliminate_one_player_each_night"],
            "goal": "Eliminate villagers until werewolves equal or outnumber villagers."
        },
        "seer": {
            "alignment": "good",
            "count": 1,
            "abilities": ["inspect_one_player_role_per_night"],
            "goal": "Help villagers by revealing information."
        },
        "doctor": {
            "alignment": "good",
            "count": 1,
            "abilities": ["protect_one_player_per_night"],
            "goal": "Prevent eliminations by saving players."
        }
    },
    "phases": [
        {
            "name": "night",
            "order": [
                "werewolves_choose_target",
                "seer_inspects",
                "doctor_protects"
            ],
            "visibility_rules": {
                "werewolves": "know each other and choose a victim collectively",
                "seer": "receives inspection result privately",
                "doctor": "knows who they protected (but not if it was needed)",
                "villagers": "do not receive information"
            },
            "resolution": "Apply werewolves' elimination unless doctor protected that target. Record inspection result for seer."
        },
        {
            "name": "day",
            "order": [
                "reveal_night_elimination",
                "discussion",
                "vote_to_eliminate"
            ],
            "visibility_rules": {
                "all": "see who (if anyone) was eliminated last night; can discuss openly"
            },
            "resolution": "Player with majority votes is eliminated (revealed role)."
        }
    ],
    "win_conditions": {
        "villagers": "All werewolves have been eliminated.",
        "werewolves": "Number of werewolves is equal to or greater than number of remaining non-werewolf players."
    },
    "agent_responsibilities": {
        "initialize_game": "Assign roles randomly, track player list, ensure secrecy.",
        "manage_phase_transitions": "Switch between night and day, enforce order.",
        "collect_actions": {
            "night": {
                "werewolves": "Collect target choice privately.",
                "seer": "Collect inspection target.",
                "doctor": "Collect protection target."
            }
        },
        "resolve_actions": "Apply night actions in correct sequence with conflict handling (doctor can save werewolves' target).",
        "facilitate_discussion": "Announce daytime events, guide discussion, prompt for votes.",
        "tally_votes": "Determine elimination based on majority or predefined tie-breaker rule.",
        "check_win": "After each elimination, evaluate win conditions and declare winner if met.",
        "reveal_information": "Only disclose information appropriate to role/phase."
    },
    "example_initial_state": {
        "players": [
            {"id": "player1", "role": "villager", "alive": True},
            {"id": "player2", "role": "werewolf", "alive": True},
            {"id": "player3", "role": "seer", "alive": True},
            {"id": "player4", "role": "doctor", "alive": True},
            {"id": "player5", "role": "villager", "alive": True}
        ],
        "phase": "night",
        "history": []
    },
    "configuration_options": {
        "role_variants": ["add more special roles like hunter, cupid, etc."],
        "tie_breaker": "If vote is tied, no one is eliminated or implement predefined rule (e.g., revote or random)."
    }
}
