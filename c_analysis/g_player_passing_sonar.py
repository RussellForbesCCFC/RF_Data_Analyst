import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib
import matplotlib.patheffects as path_effects
from matplotlib import gridspec
from matplotlib.colors import Normalize
import matplotlib.cm as cm

from helpers.helper_dictionaries import position_groups
from helpers.helper_functions import get_start_locations, get_carry_end_locations, get_pass_end_locations, \
    calculate_action_distance


def create_player_passing_sonar(focus_player_id):
    """
    create pass sonars
    length will be median pass distance in that direction
    color will represent number of passes
    :param focus_player_id:
    :return:
    """
    cmap_list = ["#FEFAF1", "#95b0d1", "#1974b1"]
    cmap = LinearSegmentedColormap.from_list("", cmap_list)
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

    # print(player_events_df[player_events_df["team"] == "Spain"][["player", "player_id"]].value_counts().to_string())
    focus_player_open_play_pass_events_df = player_events_df[
        (player_events_df["player_id"] == focus_player_id)
        & (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Offside")
        & ~(player_events_df["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))].copy()

    # focus_player_open_play_pass_events_df["pass_angle_degrees"] = (
    #     focus_player_open_play_pass_events_df[
    #         "pass_angle"].apply(lambda x: np.degrees(-x)))

    focus_player_name = focus_player_open_play_pass_events_df["player"].iloc[0]
    focus_player_open_play_pass_counts = focus_player_open_play_pass_events_df.shape[0]

    print(focus_player_open_play_pass_events_df.head().to_string())

    # player passing sonar
    fig = plt.figure(figsize=(14, 15), dpi=150)
    ax_gs = gridspec.GridSpec(2, 1, height_ratios=[.95, .05], hspace=0.1)
    ax_cbar = gridspec.GridSpec(2, 3, height_ratios=[.95, .05], width_ratios=[0.05, 0.9, 0.05], hspace=0.1)
    ax = fig.add_subplot(ax_gs[0], projection="polar")
    title_text_color = "black"

    ax.set_theta_offset(np.deg2rad(270))
    ax.set_theta_direction(-1)
    ax.spines['polar'].set_edgecolor('none')

    # ax.set_yticks([])
    # ax.set_xticks([])
    # ax.set_yticklabels([])
    # ax.set_xticklabels([])

    ax.set_ylim(-0.05, 1.1)

    # Edge Circle
    theta = np.linspace(0, 2 * np.pi, 100)
    r = np.ones(100)

    ax.plot(theta, r * .2, color="black",
            linewidth=1, alpha=1, zorder=3, ls="--")
    ax.plot(theta, r * .4, color="black",
            linewidth=1, alpha=1, zorder=3, ls="--")
    ax.plot(theta, r * .6, color="black",
            linewidth=1, alpha=1, zorder=3, ls="--")
    ax.plot(theta, r * .8, color="black",
            linewidth=1, alpha=1, zorder=3, ls="--")
    ax.plot(theta, r * 1, color="black",
            linewidth=1, alpha=1, zorder=3, ls="--")

    # straight lines up and across
    ax.plot([0, 0], [0, 1], color="black")
    ax.plot([np.pi, np.pi], [0, 1], color="black")
    ax.plot([np.pi / 2, np.pi / 2], [0, 1], color="black")
    ax.plot([-(np.pi / 2), -(np.pi / 2)], [0, 1], color="black")

    # # annotate backwards and forwards text
    ax.text(x=np.pi, y=.9, s="Forwards ->".upper(),
            ha="center", va="center", family="avenir next condensed",
            fontsize=20, rotation=90,
            path_effects=[path_effects.Stroke(linewidth=5, foreground="#FEFAF1", alpha=1),
                          path_effects.Normal()])

    ax.text(x=0, y=.9, s="Backwards ->".upper(),
            ha="center", va="center", family="avenir next condensed",
            fontsize=20, rotation=270,
            path_effects=[path_effects.Stroke(linewidth=5, foreground="#FEFAF1", alpha=1),
                          path_effects.Normal()])

    # return a list of each pass angle - starting at directly backwards
    number_of_angles = 20
    pass_angles_list = np.linspace(-np.pi, np.pi, number_of_angles)

    # angle I want to increase by each step
    step_in_angles_list = (
            (pass_angles_list[number_of_angles - 2])
            - (pass_angles_list[number_of_angles - 3]))

    indexes = list(range(0, number_of_angles - 1))
    width = 2 * np.pi / (number_of_angles - 1)
    angles = [element * width for element in indexes]

    # list that will hold the number of passes in each direction for every direction -
    # will be used for color scale
    pass_data_list = []
    for n in range(number_of_angles - 1):
        start_angle = pass_angles_list[n]
        end_angle = start_angle + step_in_angles_list

        if n == 0:
            player_passes_in_direction = focus_player_open_play_pass_events_df[
                (focus_player_open_play_pass_events_df['pass_angle'] >= start_angle)
                & (focus_player_open_play_pass_events_df['pass_angle'] <= end_angle)]
        else:
            player_passes_in_direction = focus_player_open_play_pass_events_df[
                (focus_player_open_play_pass_events_df['pass_angle'] > start_angle)
                & (focus_player_open_play_pass_events_df['pass_angle'] <= end_angle)]

        count_of_passes = player_passes_in_direction.shape[0]
        median_pass_length = player_passes_in_direction["pass_length"].median()
        pass_dict = {"loop_number": n, "angle": start_angle, "count": count_of_passes,
                     "median_length": median_pass_length}
        pass_data_list.append(pass_dict)

    pass_df = pd.DataFrame(pass_data_list)
    max_count_of_passes = pass_df["count"].max()
    min_count_of_passes = pass_df["count"].min()
    max_length = pass_df["median_length"].max()
    min_length = pass_df["median_length"].min()

    color_map = matplotlib.colormaps["cool"]
    # loop through again to add bars
    for n in range(number_of_angles - 1):
        start_angle = pass_angles_list[n]
        end_angle = start_angle + step_in_angles_list

        if n == 0:
            player_passes_in_direction = focus_player_open_play_pass_events_df[
                (focus_player_open_play_pass_events_df['pass_angle'] >= start_angle)
                & (focus_player_open_play_pass_events_df['pass_angle'] <= end_angle)]
        else:
            player_passes_in_direction = focus_player_open_play_pass_events_df[
                (focus_player_open_play_pass_events_df['pass_angle'] > start_angle)
                & (focus_player_open_play_pass_events_df['pass_angle'] <= end_angle)]

        count_of_passes = player_passes_in_direction.shape[0]
        median_pass_length = player_passes_in_direction["pass_length"].median()

        if count_of_passes > 0:
            pass_count_in_range = ((count_of_passes - min_count_of_passes) /
                                   (max_count_of_passes - min_count_of_passes))

            pass_length_in_range = median_pass_length / max_length

            bar_color = color_map(pass_count_in_range)

            angle_r = angles[n]
            rotation_angle = np.degrees(-angle_r)
            if 90 < np.degrees(angle_r) < 270:
                rotation_angle -= 180
                v_position = "top"
            else:
                rotation_angle -= 0
                v_position = "bottom"

            ax.bar(x=angle_r, height=pass_length_in_range, width=width,
                   edgecolor='black', linewidth=1.5,
                   zorder=3, alpha=1, color=bar_color)

            if median_pass_length == max_length:
                pass_distance = f"{round(median_pass_length * 0.9144, 1)}m"
                ax.text(angle_r, 1.1, f"{pass_distance}",
                        ha='center', va=v_position,
                        rotation=rotation_angle, rotation_mode='anchor',
                        fontsize=20, color="black",
                        family='avenir next condensed',
                        zorder=8,
                        path_effects=[path_effects.Stroke(linewidth=2, foreground="#FEFAF1", alpha=1),
                                      path_effects.Normal()])

    # annotate %s for pass directions
    pass_angle_dict = {"Forwards": [135, 225],
                       "Right": [225, 315],
                       }
    forwards_angle_range = [(-np.pi / 6), (np.pi / 6)]

    # COLOR BAR -------------------------------------------------------------------------------------------------------
    cbar_ax = fig.add_subplot(ax_cbar[4])

    cbar_ax.set_ylim(0, 1)
    cbar_ax.set_xlim(min_count_of_passes, max_count_of_passes)

    norm = Normalize(vmin=min_count_of_passes, vmax=max_count_of_passes)
    fig.colorbar(cm.ScalarMappable(norm=norm, cmap=color_map), cax=cbar_ax,
                 orientation="horizontal", location="bottom", shrink=0.8)

    cbar_ax.tick_params(labelsize=20, labelfontfamily="avenir", length=1)

    # ax_low.yaxis.set_ticks([])
    # ax_low.xaxis.set_ticks([])

    # FIGURE TEXT

    fig.text(x=.5125, y=1.02, s=f"Passing Sonar".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=50, ha="center", va="center")

    fig.text(x=.5125, y=.96,
             s=f"{focus_player_name} Open Play Passes"
               f"\nLength of bar represents median pass distance in that direction\n"
               f"Total Passes {focus_player_open_play_pass_counts}".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=24, ha="center", va="center")

    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_passes_radar_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=True)

    plt.close()

# create_player_passing_sonar(6655)
