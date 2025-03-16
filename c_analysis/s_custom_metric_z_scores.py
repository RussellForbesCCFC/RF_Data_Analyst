import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from highlight_text import ax_text
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)

from helpers.position_group_metrics import position_metrics_dict, profile_metrics_dict


def single_metric_player_z_scores(focus_player_id, metric_name, profile, position_group, min_minutes):
    player_df = pd.read_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/b_aggregated_data/player_aggregated_data.csv")

    player_df = player_df[
        (player_df["total_time_minutes"] >= min_minutes)
        & (player_df["position_group"] == position_group)]

    print(player_df.head().to_string())

    focus_player_name = player_df[player_df["player_id"] == focus_player_id]["player"].iloc[0]

    fig = plt.figure(figsize=(10, 3), dpi=150)
    ax = fig.add_subplot()

    ax.set_xlim(-4, 4)
    ax.set_ylim(-.5, .5)

    ax.yaxis.set_ticks([])
    ax.xaxis.set_ticks([])

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # plot 0 line
    ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [0, 0],
            color="black", lw=.5, alpha=.75, zorder=1)

    # plot 0 average line
    ax.plot([0, 0], [-0.5, .5],
            color="black", lw=.5, alpha=.75, zorder=1, ls='--')

    metric_average = player_df[metric_name].mean()
    metric_std = player_df[metric_name].std()

    player_df[f"{metric_name}_rank"] = player_df[metric_name].rank(ascending=False)
    for index, row in player_df.iterrows():
        player_metric_value = row[metric_name]
        player_z_score = (player_metric_value - metric_average) / metric_std
        player_id = row["player_id"]
        player_rank = row[f"{metric_name}_rank"]

        if player_id == focus_player_id:
            z_ref = 5
            size_ref = 1000
            alpha_ref = 1
            color_ref = "powderblue"

            if metric_name in ["open_play_forward_pass_percentage"]:
                player_metric_value = int(round(player_metric_value * 100))
                sym = "%"
            else:
                player_metric_value = round(player_metric_value, 2)
                sym = ""

            player_text = (f"{focus_player_name}\n"
                           f"{player_metric_value}{sym}\n"
                           f"{int(player_rank)} / {player_df.shape[0]} Players")

            ax.text(x=player_z_score, y=0 - 0.125,
                    s=player_text, ha="center", va="top", zorder=5,
                    bbox=dict(facecolor=color_ref, alpha=1, boxstyle='round,pad=0.2'),
                    family="avenir next condensed", fontsize=16)

        else:
            z_ref = 3
            size_ref = 400
            alpha_ref = 0.8
            color_ref = "lightgrey"

        ax.scatter(x=player_z_score, y=0, s=size_ref,
                   color=color_ref, edgecolor="black", lw=.5, zorder=z_ref, alpha=alpha_ref)

    fig.text(x=0.5, y=.85, s=f"{metric_name.replace('_', ' ')} - {position_group.replace('_', ' ')}".upper(),
             ha="center", va="center",
             family="avenir next condensed", color="black",
             fontsize=22)

    fig.set_facecolor("none")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_single_metric_z_scores_{focus_player_name}_{metric_name}",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=True)

    plt.close()


single_metric_player_z_scores(6655, "ball_recoveries_per_90", "box_to_box",
                              "Central / Defensive Midfielder",
                              300)

# metrics entered
# all_touches_per_90
# progressive_passes_per_90
# open play forward pass percentage
# progressive_carries_per_90
# progressive_carries_from_own_half_per_90
