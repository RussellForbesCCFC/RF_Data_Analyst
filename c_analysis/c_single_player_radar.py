import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from highlight_text import ax_text
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)

from helpers.position_group_metrics import position_metrics_dict, profile_metrics_dict


def create_player_radar(focus_player_id, profile, position_group, min_minutes):
    """
    a function to create a player radar based on the position group with metrics within a profile highlighted
    :param focus_player_id:
    :param profile:
    :param position_group:
    :param min_minutes:
    :return: a matplotlib player radar
    """
    cmap_list = ["#FEFAF1", "#95b0d1", "#1974b1"]
    cmap = LinearSegmentedColormap.from_list("", cmap_list)

    player_df = pd.read_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/b_aggregated_data/player_aggregated_data.csv")

    player_df = player_df[
        (player_df["total_time_minutes"] >= min_minutes)
        & (player_df["position_group"] == position_group)]

    position_group_metric_list = [i for i in position_metrics_dict[position_group].keys()]

    for metric_ in position_group_metric_list:
        player_df[f"{metric_}_percentile"] = player_df[metric_].rank(pct=True, ascending=True)

    filtered_player_row = player_df[
        (player_df["player_id"] == focus_player_id)]

    player_name = filtered_player_row["player"].iloc[0]
    player_team = filtered_player_row["team"].iloc[0]
    player_minutes = filtered_player_row["total_time_minutes"].iloc[0]

    profile_metrics = [i for i in profile_metrics_dict[profile].keys()]

    # PLAYER RADAR
    fig = plt.figure(figsize=(10, 10), dpi=100)

    ax = fig.add_subplot(projection='polar')
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

    fs = 25
    props = [{"fontsize": fs - 6},
             {"family": "avenir", "fontsize": fs - 12}]

    player_title = (f"{player_name} | {player_team}"
                    f"\n{position_group}\n"
                    f"<Minutes in Position {int(round(player_minutes))}>\n"
                    f"<Compared to all {position_group}s with over {min_minutes} Minutes>")

    ax_text(0, 1.25, s=player_title.upper(),
            family="avenir next condensed", textalign="center", vsep=4,
            highlight_textprops=props, color="black",
            ha="center", va="bottom", fontsize=fs, ax=ax)

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

    badge_path = f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/e_media/national_team_badges/{player_team}.png"
    image = Image.open(badge_path)
    badge_image_array = np.array(image)
    zoom_ref = .15
    team_imagebox = OffsetImage(badge_image_array, zoom=zoom_ref)
    team_ab = AnnotationBbox(team_imagebox, (0, -0.25), xycoords='data', frameon=False)
    ax.add_artist(team_ab)

    # adding player percentiles
    for n, m in enumerate(position_group_metric_list):
        player_percentile = filtered_player_row[m + "_percentile"].iloc[0]

        angle_r = angles[n]

        bar_color = cmap(player_percentile)

        ax.bar(x=angle_r,
               height=player_percentile,
               width=width,  # hatch="////",
               edgecolor="black", linewidth=1, zorder=2, alpha=1, color=bar_color)

    for angle, metric_name in zip(angles, position_group_metric_list):
        rotation_angle = np.degrees(-angle)
        metric_rename = position_metrics_dict[position_group][metric_name]["rename"]
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

        if metric_name in profile_metrics:
            col = "orange"
            pe_col = "black"
        else:
            col = "black"
            pe_col = "#FEFAF1"

        ax.text(angle, 1.04, metric_rename.upper(),
                ha='center', va=v_position,
                rotation=rotation_angle, rotation_mode='anchor', fontsize=16, color=col,
                family='avenir next condensed',
                zorder=8,
                path_effects=[path_effects.Stroke(linewidth=2, foreground=pe_col, alpha=1),
                              path_effects.Normal()])

        ax.text(angle, player_percentile, f"{player_value}",
                ha='center', va="center",
                rotation=rotation_angle, rotation_mode='anchor', fontsize=16,
                family='avenir next condensed', color="black",
                zorder=7,
                bbox=dict(facecolor="#FEFAF1", alpha=1, boxstyle='round,pad=0.2'))

    fig.text(x=0.5, y=0, s=f"Metrics in the {profile.replace('_', ' ')} Profile".upper(), ha="center", va="center",
             family="avenir next condensed", color="orange",
             fontsize=22,
             bbox=dict(facecolor="#fefaf1", alpha=.5, boxstyle='round,pad=0.2'),
             path_effects=[path_effects.Stroke(linewidth=2, foreground="black", alpha=1),
                           path_effects.Normal()])

    fig.set_facecolor("none")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_radar_{player_name}_{profile}_radar.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


create_player_radar(6655, "box_to_box", "Central / Defensive Midfielder", 300)
