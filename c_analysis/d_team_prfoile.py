import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)

from helpers.helper_functions import get_start_locations, get_pass_end_locations


def player_team_z_scores(focus_player_id):
    # read and combine raw data
    euro_events_df = pd.read_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/a_raw_data/euro_2024_task_data.csv",
        low_memory=False)
    euro_events_df["competition_name"] = "Euro 2024"

    copa_events_df = pd.read_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/a_raw_data/copa_2024_task_data.csv",
        low_memory=False)
    copa_events_df["competition_name"] = "Copa 2024"

    player_events_df = pd.concat([euro_events_df, copa_events_df], ignore_index=True)

    focus_player_events = player_events_df[
        (player_events_df["player_id"] == focus_player_id)]

    focus_player_team = focus_player_events["team"].iloc[0]

    # remove penalty shootouts
    player_events_df = player_events_df[player_events_df["period"] != 5]

    # add opposition team column
    event_match_ids = player_events_df["match_id"].unique().tolist()
    match_id_team_dict_list = []
    for match_id_reference in event_match_ids:
        teams_in_match_id = player_events_df[player_events_df["match_id"] == match_id_reference][
            "team"].unique().tolist()
        match_id_team_dict = {"match_id": match_id_reference, "team_one": teams_in_match_id[0],
                              "team_two": teams_in_match_id[1]}
        match_id_team_dict_list.append(match_id_team_dict)

    match_team_info_df = pd.DataFrame(match_id_team_dict_list)

    player_events_df = player_events_df.merge(match_team_info_df, on="match_id", how="left")

    player_events_df["opposition_team"] = np.where(
        player_events_df["team"] == player_events_df["team_one"],
        player_events_df["team_two"], player_events_df["team_one"])

    # create basic team data stats per game
    # get team matches played counts
    team_match_counts = player_events_df[
        (player_events_df["type"] == "Starting XI")]["team"].value_counts().rename(
        "matches_played")

    # create team data -------------------------------------------------------------------------------------------------
    team_xg_created = player_events_df[(player_events_df["shot_type"] != "Penalty")].groupby(
        "team")["shot_statsbomb_xg"].sum().rename("xg_created")

    team_xg_conceded = player_events_df[player_events_df["shot_type"] != "Penalty"].groupby(
        "opposition_team")["shot_statsbomb_xg"].sum().rename("xg_conceded")

    team_passes_made = player_events_df[
        (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Pass Offside")]["team"].value_counts().rename(
        "passes_made")

    team_short_passes_made = player_events_df[
        (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Pass Offside")
        & (player_events_df["pass_length"] <= 10)]["team"].value_counts().rename(
        "short_passes_made")

    team_long_passes_made = player_events_df[
        (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Pass Offside")
        & (player_events_df["pass_length"] >= 35)]["team"].value_counts().rename(
        "long_passes_made")

    team_unpressured_long_passes_made = player_events_df[
        (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Pass Offside")
        & (player_events_df["pass_length"] >= 35)
        & (player_events_df["under_pressure"].isnull())]["team"].value_counts().rename(
        "unpressured_long_passes_made")

    team_opposition_passes_made = player_events_df[
        (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Pass Offside")]["opposition_team"].value_counts().rename(
        "opposition_passes")

    pressure_events_df = player_events_df[player_events_df['type'] == "Pressure"].copy()

    pressure_events_df[['location_x', 'location_y']] = pressure_events_df.apply(
        lambda row_: pd.Series(get_start_locations(row_)), axis=1)

    team_pressures = pressure_events_df[
        (pressure_events_df['type'] == "Pressure")]["team"].value_counts().rename("pressures")

    team_pressures_opp_forty_per = pressure_events_df[
        (pressure_events_df['type'] == "Pressure")
        & (pressure_events_df['location_x'] >= 72)]["team"].value_counts().rename("pressures_opp_40")

    defensive_actions_df = player_events_df[
        ((player_events_df['type'] == "Duel")
         & (player_events_df['duel_type'] == "Tackle"))
        | ((player_events_df['type'] == "Foul Committed")
           & (player_events_df['foul_committed_offensive'].isnull()))
        | (player_events_df['type'] == "Pressure")
        | (player_events_df['type'] == "Block")
        | (player_events_df["type"] == "Dribbled Past")
        | (player_events_df["type"] == "Interception")
        | (player_events_df["pass_type"] == "Interception")]

    defensive_actions_df = defensive_actions_df.copy()
    defensive_actions_df[['location_x', 'location_y']] = defensive_actions_df.apply(
        lambda row_: pd.Series(get_start_locations(row_)), axis=1)

    team_defensive_action_height = defensive_actions_df.groupby(
        ['team'])[
        'location_x'].mean().rename('defensive_action_height').fillna(0)

    # workings for 10+ pass sequences
    all_pass_events = player_events_df[
        (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Pass Offside")].copy()

    all_pass_events["team_pass_count_in_possession"] = all_pass_events.groupby(
        ["match_id", "team", "possession"]).cumcount() + 1

    all_pass_events["tenth_pass_in_sequence"] = all_pass_events["team_pass_count_in_possession"] == 10

    team_ten_pass_sequences = all_pass_events[
        (all_pass_events["tenth_pass_in_sequence"] == True)]["team"].value_counts().rename("10_plus_pass_sequences")

    # box cross %
    all_pass_events[['location_x', 'location_y']] = all_pass_events.apply(
        lambda row_: pd.Series(get_start_locations(row_)), axis=1)

    all_pass_events[['end_location_x', 'end_location_y']] = all_pass_events.apply(
        lambda row_: pd.Series(get_pass_end_locations(row_)), axis=1)

    all_passes_into_box = all_pass_events[
        (all_pass_events['pass_type'] != "Corner") &
        (all_pass_events['pass_outcome'] != 'Pass Offside')
        & ~((all_pass_events['location_x'] >= 102)
            & (all_pass_events['location_y'] <= 62)
            & (all_pass_events['location_y'] >= 18))
        & ((all_pass_events['end_location_x'] >= 102)
           & (all_pass_events['end_location_y'] <= 62)
           & (all_pass_events['end_location_y'] >= 18))]

    team_passes_into_box = all_passes_into_box["team"].value_counts().rename("all_passes_into_box")

    crosses_into_box = all_passes_into_box[all_passes_into_box["pass_cross"] == True]

    team_crosses_into_box = crosses_into_box["team"].value_counts().rename("crosses_into_box")

    # combine dataframes
    team_stats_df = pd.concat(
        [team_match_counts,
         team_xg_created, team_xg_conceded,
         team_passes_made, team_opposition_passes_made,
         team_short_passes_made, team_long_passes_made,
         team_unpressured_long_passes_made, team_ten_pass_sequences,
         team_passes_into_box, team_crosses_into_box,
         team_pressures, team_pressures_opp_forty_per,
         team_defensive_action_height], axis=1)

    team_stats_df["possession"] = team_stats_df["passes_made"] / team_stats_df[
        ["passes_made", "opposition_passes"]].sum(axis=1)

    team_stats_df["per_passes_into_box_cross"] = (
            team_stats_df["crosses_into_box"] /
            team_stats_df["all_passes_into_box"])

    # team z-scores figure
    z_score_metrics_dict = {
        "xg_created": "Expected\nGoals",
        "xg_conceded": "Expected\nGoals\nConceded",
        "passes_made": "Passes",
        "possession": "Possession %",
        "10_plus_pass_sequences": "10+ Pass\nSequences",
        "unpressured_long_passes_made": "Unpressured\nLong Balls",
        "per_passes_into_box_cross": "Box Cross %",
        "pressures_opp_40": "Pressures\nOpp 40",
        "defensive_action_height": "Def Action\n Height"}

    z_score_metrics = [i for i in z_score_metrics_dict.keys()]

    for metric in z_score_metrics:
        team_stats_df[f"{metric}_per_game"] = team_stats_df[metric] / team_stats_df["matches_played"]

    team_stats_df.reset_index(inplace=True)

    # FIGURE
    fig = plt.figure(figsize=(18, 4), dpi=150)
    ax = fig.add_subplot()

    ax.set_xlim(0, len(z_score_metrics) + .1)
    ax.set_ylim(-4, 4)

    ax.yaxis.set_ticks([])
    ax.xaxis.set_ticks([])

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # plot 0 line
    ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [0, 0],
            color="black", lw=.5, alpha=.75, zorder=1)

    # plot each metric and teams z-score
    x_start = 0.5
    for z_metric in z_score_metrics:
        # add title
        if z_metric in ["xg_conceded", "per_passes_into_box_cross"]:
            metric_rename = f"{z_score_metrics_dict[z_metric]}*"
        else:
            metric_rename = f"{z_score_metrics_dict[z_metric]}"

        ax.text(x=x_start, y=ax.get_ylim()[1] - 0.1, s=metric_rename.upper(),
                ha="center", va="top", family="avenir next condensed", fontsize=14)

        if z_metric in ["xg_created", "xg_conceded", "passes_made",
                        "10_plus_pass_sequences", "unpressured_long_passes_made", "pressures_opp_40"]:
            z_metric_col_name = f"{z_metric}_per_game"
        else:
            z_metric_col_name = z_metric

        z_metric_average = team_stats_df[z_metric_col_name].mean()
        z_metric_std = team_stats_df[z_metric_col_name].std()

        for index, row in team_stats_df.iterrows():
            team_name = row["index"]
            team_metric = row[z_metric_col_name]
            team_z_score = (team_metric - z_metric_average) / z_metric_std

            # reverse z-score of selected metrics so higher always better
            if z_metric in ["xg_conceded", "per_passes_into_box_cross"]:
                team_z_score = team_z_score * -1
            else:
                team_z_score = team_z_score

            if team_name == focus_player_team:
                badge_path = f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/e_media/national_team_badges/{team_name}.png"
                image = Image.open(badge_path)
                badge_image_array = np.array(image)
                zoom_ref = .05
                h_imagebox = OffsetImage(badge_image_array, zoom=zoom_ref)
                ab = AnnotationBbox(
                    h_imagebox, (x_start, team_z_score), xycoords='data', frameon=False)
                ax.add_artist(ab)

                # add team value at the bottom

                if z_metric in ["per_passes_into_box_cross", "possession"]:
                    metric_ann = f"{round(team_metric * 100, 1)}%"
                else:
                    metric_ann = round(team_metric, 2)
                ax.text(x=x_start, y=team_z_score - 0.75,
                        s=metric_ann, ha="center", va="center", zorder=5,
                        bbox=dict(facecolor="#FEFAF1", alpha=1, boxstyle='round,pad=0.2'),
                        family="avenir next condensed", fontsize=14,
                        )

            else:
                ax.scatter(x=x_start, y=team_z_score, s=100,
                           color="lightgrey", edgecolor="black", lw=.5, zorder=2, alpha=.6)

        x_start += 1

    fig.text(x=.5125, y=.99, s=f"Team Overview".upper(),
             color="black",
             family="avenir next condensed",
             fontsize=26, ha="center", va="center")

    fig.text(x=.5125, y=.92,
             s=f"Values per Game of {focus_player_team} Compared to Teams in Euro 2024 and Copa America 2024".upper(),
             color="black",
             family="avenir",
             fontsize=12, ha="center", va="center")

    fig.text(x=.5125, y=.1,
             s=f"* Indicates where metric is reversed".upper(),
             color="black",
             family="avenir",
             fontsize=12, ha="center", va="center")

    ax.set_facecolor("#FEFAF1")
    fig.set_facecolor("None")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_team_profile_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=True)

    plt.close()


player_team_z_scores(6655)
