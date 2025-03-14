import matplotlib.pyplot as plt
import pandas as pd
from highlight_text import ax_text
from mplsoccer import VerticalPitch

from helpers.helper_functions import get_start_locations, get_pass_end_locations, add_position_to_pass_receiver


def player_top_6_pass_clusters(focus_player_id):
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

    focus_player_open_play_pass_events_df = player_events_df[
        (player_events_df["player_id"] == focus_player_id)
        & (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Offside")
        & ~(player_events_df["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))].copy()

    focus_player_open_play_pass_events_df[['location_x', 'location_y']] = focus_player_open_play_pass_events_df.apply(
        lambda _row_: pd.Series(get_start_locations(_row_)), axis=1)

    focus_player_open_play_pass_events_df[
        ['end_location_x', 'end_location_y']] = focus_player_open_play_pass_events_df.apply(
        lambda _row_: pd.Series(get_pass_end_locations(_row_)), axis=1)

    focus_player_open_play_pass_events_df["pass_receiver_position"] = focus_player_open_play_pass_events_df.apply(
        lambda row_: add_position_to_pass_receiver(row_, player_events_df), axis=1)

    focus_player_name = focus_player_open_play_pass_events_df["player"].iloc[0]

    # only filter where the pass cluster probability is over 60%
    focus_player_open_play_pass_events_df_with_clusters = focus_player_open_play_pass_events_df[
        (focus_player_open_play_pass_events_df["pass_pass_cluster_probability"] > .6)]

    focus_player_cluster_counts = focus_player_open_play_pass_events_df_with_clusters[
        "pass_pass_cluster_id"].value_counts().reset_index()

    fig = plt.figure(figsize=(20, 20), dpi=100)
    title_text_color = "black"

    ax_counter = 1
    for index, row in focus_player_cluster_counts.head(6).iterrows():
        ax = fig.add_subplot(2, 3, ax_counter)

        pitch = VerticalPitch(pitch_type="statsbomb",
                              pitch_color='none',
                              half=False, line_zorder=2, corner_arcs=True,
                              linewidth=1, line_alpha=1, line_color='black',
                              pad_left=4, pad_right=4, pad_bottom=4, pad_top=4)

        pitch.draw(ax=ax)

        ax.fill_between([0, 80],
                        0, 120,
                        linewidth=0,
                        color="#fefaf1",
                        alpha=1, zorder=1)

        if ax_counter in [1, 4]:
            ax.annotate(xy=(-2, 90), xytext=(-2, 30), text='', color=title_text_color, size=16,
                        xycoords='data',
                        arrowprops=dict(arrowstyle='-|>', color=title_text_color))

            ax.annotate(xy=(-2.5, 60), xytext=(-2.5, 60), text='Direction of Attack'.upper(),
                        va='center', ha="right", color=title_text_color, size=14,
                        xycoords='data', family='avenir', rotation=90)

        x_plot_points = [18, 30, 50, 62]
        y_plot_points = [18, 40, 60, 80, 102]
        for y in y_plot_points:
            ax.plot([0, 80], [y, y], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

        for x in x_plot_points:
            ax.plot([x, x], [0.1, 120], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

        pass_id = row["pass_pass_cluster_id"]
        passes_in_cluster = focus_player_open_play_pass_events_df_with_clusters[
            (focus_player_open_play_pass_events_df_with_clusters["pass_pass_cluster_id"] == pass_id)]
        cluster_pass_receivers = passes_in_cluster["pass_receiver_position"].value_counts().reset_index()
        top_receiver_position = cluster_pass_receivers["pass_receiver_position"].iloc[0]
        top_receiver_count = cluster_pass_receivers["count"].iloc[0]

        pass_cluster_name = passes_in_cluster["pass_pass_cluster_label"].iloc[0]
        pass_cluster_name_split = pass_cluster_name.split(" - ")

        total_passes_in_cluster = passes_in_cluster.shape[0]
        pitch_title = (f"{pass_cluster_name_split[0]} - {pass_cluster_name_split[4]}\n"
                       f"<Total Passes: {total_passes_in_cluster}>\n"
                       f"<Top Receiver: {top_receiver_position} ({top_receiver_count})>")

        ax_text(x=40, y=127, s=pitch_title.upper(),
                color=title_text_color, highlight_textprops=[
                {"family": "avenir", "fontsize": 15}, {"family": "avenir", "fontsize": 13}],
                textalign="center", vsep=2,
                ha="center", va="center", family="avenir next condensed", fontsize=20)

        pitch.arrows(passes_in_cluster["location_x"], passes_in_cluster["location_y"],
                     passes_in_cluster["end_location_x"], passes_in_cluster["end_location_y"],
                     color="powderblue", ec='black', linewidth=.5,
                     ax=ax, width=2, headwidth=4.5, headlength=4.5, alpha=1, zorder=2)

        ax_counter += 1

    # FIGURE
    fig.text(x=.5125, y=.955, s=f"{focus_player_name} Most Common Passes".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=48, ha="center", va="center")

    fig.text(x=.5125, y=.93,
             s=f"Pitches Show the 6 most common pass types played by {focus_player_name}".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=22, ha="center", va="center")

    fig.set_facecolor("none")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_all_passes_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


player_top_6_pass_clusters(6655)
