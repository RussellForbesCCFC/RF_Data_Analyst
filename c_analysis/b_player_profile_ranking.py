import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import requests
from PIL import Image
from io import BytesIO
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)
from matplotlib.colors import LinearSegmentedColormap

from helpers.position_group_metrics import profile_metrics_dict


def add_player_z_score(row, metric, df, weightings_dict):
    metric_weight = weightings_dict[metric]
    player_value = row[metric]
    metric_average = df[metric].mean()
    metric_std = df[metric].std()

    player_std_from_mean = (player_value - metric_average) / metric_std
    weighted_std_from_mean = player_std_from_mean * metric_weight

    return weighted_std_from_mean


def scale_weighted_average(row, df):
    player_z_weighted_average = row["z_score_weighted_average"]
    max_z_weighted = df["z_score_weighted_average"].max()
    min_z_weighted = df["z_score_weighted_average"].min()
    scaled_z_score = (player_z_weighted_average - min_z_weighted) / (max_z_weighted - min_z_weighted)
    return scaled_z_score


# def filter_if_player_above_all_z_scores(z_score_list, row, min_value):
#     over_z_score_counter = 0
#     for met in z_score_list:
#         player_z_score_value = row[met]
#         if player_z_score_value < min_value:
#             over_z_score_counter += 1
#
#     return over_z_score_counter
#
#
# def filter_if_player_above_all_percentiles(percentile_list, row, min_value):
#     percentile_under_min_value_counter = 0
#     for met in percentile_list:
#         player_z_score_value = row[met]
#         if player_z_score_value < min_value:
#             percentile_under_min_value_counter += 1
#
#     if percentile_under_min_value_counter == 0:
#         return True
#     else:
#         return False


