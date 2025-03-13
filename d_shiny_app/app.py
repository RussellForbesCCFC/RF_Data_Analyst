import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from shiny import App, render, ui, reactive
import pandas as pd
from shiny.express.ui import card_header

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
        {"name": "open_play_xga_per_90", "weight": 1}]}

profile_list = [i for i in profile_dictionaries.keys()]
profile_list.insert(0, "None")

metrics_dict = {"None": "None",
                # 'total_obv_net_per_90': "Obv",
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
app_ui = ui.page_fillable(
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
        col_widths=[2, 7, 3]))


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

        return ui.input_selectize("metric_one_selector", "Metric 1", custom_metrics_list, selected=default_value),

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
            fig = plt.figure(figsize=(20, 10), dpi=100)

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
                        family="avenir next condensed", ha="center", va="center", fontsize=12)

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


app = App(app_ui, server)

# app.run()
