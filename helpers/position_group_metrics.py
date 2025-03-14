profile_metrics_dict = {
    "box_to_box": {
        "tackles_and_interceptions_per_90":
            {"weight": 1, "rename": "Tackles &\nInterceptions"},
        "ball_recoveries_per_90":
            {"weight": 1, "rename": "Ball\nRecoveries"},
        "progressive_carries_from_own_half_per_90":
            {"weight": 1, "rename": "Prog Carries\nOwn Half"},
        "passes_made_in_final_third_per_90":
            {"weight": 1, "rename": "Final Third\nPasses"},
        "total_np_xg_per_90":
            {"weight": 1, "rename": "Expected\nGoals"},
        "open_play_xga_per_90":
            {"weight": 1, "rename": "Expected\nAssists"}}}

position_metrics_dict = {
    "Central / Defensive Midfielder": {
        "total_obv_net_per_90":
            {"rename": "OBV"},
        # passing
        "pass_obv_per_90":
            {"rename": "Pass OBV"},
        "progressive_passes_per_90":
            {"rename": "Progressive Passes"},
        "passes_made_in_final_third_per_90":
            {"rename": "Final Third\nPasses"},
        "open_play_xga_per_90":
            {"rename": "Expected\nAssists"},
        "difference_to_expected_pass_completion_ratio":
            {"rename": "Difference to\nExpected Pass %"},
        "ball_retention_under_pressure":
            {"rename": "Ball Retention\nUnder Pressure %"},
        # carrying
        "total_dribble_carry_obv_per_90":
            {"rename": "Carry OBV"},
        "progressive_carries_from_own_half_per_90":
            {"rename": "Progressive Carries\nOwn Half"},
        "carries_into_final_third_per_90":
            {"rename": "Carries into\nFinal Third"},
        # ball winning
        "ball_recoveries_per_90":
            {"rename": "Ball\nRecoveries"},
        "tackles_and_interceptions_per_90":
            {"rename": "Tackles &\nInterceptions"},
        # shooting
        "total_np_xg_per_90":
            {"weight": .5, "rename": "Expected\nGoals"},
        # aerial
        "aerial_wins_per_90":
            {"weight": .5, "rename": "Aerial\nWins"}}}

# {"name": "carry_obv_from_own_half_per_90", "weight": .6, "rename": "Own Half\nCarry OBV"},
# {"name": "opp_half_pass_obv_per_90", "weight": .4, "rename": "Opp Half\nPass OBV"},
# {"name": "progressive_carries_from_own_half_per_90", "weight": .5, "rename": "Prog Carries\nOwn Half"},
# {"name": "passes_made_in_final_third_per_90", "weight": .5, "rename": "Final Third\nPasses"},

# {"name": "total_np_xg_per_90", "weight": .5, "rename": "Expected\nGoals"},
# {"name": "open_play_xga_per_90", "weight": .5, "rename": "Expected\nAssists"},
# {"name": "total_np_xg_plus_op_xga_per_90", "weight": 1, "rename": "Expected\nGoals+Assists"},


# "Defensive Midfielder": {
#         "player_season_obv_90":
#             {"rename": "OBV", "rank_asc": True, "percentage": False,
#              "key": "IMPACT OF A PLAYERS ACTIONS ON THEIR TEAMS CHANCES OF SCORING OR CONCEDING",
#              "rename_long": "OBV"},
#         "player_season_deep_progressions_90":
#             {"rename": "DEEP\nPROGRESSIONS", "rank_asc": True, "percentage": False,
#              "key": "PASSES AND CARRIES INTO THE FINAL THIRD",
#              "rename_long": "DEEP PROGRESSIONS"},
#         "player_season_obv_pass_90":
#             {"rename": "PASS OBV", "rank_asc": True, "percentage": False,
#              "key": "OBV FROM PASSES", "rename_long": "PASS OBV"
#              },
#         "player_season_op_xa_90":
#             {"rename": "OP xG ASSISTED", "rank_asc": True, "percentage": False,
#              "key": "xG CREATED FOR TEAM MATES IN OPEN PLAY", "rename_long": "OP xG ASSISTED"
#              },
#         "player_season_obv_dribble_carry_90":
#             {"rename": "DRIBBLE\nCARRY OBV", "rank_asc": True, "percentage": False,
#              "key": "OBV FROM DRIBBLES AND CARRIES", "rename_long": "DRIBBLE CARRY OBV"
#              },
#         "player_season_fouls_won_90":
#             {"rename": "FOULS WON", "rank_asc": True, "percentage": False,
#              "key": "FOULS WON", "rename_long": "FOULS WON"
#              },
#         "player_season_turnovers_90":
#             {"rename": "TURNOVERS", "rank_asc": False, "percentage": False,
#              "key": "LOSING THE BALL VIA A MISCONTROL OR FAILED DRIBBLE",
#              "rename_long": "TURNOVERS"
#              },
#         "player_season_padj_pressures_90":
#             {"rename": "Padj PRESSURES", "rank_asc": True, "percentage": False,
#              "key": "PRESSURES ADJUSTED FOR THEIR TEAMS POSSESSION",
#              "rename_long": "Padj PRESSURES"
#              },
#         "player_season_padj_tackles_and_interceptions_90":
#             {"rename": "Padj TACKLES\nINTERCEPTIONS", "rank_asc": True, "percentage": False,
#              "key": "TACKLES AND INTERCEPTIONS ADJUSTED FOR THEIR TEAMS POSSESSION",
#              "rename_long": "Padj TACKLES INTERCEPTIONS"
#              },
#         "player_season_challenge_ratio":
#             {"rename": "TACKLE %", "rank_asc": True, "percentage": True,
#              "key": "% OF WHEN A PLAYER MAKES A TACKLE VS BEING DRIBBLED PAST",
#              "rename_long": "TACKLE %"
#              },
#         "player_season_obv_defensive_action_90":
#             {"rename": "DEFENSIVE ACTION\nOBV", "rank_asc": True, "percentage": False,
#              "key": "OBV FROM DEFENSIVE ACTIONS",
#              "rename_long": "DEFENSIVE ACTION OBV"
#              }},

additional_metrics = [
    # {"name": "tackles_and_interceptions_in_defensive_third_per_90", "weight": 1},
    # {"name": "ball_recoveries_own_half_per_90", "weight": 1},
    # {"name": "pressures_in_final_third_per_90", "weight": 1},
    # {"name": "progressive_carries_from_own_half_per_90", "weight": 1},
    # {"name": "total_dribble_carry_obv_per_90", "weight": 1},
    # {"name": "progressive_carries_per_90", "weight": 1},
    # {"name": "progressive_passes_from_own_half_per_90", "weight": 1},
    # {"name": "deep_progressions_per_90", "weight": 1},
    # {"name": "carry_distance_from_own_half_per_90", "weight": 1},
    # {"name": "carry_distance_per_90", "weight": 1},
    # {"name": "passes_made_in_final_third_per_90", "weight": 1},
    # {"name": "final_third_pass_obv_per_90", "weight": .4},
    # {"name": "pass_obv_per_90", "weight": 1},
    # {"name": "total_dribble_carry_obv_per_90", "weight": 1},
    # {"name": "pass_obv_per_90", "weight": 1},
    # {"name": "total_np_shots_per_90", "weight": 1},
    # {"name": "open_play_xga_per_90", "weight": 1},
    # {"name": "total_np_xg_plus_op_xga_per_90", "weight": 1}

]
