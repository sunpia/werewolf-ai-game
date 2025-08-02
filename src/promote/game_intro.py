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
            "abilities": ["eliminate_one_player_each_night"],
            "goal": "Eliminate villagers until werewolves equal or outnumber villagers."
        },
    },
    "phases": [
        {
            "name": "night",
            "order": [
                "werewolves_choose_target",
            ],
            "visibility_rules": {
                "werewolves": "know each other and choose a victim collectively",
                "villagers": "do not receive information"
            },
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
}
