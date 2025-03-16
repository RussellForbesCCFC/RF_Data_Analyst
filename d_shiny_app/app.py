import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from shiny import App, render, ui, reactive
from shiny.express.ui import card_header
import pandas as pd
import io
from matplotlib import gridspec
from matplotlib import font_manager, rcParams
from PIL import Image
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)

avenir_next_condensed_path = "Avenir Next Condensed.ttc"
avenir_path = "Avenir.ttc"
font_manager.fontManager.addfont(avenir_next_condensed_path)
font_manager.fontManager.addfont(avenir_path)
rcParams['font.family'] = 'Avenir Next Condensed'

data_df = pd.read_csv("player_aggregated_data.csv")

data_columns = data_df.columns.tolist()
filter_data_columns = []
for d in data_columns:
    end_of_string = d[-6:]
    if end_of_string == "per_90":
        filter_data_columns.append(d)

wider_position_list = ["Goalkeeper", "Left Back", "Right Back", "Center Back",
                       "Central / Defensive Midfielder",
                       "Left Midfielder / Winger",
                       "Right Midfielder / Winger",
                       "Attacking Midfielder",
                       "Center Forward"]

profile_dictionaries = {
    "Box to Box Midfielder": [
        {"name": "tackles_and_interceptions_per_90", "weight": 1},
        {"name": "ball_recoveries_per_90", "weight": 1},
        {"name": "progressive_carries_from_own_half_per_90", "weight": 1},
        {"name": "passes_made_in_final_third_per_90", "weight": 1},
        {"name": "total_np_xg_per_90", "weight": 1},
        {"name": "open_play_xga_per_90", "weight": 1}],
    "Deep Lying Playmaker": [
        {"name": "completed_passes_per_90", "weight": 1},
        {"name": "passes_into_final_third_per_90", "weight": 1},
        {"name": "progressive_passes_from_own_half_per_90", "weight": 1},
        {"name": "open_play_xga_per_90", "weight": 1},
        {"name": "pass_obv_per_90", "weight": 1},
        {"name": "open_play_pass_goal_assist_per_90", "weight": 1}]
}