def calculate_profile_ranks(profile, position_group, min_minutes):
    positive_cmap_list = ["#FEFAF1", "#9cb7d8", "#1974b1"]
    positive_cmap = LinearSegmentedColormap.from_list("", positive_cmap_list)

    data_df = pd.read_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/b_aggregated_data/player_aggregated_data.csv")

    data_df = data_df[
        (data_df["total_time_minutes"] >= min_minutes)
        & (data_df["position_group"] == position_group)]

    position_group_metrics_as_list = [i for i in profile_metrics_dict[profile].keys()]
    metric_weightings = {}
    for p_m in position_group_metrics_as_list:
        weight = profile_metrics_dict[profile][p_m]["weight"]
        metric_weightings[p_m] = weight

    # adding percentiles and z-scores
    metric_z_score_names_weighted = []
    # metric_z_score_names_scaled = []
    # metric_percentile_names = []
    for met in position_group_metrics_as_list:
        # data_df[f"{met}_percentile"] = data_df[met].rank(pct=True, ascending=True)
        data_df[f"{met}_z_score_weighted"] = data_df.apply(
            lambda _row: add_player_z_score(_row, met, data_df, metric_weightings), axis=1)

        # metric_percentile_names.append(f"{met}_percentile")
        metric_z_score_names_weighted.append(f"{met}_z_score_weighted")
        # metric_z_score_names_scaled.append(f"{met}_z_score_scaled")

    data_df["z_score_weighted_average"] = data_df[metric_z_score_names_weighted].mean(axis=1)
    data_df["z_score_weighted_average_scaled"] = data_df.apply(lambda row_: scale_weighted_average(row_, data_df),
                                                               axis=1)

    # average z score
    ranked_players = data_df.sort_values("z_score_weighted_average", ascending=False).head(10)

    # create table of players
    fig = plt.figure(figsize=(16, 16), dpi=100)
    ax = fig.add_subplot()

    metric_count = len(metric_z_score_names_weighted)
    x_lim = metric_count + 3.6

    ax.set_xlim(-0.1, x_lim)
    ax.set_ylim(-0.1, 11.1)

    ax.yaxis.set_ticks([])
    ax.xaxis.set_ticks([])

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # top horizontal line
    ax.plot([ax.get_xlim()[0] + 0.1, ax.get_xlim()[1] - 0.1],
            [ax.get_ylim()[1] - 0.1, ax.get_ylim()[1] - 0.1], color='black')

    # bottom horizontal line
    ax.plot([ax.get_xlim()[0] + 0.1, ax.get_xlim()[1] - 0.1],
            [ax.get_ylim()[0] + 0.1, ax.get_ylim()[0] + 0.1], color='black')

    # left vertical line
    ax.plot([ax.get_xlim()[0] + 0.1, ax.get_xlim()[0] + 0.1],
            [ax.get_ylim()[0] + 0.1, ax.get_ylim()[1] - 0.1], color='black')

    # right vertical line
    ax.plot([ax.get_xlim()[1] - 0.1, ax.get_xlim()[1] - 0.1],
            [ax.get_ylim()[0] + 0.1, ax.get_ylim()[1] - 0.1], color='black')

    # adding column names to the table

    x_start = 1
    col_title_y_location = ax.get_ylim()[1] - 0.6

    column_title_names = position_group_metrics_as_list.copy()
    # column_title_names.insert(0, "team")
    column_title_names.insert(0, "player")
    column_title_names.append("z_score_weighted_average_scaled")
    column_title_names.append("total_obv_net_per_90")

    additional_renames = {"player": "Player\nName",
                          "team": "Team",
                          "z_score_weighted_average_scaled": f"Profile %\n{profile.replace('_', ' ')}",
                          "total_obv_net_per_90": "On Ball\nValue"}

    # add vertical line to right of column name
    ax.plot([x_start - .5, x_start - .5],
            [ax.get_ylim()[0] + 0.1, ax.get_ylim()[1] - 1.1], color='black', alpha=.5)

    for met_name in column_title_names:
        if met_name in position_group_metrics_as_list:
            metric_rename = profile_metrics_dict[profile][met_name]["rename"]
            metric_weight = f"Weight: {metric_weightings[met_name]}"

        else:
            metric_rename = additional_renames[met_name]
            metric_weight = ""

        ax.text(x=x_start, y=col_title_y_location,
                s=metric_rename.upper(),
                ha="center", va="center",
                family="avenir next condensed",
                fontsize=13)

        ax.text(x=x_start, y=col_title_y_location - 0.25,
                s=metric_weight.upper(),
                ha="center", va="center",
                family="avenir",
                fontsize=7)

        # add vertical line to right of column name
        ax.plot([x_start + .5, x_start + .5],
                [ax.get_ylim()[0] + 0.1, ax.get_ylim()[1] - 1.1], color='black', alpha=.5)

        x_start += 1

    # title column line
    ax.plot([ax.get_xlim()[0] + 0.1, ax.get_xlim()[1] - 0.1],
            [ax.get_ylim()[1] - 1.1, ax.get_ylim()[1] - 1.1], color='black')

    # looping ranked players df and adding player and their data
    data_start_y_location = ax.get_ylim()[1] - 1.6
    for index, row in ranked_players.iterrows():
        # add in horizontal line under each row
        ax.plot([ax.get_xlim()[0] + 0.1, ax.get_xlim()[1] - 0.1],
                [data_start_y_location - .5, data_start_y_location - .5],
                color='black', ls="--")

        # in each row loop each metric
        data_x_start = 1
        for met_name in column_title_names:
            row_data_value = row[met_name]
            if met_name in ["player"]:
                name_characters = len(row_data_value)
                if name_characters >= 20:
                    fs = 12
                else:
                    fs = 14

                player_name_split = row_data_value.split(" ")
                player_name_joined = "\n".join(player_name_split)
                data_string = player_name_joined.upper()

                team_name = row["team"]
                badge_path = f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/e_media/national_team_badges/{team_name}.png"
                image = Image.open(badge_path)
                badge_image_array = np.array(image)
                zoom_ref = .075
                h_imagebox = OffsetImage(badge_image_array, zoom=zoom_ref)
                ab = AnnotationBbox(h_imagebox, (data_x_start - 0.75,
                                                 data_start_y_location), xycoords='data',
                                    frameon=False)
                ax.add_artist(ab)

            elif met_name in ["z_score_weighted_average_scaled"]:
                data_string = f"{round(row_data_value * 100, 1)}%"
                fs = 16

            elif met_name in ["tackles_and_interceptions_per_90", "ball_recoveries_per_90"]:
                data_string = round(row_data_value, 1)
                fs = 16
            else:
                data_string = round(row_data_value, 2)
                fs = 16

            ax.text(x=data_x_start, y=data_start_y_location,
                    s=data_string,
                    ha="center", va="center",
                    family="avenir next condensed",
                    fontsize=fs)

            # color filling
            if met_name != "player":
                value_max = data_df[met_name].max()
                value_min = data_df[met_name].min()
                value_as_per_in_range = (row_data_value - value_min) / (value_max - value_min)
                color = positive_cmap(value_as_per_in_range)

                ax.fill_between([data_x_start - .5, data_x_start + .5],
                                data_start_y_location - 0.5,
                                data_start_y_location + 0.5,
                                linewidth=0,
                                color=color,
                                alpha=.4, zorder=1)

            data_x_start += 1
        data_start_y_location -= 1

    # FIGURE TEXT AND SAVE

    fig.text(x=.5125, y=.9, s=f"{profile.replace('_', ' ')} - Top Ranked Players".upper(),
             color="black",
             family="avenir next condensed",
             fontsize=26, ha="center", va="center")

    fig.text(x=.5125, y=.885, s=f"Minimum {min_minutes} Minutes | Values per 90".upper(),
             color="black",
             family="avenir",
             fontsize=14, ha="center", va="center")

    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/top_ranked_players.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


calculate_profile_ranks("box_to_box", "Central / Defensive Midfielder", 300)