position_metrics_dict = {
    "Central / Defensive Midfielder": {
        "total_obv_net_per_90":
            {"rename": "OBV"},
        # passing
        "pass_obv_per_90":
            {"rename": "Pass OBV"},
        "progressive_passes_per_90":
            {"rename": "Progressive\nPasses"},
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

profile_list = [i for i in profile_dictionaries.keys()]
profile_list.insert(0, "None")

metrics_dict = {"None": "None",
                'total_np_shots_per_90': "Np Shots",
                'total_np_goals_per_90': "Np Goals",
                'total_np_xg_per_90': "xG",
                'np_on_target_shots_per_90': "Shots on Target",
                'total_dribbles_per_90': "Dribbles",
                'completed_dribbles_per_90': "Dribbles Completed",
                'total_dribble_carry_obv_per_90': "Dribble/Carry Obv",
                'carry_obv_from_own_half_per_90': "Carry Obv Own Half",
                'carries_into_final_third_per_90': "Carries into Final Third",
                'carry_distance_per_90': "Carry Distance",
                'carry_distance_from_own_half_per_90': "Carry Distance Own Half",
                'progressive_carries_per_90': "Progressive Carries",
                'progressive_carries_from_own_half_per_90': "Progressive Carries Own Half",
                'total_passes_per_90': "Passes",
                'open_play_total_passes_per_90': "Open Play Passes",
                'completed_passes_per_90': "Completed Passes",
                'key_passes_per_90': "Key Passes",
                'open_play_key_passes_per_90': "Open Play key Passes",
                'passes_into_final_third_per_90': "Passes into Final Third",
                'passes_made_in_final_third_per_90': "Passes in Final Third",
                'final_third_pass_obv_per_90': "Final Third Pass Obv",
                'opp_half_pass_obv_per_90': "Opp Half Pass Obv",
                'attempted_crosses_per_90': "Crosses",
                'successful_crosses_per_90': "Successful Crosses",
                'progressive_passes_per_90': "Progressive Passes",
                'progressive_passes_from_own_half_per_90': "Progressive Passes Own Half",
                'total_passes_under_pressure_per_90': "Passes Under Pressure",
                'completed_passes_under_pressure_per_90': "Completed Passes Under Pressure",
                'touches_inside_box_per_90': "Box Touches",
                'touches_in_final_third_per_90': "Final Third Touches",
                'xga_per_90': "xGA",
                'open_play_xga_per_90': "Open Play xGA",
                'set_piece_xga_per_90': "Set Piece xGA",
                'pass_goal_assist_per_90': "Assists",
                'open_play_pass_goal_assist_per_90': "Open Play Assists",
                'pass_obv_per_90': "Pass Obv",
                'total_tackles_per_90': "Tackles",
                'successful_tackles_per_90': "Successful Tackles",
                'tackles_in_defensive_third_per_90': "Tackles in Defensive Third",
                'total_interceptions_per_90': "Interceptions",
                'interceptions_in_defensive_third_per_90': "Interceptions in Defensive Third",
                'dribbled_past_per_90': "Dribbled Past",
                'aerial_losses_per_90': "Aerial Losses",
                'aerial_wins_per_90': "Aerial Wins",
                'fouls_won_per_90': "Fouls Won",
                'ball_recoveries_per_90': "Ball Recoveries",
                'ball_recoveries_own_half_per_90': "Ball Recoveries Own Half",
                'ball_recoveries_opp_half_per_90': "Ball Recoveries Opp Half",
                'pressures_per_90': "Pressures",
                'pressure_regains_per_90': "Pressure Regains",
                'pressures_in_opp_half_per_90': "Pressures Opp Half",
                'pressures_in_final_third_per_90': "Pressures in Final Third",
                'fouls_per_90': "Fouls",
                'clearances_per_90': "Clearances",
                'turnovers_per_90': "Turnovers",
                'dispossessions_per_90': "Dispossessions",
                'defensive_action_obv_per_90': "Defensive Action Obv",
                'total_aerial_duels_per_90': "Aerial Duels",
                'tackles_and_interceptions_per_90': "Tackles & Interceptions",
                'tackles_and_interceptions_in_defensive_third_per_90': "Tackles and Interceptions Defensive Third",
                'deep_progressions_per_90': "Deep Progressions",
                'total_np_xg_plus_op_xga_per_90': "xG + xGA"}

reverse_metric_rename_dict = {}
for metric, metric_rename in metrics_dict.items():
    reverse_metric_rename_dict[metric_rename] = metric

metrics_list = [n for i, n in metrics_dict.items()]

rename_dict = metrics_dict.copy()
rename_dict["player"] = "Player"
rename_dict["team"] = "Team"
rename_dict["competition_name"] = "Competition"
rename_dict["total_time_minutes"] = "Minutes in Position"
rename_dict["position_group"] = "Position"
rename_dict["total_obv_net_per_90"] = "OBV"

team_list = sorted(data_df["team"].unique().tolist())


def add_player_z_score(row, _metric, df, metric_weight):
    player_value = row[_metric]
    metric_average = df[_metric].mean()
    metric_std = df[_metric].std()

    player_std_from_mean = (player_value - metric_average) / metric_std
    weighted_std_from_mean = player_std_from_mean * metric_weight

    return weighted_std_from_mean


def scale_weighted_average(row, df):
    player_z_weighted_average = row["z_score_weighted_average"]
    max_z_weighted = df["z_score_weighted_average"].max()
    min_z_weighted = df["z_score_weighted_average"].min()
    scaled_z_score = (player_z_weighted_average - min_z_weighted) / (max_z_weighted - min_z_weighted)
    return scaled_z_score


# APP WORKINGS ---------------------------------------------------------------------------------------------------------
# testing new ui
app_ui = ui.page_navbar(
    ui.nav_panel("Player Search",
                 ui.layout_columns(
                     ui.card(
                         ui.card_header("PLAYER FILTERS"),
                         ui.card_body(
                             ui.input_selectize("position", "Position", wider_position_list,
                                                selected="Central / Defensive Midfielder"),
                             ui.input_selectize("profile", "Profile", profile_list),
                             ui.input_slider("minute_filter", "Minutes Played",
                                             min=0, max=800,
                                             value=300, step=50),
                             ui.output_ui("render_metric_one_selector"),
                             ui.output_ui("render_one_metric_weight"),
                             ui.output_ui("render_metric_two_selector"),
                             ui.output_ui("render_two_metric_weight"),
                             ui.output_ui("render_metric_three_selector"),
                             ui.output_ui("render_three_metric_weight"),
                             ui.output_ui("render_metric_four_selector"),
                             ui.output_ui("render_four_metric_weight"),
                             ui.output_ui("render_metric_five_selector"),
                             ui.output_ui("render_five_metric_weight"),
                             ui.output_ui("render_metric_six_selector"),
                             ui.output_ui("render_six_metric_weight")),
                     ),

                     ui.card(
                         ui.output_ui("render_results_headers"),
                         ui.output_data_frame("render_player_results_table")),
                     ui.card(
                         ui.output_ui("render_z_scores_header"),
                         ui.output_plot("show_player_z_scores")),
                     col_widths=[2, 7, 3])),

    ui.nav_panel("Player Radar - Central Midfielders",
                 ui.layout_columns(
                     ui.card(
                         ui.card_header("PLAYER SEARCH"),
                         ui.card_body(
                             ui.input_slider("player_search_minute_filter", "Minutes Played",
                                             min=0, max=800,
                                             value=300, step=50),
                             ui.output_ui("render_player_player_filter"))),
                     ui.card(
                         # ui.output_ui("render_filtered_player_radar_header"),
                         ui.card_body(
                             ui.output_plot("render_player_radar"),
                             fill=True,
                             min_height="500px")),
                     ui.card(
                         ui.card_header("PLAYER COMPARISON"),
                         ui.card_body(
                             ui.output_ui("render_player_player_comparison_filter"),
                             ui.download_button("download_player_radar", "Download Plot",
                                                icon="⬇", class_="btn-primary"))),
                     col_widths=[2, 8, 2]
                 )), fillable=True)


def server(input_, output_, session_):
    @reactive.Calc
    @render.ui()
    def render_metric_one_selector():
        profile_input = input_.profile()
        if profile_input != "None":
            selected_profile_metrics = profile_dictionaries[profile_input]
            default_value = metrics_dict[selected_profile_metrics[0]["name"]]
        else:
            default_value = "None"

        custom_metrics_list = metrics_list.copy()

        return ui.input_selectize("metric_one_selector", "Metric 1", custom_metrics_list, selected=default_value)

    @reactive.Calc
    @render.ui()
    def render_one_metric_weight():
        profile_input = input_.profile()
        if profile_input != "None":
            selected_profile_metrics = profile_dictionaries[profile_input]
            default_value = (selected_profile_metrics[0]["weight"]) * 100
        else:
            default_value = 50
        metric_one_input = input_.metric_one_selector()
        if metric_one_input != "None":
            return ui.input_slider("metric_one_weight", f"{metric_one_input} Weight",
                                   0, 100, value=default_value, step=5)

    # Render 2nd metric and weight
    @reactive.Calc
    @render.ui()
    def render_metric_two_selector():
        profile_input = input_.profile()
        if profile_input != "None":
            selected_profile_metrics = profile_dictionaries[profile_input]
            default_value = metrics_dict[selected_profile_metrics[1]["name"]]
        else:
            default_value = "None"

        metric_one_input = input_.metric_one_selector()
        if metric_one_input != "None":
            custom_metrics_list = metrics_list.copy()
            custom_metrics_list.remove(metric_one_input)
            return ui.input_selectize("metric_two_selector", "Metric 2", custom_metrics_list, selected=default_value)

    @reactive.Calc
    @render.ui()
    def render_two_metric_weight():
        profile_input = input_.profile()
        if profile_input != "None":
            selected_profile_metrics = profile_dictionaries[profile_input]
            default_value = (selected_profile_metrics[1]["weight"]) * 100
        else:
            default_value = 50
        metric_two_input = input_.metric_two_selector()
        if metric_two_input != "None":
            return ui.input_slider("metric_two_weight", f"{metric_two_input} Weight",
                                   0, 100, value=default_value, step=5)

    # Render 3rd metric and weight
    @reactive.Calc
    @render.ui()
    def render_metric_three_selector():
        profile_input = input_.profile()
        if profile_input != "None":
            selected_profile_metrics = profile_dictionaries[profile_input]
            default_value = metrics_dict[selected_profile_metrics[2]["name"]]
        else:
            default_value = "None"
        metric_one_input = input_.metric_one_selector()
        metric_two_input = input_.metric_two_selector()
        if metric_two_input != "None":
            custom_metrics_list = metrics_list.copy()
            custom_metrics_list.remove(metric_one_input)
            custom_metrics_list.remove(metric_two_input)

            return ui.input_selectize("metric_three_selector", "Metric 3", custom_metrics_list, selected=default_value)

    @reactive.Calc
    @render.ui()
    def render_three_metric_weight():
        profile_input = input_.profile()
        if profile_input != "None":
            selected_profile_metrics = profile_dictionaries[profile_input]
            default_value = (selected_profile_metrics[2]["weight"]) * 100
        else:
            default_value = 50
        metric_three_input = input_.metric_three_selector()
        if metric_three_input != "None":
            return ui.input_slider("metric_three_weight", f"{metric_three_input} Weight",
                                   0, 100, value=default_value, step=5)

    # Render 4th metric and weight
    @reactive.Calc
    @render.ui()
    def render_metric_four_selector():
        profile_input = input_.profile()
        if profile_input != "None":
            selected_profile_metrics = profile_dictionaries[profile_input]
            default_value = metrics_dict[selected_profile_metrics[3]["name"]]
        else:
            default_value = "None"
        metric_one_input = input_.metric_one_selector()
        metric_two_input = input_.metric_two_selector()
        metric_three_input = input_.metric_three_selector()
        if metric_three_input != "None":
            custom_metrics_list = metrics_list.copy()
            custom_metrics_list.remove(metric_one_input)
            custom_metrics_list.remove(metric_two_input)
            custom_metrics_list.remove(metric_three_input)
            return ui.input_selectize("metric_four_selector", "Metric 4", custom_metrics_list, selected=default_value)

    @reactive.Calc
    @render.ui()
    def render_four_metric_weight():
        profile_input = input_.profile()
        if profile_input != "None":
            selected_profile_metrics = profile_dictionaries[profile_input]
            default_value = (selected_profile_metrics[3]["weight"]) * 100
        else:
            default_value = 50
        metric_four_input = input_.metric_four_selector()
        if metric_four_input != "None":
            return ui.input_slider("metric_four_weight", f"{metric_four_input} Weight",
                                   0, 100, value=default_value, step=5)

    # Render 4th metric and weight
    @reactive.Calc
    @render.ui()
    def render_metric_five_selector():
        profile_input = input_.profile()
        if profile_input != "None":
            selected_profile_metrics = profile_dictionaries[profile_input]
            default_value = metrics_dict[selected_profile_metrics[4]["name"]]
        else:
            default_value = "None"
        metric_one_input = input_.metric_one_selector()
        metric_two_input = input_.metric_two_selector()
        metric_three_input = input_.metric_three_selector()
        metric_four_input = input_.metric_four_selector()
        if metric_four_input != "None":
            custom_metrics_list = metrics_list.copy()
            custom_metrics_list.remove(metric_one_input)
            custom_metrics_list.remove(metric_two_input)
            custom_metrics_list.remove(metric_three_input)
            custom_metrics_list.remove(metric_four_input)
            return ui.input_selectize("metric_five_selector", "Metric 5", custom_metrics_list, selected=default_value),

    @reactive.Calc
    @render.ui()
    def render_five_metric_weight():
        profile_input = input_.profile()
        if profile_input != "None":
            selected_profile_metrics = profile_dictionaries[profile_input]
            default_value = (selected_profile_metrics[4]["weight"]) * 100
        else:
            default_value = 50
        metric_five_input = input_.metric_five_selector()
        if metric_five_input != "None":
            return ui.input_slider("metric_five_weight", f"{metric_five_input} Weight",
                                   0, 100, value=default_value, step=5)

    # Render 5th metric and weight
    @reactive.Calc
    @render.ui()
    def render_metric_six_selector():
        profile_input = input_.profile()
        if profile_input != "None":
            selected_profile_metrics = profile_dictionaries[profile_input]
            default_value = metrics_dict[selected_profile_metrics[5]["name"]]
        else:
            default_value = "None"
        metric_one_input = input_.metric_one_selector()
        metric_two_input = input_.metric_two_selector()
        metric_three_input = input_.metric_three_selector()
        metric_four_input = input_.metric_four_selector()
        metric_five_input = input_.metric_five_selector()
        if metric_five_input != "None":
            custom_metrics_list = metrics_list.copy()
            custom_metrics_list.remove(metric_one_input)
            custom_metrics_list.remove(metric_two_input)
            custom_metrics_list.remove(metric_three_input)
            custom_metrics_list.remove(metric_four_input)
            custom_metrics_list.remove(metric_five_input)
            return ui.input_selectize("metric_six_selector", "Metric 6", custom_metrics_list, selected=default_value),

    @reactive.Calc
    @render.ui()
    def render_six_metric_weight():
        profile_input = input_.profile()
        if profile_input != "None":
            selected_profile_metrics = profile_dictionaries[profile_input]
            default_value = (selected_profile_metrics[5]["weight"]) * 100
        else:
            default_value = 50
        metric_six_input = input_.metric_six_selector()
        if metric_six_input != "None":
            return ui.input_slider("metric_six_weight", f"{metric_six_input} Weight",
                                   0, 100, value=default_value, step=5)

    @reactive.Calc
    @render.ui()
    def render_results_headers():
        position_group_input = input_.position()
        minute_input = input_.minute_filter()

        metric_one_input = input_.metric_one_selector()

        # if metric one input exists then there will be a metric one weighting
        # there will also be a metric two selector
        if metric_one_input != "None":
            metric_one_weight = input_.metric_one_weight()
            metric_two_input = input_.metric_two_selector()

        # if metric one is not rendered
        else:
            metric_one_weight = -1
            metric_two_input = "None"
        if metric_two_input != "None":
            metric_two_weight = input_.metric_two_weight()
            metric_three_input = input_.metric_three_selector()
        else:
            metric_two_weight = -1
            metric_three_input = "None"

        if metric_three_input != "None":
            metric_three_weight = input_.metric_three_weight()
            metric_four_input = input_.metric_four_selector()
        else:
            metric_three_weight = -1
            metric_four_input = "None"

        if metric_four_input != "None":
            metric_four_weight = input_.metric_four_weight()
            metric_five_input = input_.metric_five_selector()
        else:
            metric_four_weight = -1
            metric_five_input = "None"

        if metric_five_input != "None":
            metric_five_weight = input_.metric_five_weight()
            metric_six_input = input_.metric_six_selector()
        else:
            metric_five_weight = -1
            metric_six_input = "None"

        if metric_six_input != "None":
            metric_six_weight = input_.metric_five_weight()
        else:
            metric_six_weight = -1

        raw_metric_list = [metric_one_input, metric_two_input,
                           metric_three_input, metric_four_input,
                           metric_five_input, metric_six_input]

        raw_weightings_list = [metric_one_weight, metric_two_weight,
                               metric_three_weight, metric_four_weight,
                               metric_five_weight, metric_six_weight]

        rendered_metric_list = [reverse_metric_rename_dict[i] for i in raw_metric_list if i != "None"]

        if len(rendered_metric_list) == 0:
            sort_text = "Sorted by OBV"
        else:
            sort_text = "Sorted by Profile Match"

        return ui.card_header(f"Search Results - {position_group_input} - Minimum {minute_input} Minutes - {sort_text}")

    @reactive.Calc
    def create_player_results_table():
        position_group_input = input_.position()
        minute_input = input_.minute_filter()

        metric_one_input = input_.metric_one_selector()

        # if metric one input exists then there will be a metric one weighting
        # there will also be a metric two selector
        if metric_one_input != "None":
            metric_one_weight = input_.metric_one_weight()
            metric_two_input = input_.metric_two_selector()

        # if metric one is not rendered
        else:
            metric_one_weight = -1
            metric_two_input = "None"
        if metric_two_input != "None":
            metric_two_weight = input_.metric_two_weight()
            metric_three_input = input_.metric_three_selector()
        else:
            metric_two_weight = -1
            metric_three_input = "None"

        if metric_three_input != "None":
            metric_three_weight = input_.metric_three_weight()
            metric_four_input = input_.metric_four_selector()
        else:
            metric_three_weight = -1
            metric_four_input = "None"

        if metric_four_input != "None":
            metric_four_weight = input_.metric_four_weight()
            metric_five_input = input_.metric_five_selector()
        else:
            metric_four_weight = -1
            metric_five_input = "None"

        if metric_five_input != "None":
            metric_five_weight = input_.metric_five_weight()
            metric_six_input = input_.metric_six_selector()
        else:
            metric_five_weight = -1
            metric_six_input = "None"

        if metric_six_input != "None":
            metric_six_weight = input_.metric_five_weight()
        else:
            metric_six_weight = -1

        raw_metric_list = [metric_one_input, metric_two_input,
                           metric_three_input, metric_four_input,
                           metric_five_input, metric_six_input]

        raw_weightings_list = [metric_one_weight, metric_two_weight,
                               metric_three_weight, metric_four_weight,
                               metric_five_weight, metric_six_weight]

        rendered_metric_list = [reverse_metric_rename_dict[i] for i in raw_metric_list if i != "None"]
        rendered_weightings_list = [(w / 100) for w in raw_weightings_list if w > 0]

        standard_columns = ["player", "team", "competition_name", "position_group", "total_time_minutes",
                            "total_obv_net_per_90"]

        for col in rendered_metric_list:
            standard_columns.append(col)

        filtered_data_df = data_df[
            (data_df["position_group"] == position_group_input)
            & (data_df["total_time_minutes"] >= minute_input)][standard_columns]

        if len(rendered_metric_list) == 0:
            filtered_data_df.sort_values("total_obv_net_per_90", ascending=False, inplace=True)

        # if there is items in the metric list need to calculate their z-scores and the player average z-score
        else:
            metric_z_score_names_weighted = []
            for n, met in enumerate(rendered_metric_list):
                metric_weight = rendered_weightings_list[n]
                metric_z_score_names_weighted.append(f"{met}_z_score_weighted")

                filtered_data_df[f"{met}_z_score_weighted"] = filtered_data_df.apply(
                    lambda _row: add_player_z_score(_row, met, filtered_data_df, metric_weight), axis=1)

            filtered_data_df["z_score_weighted_average"] = filtered_data_df[
                metric_z_score_names_weighted].mean(axis=1)

            filtered_data_df["z_score_weighted_average_scaled"] = filtered_data_df.apply(
                lambda row_: scale_weighted_average(row_, filtered_data_df),
                axis=1)

            filtered_data_df["z_score_weighted_average_scaled"] = round(
                filtered_data_df["z_score_weighted_average_scaled"] * 100, 1)

            filtered_data_df.sort_values("z_score_weighted_average_scaled", ascending=False, inplace=True)
            filtered_data_df.drop(columns=metric_z_score_names_weighted, inplace=True)
            filtered_data_df.drop(columns="z_score_weighted_average", inplace=True)
            filtered_data_df.rename(columns={"z_score_weighted_average_scaled": "Profile %"}, inplace=True)

        filtered_data_df["total_time_minutes"] = filtered_data_df["total_time_minutes"].round(0).astype(int)
        filtered_data_df["total_obv_net_per_90"] = filtered_data_df["total_obv_net_per_90"].round(2)

        filtered_data_df[rendered_metric_list] = filtered_data_df[rendered_metric_list].round(2)

        filtered_data_df.rename(columns={i: rename_dict[i] for i in standard_columns}, inplace=True)

        return filtered_data_df
        # return render.DataGrid(filtered_data_df, selection_mode="row")

    @render.data_frame
    def render_player_results_table():
        df = create_player_results_table()
        return render.DataGrid(df, selection_mode="row")

    @reactive.Calc
    @render.ui()
    def render_z_scores_header():
        position_group_input = input_.position()
        minute_input = input_.minute_filter()

        df = create_player_results_table()
        selected = render_player_results_table.cell_selection()["rows"]

        if selected:
            player_row = df.iloc[selected]
            player_name = player_row["Player"]
            player_team = player_row["Team"]

            title = f"{player_name} - {player_team} - Compared to {position_group_input}s - Minimum {minute_input} Minutes"
            return card_header(title)

    @reactive.Calc
    @render.plot
    def show_player_z_scores():
        position_group_input = input_.position()
        minute_input = input_.minute_filter()

        metric_one_input = input_.metric_one_selector()

        # if metric one input exists then there will be a metric one weighting
        # there will also be a metric two selector
        if metric_one_input != "None":
            metric_one_weight = input_.metric_one_weight()
            metric_two_input = input_.metric_two_selector()

        # if metric one is not rendered
        else:
            metric_one_weight = -1
            metric_two_input = "None"
        if metric_two_input != "None":
            metric_two_weight = input_.metric_two_weight()
            metric_three_input = input_.metric_three_selector()
        else:
            metric_two_weight = -1
            metric_three_input = "None"

        if metric_three_input != "None":
            metric_three_weight = input_.metric_three_weight()
            metric_four_input = input_.metric_four_selector()
        else:
            metric_three_weight = -1
            metric_four_input = "None"

        if metric_four_input != "None":
            metric_four_weight = input_.metric_four_weight()
            metric_five_input = input_.metric_five_selector()
        else:
            metric_four_weight = -1
            metric_five_input = "None"

        if metric_five_input != "None":
            metric_five_weight = input_.metric_five_weight()
            metric_six_input = input_.metric_six_selector()
        else:
            metric_five_weight = -1
            metric_six_input = "None"

        if metric_six_input != "None":
            metric_six_weight = input_.metric_five_weight()
        else:
            metric_six_weight = -1

        raw_metric_list = [metric_one_input, metric_two_input,
                           metric_three_input, metric_four_input,
                           metric_five_input, metric_six_input]

        raw_weightings_list = [metric_one_weight, metric_two_weight,
                               metric_three_weight, metric_four_weight,
                               metric_five_weight, metric_six_weight]

        rendered_metric_list = [reverse_metric_rename_dict[i] for i in raw_metric_list if i != "None"]
        rendered_weightings_list = [(w / 100) for w in raw_weightings_list if w > 0]

        df = create_player_results_table()

        # get player id
        selected = render_player_results_table.cell_selection()["rows"]
        player_row = df.iloc[selected]
        player_name = player_row["Player"]
        player_team = player_row["Team"]

        if selected:
            # FIGURE
            fig = plt.figure()
            ax = fig.add_subplot()

            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_visible(False)

            ax.yaxis.set_ticks([])
            ax.xaxis.set_ticks([])

            ax.set_xlim(-3.3, 3.3)
            ax.set_ylim(0, 6.5)

            ax.plot([0, 0], [0.75, 6.25], color="black", alpha=.5, lw=.5, ls="--")

            y_start = 6
            for z_metric in rendered_metric_list:
                ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [y_start, y_start],
                        color="black", alpha=.5, lw=.5, zorder=1)

                z_metric_rename = metrics_dict[z_metric]
                metric_average = df[z_metric_rename].mean()
                metric_std = df[z_metric_rename].std()

                ax.text(x=0, y=y_start + .35, s=z_metric_rename,
                        family="avenir next condensed", ha="center", va="center", fontsize=8)

                for index, row in df.iterrows():
                    player_name_row = row["Player"]
                    player_team_row = row["Team"]

                    row_player_metric_value = row[z_metric_rename]
                    player_z_score = (row_player_metric_value - metric_average) / metric_std

                    if player_z_score > 3.3:
                        player_z_score = 3.3
                    elif player_z_score < -3.3:
                        player_z_score = -3.3
                    else:
                        player_z_score = player_z_score

                    if player_name == player_name_row and player_team_row == player_team:
                        z_order = 3
                        s = 150
                        col = "powderblue"
                        edge_color = "black"

                        ax.text(x=player_z_score, y=y_start + .15,
                                s=round(row_player_metric_value, 2),
                                family="avenir next condensed", ha="center", va="center", fontsize=8,
                                bbox=dict(facecolor="powderblue", alpha=1, boxstyle='square,pad=0.2'), zorder=4)

                    else:
                        z_order = 2
                        s = 50
                        col = "lightgrey"
                        edge_color = "none"

                    ax.scatter(x=player_z_score, y=y_start, zorder=z_order, color=col, s=s, edgecolor=edge_color)

                y_start -= 1

            return fig

    @reactive.Calc
    @render.ui()
    def render_player_player_filter():
        """ takes the minimum minutes and the team input and filters the data frame to just midfielders over this threshold"""
        player_search_minute_filter = input_.player_search_minute_filter()

        central_midfielders_df = data_df[
            (data_df["position_group"] == "Central / Defensive Midfielder")
            & (data_df["total_time_minutes"] >= player_search_minute_filter)]

        teams_in_df = sorted(central_midfielders_df["team"].unique().tolist())

        filtered_players_dict = {}

        for t in teams_in_df:
            players_in_team = sorted(
                central_midfielders_df[central_midfielders_df["team"] == t]["player"].unique().tolist())

            players_dict = {}
            for n, p in enumerate(players_in_team):
                players_dict[p] = p

            filtered_players_dict[t] = players_dict

        return ui.input_selectize("player_search_filtered_players", "Player", choices=filtered_players_dict)

    @reactive.Calc
    @render.ui()
    def render_player_player_comparison_filter():
        """ takes the minimum minutes and the team input and filters the data frame to just midfielders over this threshold"""
        player_search_minute_filter = input_.player_search_minute_filter()
        selected_player = input_.player_search_filtered_players()

        central_midfielders_df = data_df[
            (data_df["position_group"] == "Central / Defensive Midfielder")
            & (data_df["total_time_minutes"] >= player_search_minute_filter)]

        teams_in_df = sorted(central_midfielders_df["team"].unique().tolist())

        filtered_players_dict = {"No Comparison": {"No Comparison": "No Comparison"}}

        for t in teams_in_df:
            players_in_team = sorted(
                central_midfielders_df[central_midfielders_df["team"] == t]["player"].unique().tolist())

            players_dict = {}
            for n, p in enumerate(players_in_team):
                if p != selected_player:
                    players_dict[p] = p

            filtered_players_dict[t] = players_dict

        print(filtered_players_dict)

        return ui.input_selectize("player_search_filtered_player_comparison", "Compare with",
                                  choices=filtered_players_dict, selected="No Comparison")

    @reactive.Calc
    @render.ui()
    def render_filtered_player_radar_header():
        player_search_minute_filter = input_.player_search_minute_filter()
        player_search_player_input_filter = input_.player_search_filtered_players()
        player_search_comparison_player_input_filter = input_.player_search_filtered_player_comparison()

        if player_search_comparison_player_input_filter == "No Comparison":
            title_string = (
                f"{player_search_player_input_filter}"
                f"| Compared to Central / Defensive Midfielders "
                f"| Minimum {player_search_minute_filter} Minutes")
        else:
            title_string = (
                f"{player_search_player_input_filter} vs {player_search_comparison_player_input_filter}"
                f"| Compared to Central / Defensive Midfielders "
                f"| Minimum {player_search_minute_filter} Minutes")

        return ui.card_header(title_string)

    @reactive.Calc
    def create_player_radar_fig():
        player_search_minute_filter = input_.player_search_minute_filter()
        player_search_player_input_filter = input_.player_search_filtered_players()

        filtered_df = data_df[
            (data_df["position_group"] == "Central / Defensive Midfielder")
            & (data_df["total_time_minutes"] >= player_search_minute_filter)].copy()

        cmap_list = ["#FEFAF1", "#95b0d1", "#1974b1"]
        cmap = LinearSegmentedColormap.from_list("", cmap_list)

        position_group_metric_list = [i for i in position_metrics_dict["Central / Defensive Midfielder"].keys()]

        for metric_ in position_group_metric_list:
            filtered_df[f"{metric_}_percentile"] = filtered_df[metric_].rank(pct=True, ascending=True)

        filtered_player_row = filtered_df[
            (filtered_df["player"] == player_search_player_input_filter)]

        player_search_comparison_player_input_filter = input_.player_search_filtered_player_comparison()

        if player_search_comparison_player_input_filter != "No Comparison":
            comparison_player_row = filtered_df[
                (filtered_df["player"] == player_search_comparison_player_input_filter)]
        else:
            comparison_player_row = []

        focus_player_team = filtered_player_row["team"].iloc[0]
        player_minutes_played = filtered_player_row["total_time_minutes"].iloc[0]

        # PLAYER RADAR
        fig = plt.figure(figsize=(16, 12), dpi=100)
        gs = gridspec.GridSpec(2, 1, height_ratios=[.15, .85])

        # radar
        ax = fig.add_subplot(gs[1], projection='polar')
        ax.set_facecolor("#FEFAF1")

        ax.set_theta_offset(np.deg2rad(90))
        ax.set_theta_direction(-1)
        ax.spines['polar'].set_edgecolor('black')

        ax.set_yticks([])
        ax.set_xticks([])
        ax.set_yticklabels([])
        ax.set_xticklabels([])

        ax.set_ylim(-0.25, 1)

        indexes = list(range(0, len(position_group_metric_list)))
        width = 2 * np.pi / len(position_group_metric_list)
        angles = [element * width for element in indexes]

        # clear bars for edges - these can overlay everything else
        ax.bar(x=angles, height=1, width=width,
               edgecolor='black', linewidth=1, zorder=5, alpha=1, color="none")

        # Edge Circle
        theta = np.linspace(0, 2 * np.pi, 100)
        r = np.ones(100)

        ax.plot(theta, r * .2, color="#FEFAF1",
                linewidth=.5, alpha=1, zorder=3)
        ax.plot(theta, r * .4, color="#FEFAF1",
                linewidth=.5, alpha=1, zorder=3)
        ax.plot(theta, r * .6, color="#FEFAF1",
                linewidth=.5, alpha=1, zorder=3)
        ax.plot(theta, r * .8, color="#FEFAF1",
                linewidth=.5, alpha=1, zorder=3)

        badge_path = f"national_team_badges/{focus_player_team}.png"
        image = Image.open(badge_path)
        badge_image_array = np.array(image)
        zoom_ref = .08
        team_imagebox = OffsetImage(badge_image_array, zoom=zoom_ref)
        team_ab = AnnotationBbox(team_imagebox, (0, -0.25), xycoords='data', frameon=False)
        ax.add_artist(team_ab)

        # adding player percentiles
        for n, m in enumerate(position_group_metric_list):
            player_percentile = filtered_player_row[m + "_percentile"].iloc[0]

            angle_r = angles[n]

            bar_color = cmap(player_percentile)

            if player_search_comparison_player_input_filter != "No Comparison":
                comparison_percentile = comparison_player_row[m + "_percentile"].iloc[0]
                if player_percentile > comparison_percentile:
                    start_point = comparison_percentile
                    end_point = player_percentile
                    adjusted_end_point = end_point - start_point  # need to reduce length of the bar as it is starting at the average
                    bar_col = "#1974b1"
                    line_col = "#74cff5"
                else:
                    start_point = player_percentile
                    end_point = comparison_percentile
                    adjusted_end_point = end_point - start_point  # need to reduce length of the bar as it is starting at the average
                    bar_col = "#b14941"
                    line_col = "#d17a69"
            else:
                start_point = 0
                end_point = player_percentile
                adjusted_end_point = end_point - start_point  # need to reduce length of the bar as it is starting at the average
                bar_col = "#1974b1"
                line_col = "#74cff5"

            ax.bar(x=angle_r,
                   height=adjusted_end_point,
                   bottom=start_point,
                   width=width,
                   edgecolor=line_col, linewidth=1, zorder=2, alpha=1, color=bar_col)

        for angle, metric_name in zip(angles, position_group_metric_list):
            rotation_angle = np.degrees(-angle)
            metric_rename_ = position_metrics_dict["Central / Defensive Midfielder"][metric_name]["rename"]
            player_percentile = filtered_player_row[metric_name + "_percentile"].iloc[0]
            player_value = filtered_player_row[metric_name].iloc[0]
            player_value = round(player_value, 2)

            if metric_name in ["difference_to_expected_pass_completion_ratio"]:
                if player_value > 0:
                    sig = "+"
                else:
                    sig = ""
                player_value = f"{sig}{int(round(player_value * 100))}%"
            elif metric_name in ["ball_retention_under_pressure"]:
                player_value = f"{int(round(player_value * 100))}%"

            if 90 < np.degrees(angle) < 270:
                rotation_angle -= 180
                v_position = "top"
            else:
                rotation_angle -= 0
                v_position = "bottom"

            ax.text(angle, 1.04, metric_rename_.upper(),
                    ha='center', va=v_position,
                    rotation=rotation_angle, rotation_mode='anchor', fontsize=8, color="black",
                    family='avenir next condensed',
                    zorder=8,
                    path_effects=[path_effects.Stroke(linewidth=2, foreground="#fefaf1", alpha=1),
                                  path_effects.Normal()])

            ax.text(angle, player_percentile, f"{player_value}",
                    ha='center', va="center",
                    rotation=rotation_angle, rotation_mode='anchor', fontsize=8,
                    family='avenir next condensed', color="black",
                    zorder=7,
                    bbox=dict(facecolor="#FEFAF1", alpha=1, boxstyle='round,pad=0.2'))

        if player_search_comparison_player_input_filter != "No Comparison":
            ax.bar(x=-100, bottom=-50, height=0,
                   edgecolor='#74cff5', linewidth=1, zorder=5,
                   alpha=1, color="#1974b1", hatch="///",
                   label=f"Above {player_search_comparison_player_input_filter}".upper())

            ax.bar(x=-100, bottom=-50, height=0,
                   edgecolor='#d17a69', linewidth=1, zorder=5,
                   alpha=1, color="#b14941", hatch="///",
                   label=f"Below {player_search_comparison_player_input_filter}".upper())

        else:
            ax.bar(x=-100, bottom=-50, height=0,
                   edgecolor='#74cff5', linewidth=1, zorder=5,
                   alpha=1, color="#1974b1", hatch="///",
                   label=f"{player_search_player_input_filter} Percentiles".upper())

        legend_x = 0.25
        legend_len = 0.5
        legend_cols = 1

        ax.legend(bbox_to_anchor=(legend_x, -0.4, legend_len, 0.5),
                  loc='center', frameon=False, ncols=legend_cols, labelcolor='black',
                  mode='expand', borderaxespad=1, handlelength=2, handleheight=1, handletextpad=.7,
                  prop={"family": "avenir next condensed", "size": 8})

        # title text
        text_ax = fig.add_subplot(gs[0])
        text_ax.spines['right'].set_visible(False)
        text_ax.spines['bottom'].set_visible(False)
        text_ax.spines['top'].set_visible(False)
        text_ax.spines['left'].set_visible(False)

        text_ax.yaxis.set_ticks([])
        text_ax.xaxis.set_ticks([])

        player_team_title = f"{player_search_player_input_filter} - {focus_player_team}"
        text_ax.text(x=.5, y=.95, s=player_team_title.upper(),
                     ha="center", va="center",
                     family="avenir next condensed", fontsize=20)

        league_minutes_title = f"Minutes {int(player_minutes_played)}"
        text_ax.text(x=.5, y=.7, s=league_minutes_title.upper(),
                     ha="center", va="center",
                     family="avenir", fontsize=12)

        if player_search_comparison_player_input_filter == "No Comparison":
            middle_line_raw = f"percentiles playing as a Central / Defensive Midfielder"
        else:
            middle_line_raw = f"comparison to {player_search_comparison_player_input_filter} playing as a Central / Defensive Midfielder"

        text_ax.text(x=.5, y=.45, s=middle_line_raw.upper(),
                     ha="center", va="center",
                     family="avenir next condensed", fontsize=12)

        minute_threshold_title = f"min {player_search_minute_filter} minutes"
        text_ax.text(x=.5, y=.2, s=minute_threshold_title.upper(),
                     ha="center", va="center",
                     family="avenir", fontsize=10)

        # percentile_text = f"--- 25th & 75th percentile ---"
        # text_ax.text(x=.5, y=.1, s=percentile_text.upper(),
        #              ha="center", va="center",
        #              family="avenir", fontsize=8)

        return fig

    @reactive.Calc
    @render.plot
    def render_player_radar():
        plot = create_player_radar_fig()
        return plot

    @reactive.Calc
    def create_download_file_name():
        player_name_filter = input_.player_search_filtered_players()
        comparison_player = input_.player_search_filtered_player_comparison()

        player_name_renamed = player_name_filter.replace(' ', '_')
        if comparison_player == "No Comparison":
            comparison_renamed = comparison_player.replace(' ', '_')
            plot_download_title = f"{player_name_renamed}_vs_{comparison_renamed}.png"
        else:
            plot_download_title = f"{player_name_renamed}.png"

        return plot_download_title

    @render.download(filename=create_download_file_name)
    def download_player_radar():
        plot = create_player_radar_fig()
        with io.BytesIO() as buf:
            plot.savefig(buf, format="png", dpi=500, bbox_inches='tight', pad_inches=0.1)
            yield buf.getvalue()


app = App(app_ui, server)
