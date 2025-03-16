import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import pandas as pd

from helpers.helper_functions import add_position_to_pass_receiver


def player_pass_combinations(focus_player_id):
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

    # get a list of the match_ids the player played in
    focus_player_events_df = player_events_df[player_events_df["player_id"] == focus_player_id]
    focus_player_name = focus_player_events_df["player"].iloc[0]
    focus_player_team = focus_player_events_df["team"].iloc[0]
    focus_player_competition = focus_player_events_df["competition_name"].iloc[0]

    # DATA
    focus_player_open_play_pass_events = player_events_df[
        ((player_events_df["player_id"] == focus_player_id)
         | (player_events_df["pass_recipient_id"] == focus_player_id))
        & (player_events_df["type"] == "Pass")
        & (player_events_df["pass_outcome"] != "Offside")
        & ~(player_events_df["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))].copy()

    focus_player_open_play_pass_events["pass_receiver_position"] = focus_player_open_play_pass_events.apply(
        lambda row_: add_position_to_pass_receiver(row_, player_events_df), axis=1)

    # Counts of recipients of passes from the focus player
    passes_to_focus_player_counts = focus_player_open_play_pass_events[
        (focus_player_open_play_pass_events["pass_recipient_id"] == focus_player_id)][
        "position"].value_counts().rename(
        "passes_to")

    passes_from_focus_player_counts = focus_player_open_play_pass_events[
        (focus_player_open_play_pass_events["player_id"] == focus_player_id)][
        "pass_receiver_position"].value_counts().rename("passes_from")

    player_all_pass_counts = pd.concat(
        [passes_to_focus_player_counts,
         passes_from_focus_player_counts], axis=1).fillna(0).reset_index()

    player_all_pass_counts["total_pass_events"] = player_all_pass_counts[
        ["passes_to", "passes_from"]].sum(axis=1)

    player_all_pass_counts.sort_values("total_pass_events", ascending=False, inplace=True)

    player_all_pass_counts = player_all_pass_counts.head(10)
    player_all_pass_counts.reset_index(inplace=True)
    max_passes_to_or_from = player_all_pass_counts[["passes_to", "passes_from"]].max().max()

    fig = plt.figure(figsize=(25, 8), dpi=100)
    ax = fig.add_subplot()

    ax.set_facecolor("none")
    title_text_color = "black"

    ax.set_xlim(-max_passes_to_or_from - 5, max_passes_to_or_from + 5)
    ax.set_ylim(0, 10)

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.yaxis.set_ticks([])
    ax.xaxis.set_ticks([])

    # 0 line on y-axis
    ax.plot([0, 0], [ax.get_ylim()[0], ax.get_ylim()[1]], color="black")

    ax.text(x=-5, y=ax.get_ylim()[1], s=f"Passes to {focus_player_name}".upper(),
            ha="right", va="bottom", family="avenir next condensed", fontsize=24,
            color="powderblue",
            path_effects=[path_effects.Stroke(linewidth=2, foreground="black", alpha=1),
                          path_effects.Normal()])

    ax.text(x=5, y=ax.get_ylim()[1], s=f"Passes from {focus_player_name}".upper(),
            ha="left", va="bottom", family="avenir next condensed", fontsize=24,
            color="orange",
            path_effects=[path_effects.Stroke(linewidth=2, foreground="black", alpha=1),
                          path_effects.Normal()])

    y_start = ax.get_ylim()[1] - 0.5
    for index, row in player_all_pass_counts.iterrows():
        position = row["index"]
        passes_to = row["passes_to"]
        passes_from = row["passes_from"]
        total_passes = row["total_pass_events"]

        # position text
        ax.text(x=0, y=y_start,
                s=f"{position} ({int(total_passes)})".upper(),
                ha="center", va="center", family="avenir next condensed", fontsize=18,
                color="black", bbox=dict(facecolor="#FEFAF1", alpha=1, boxstyle='round,pad=0.2'))

        # passes to player bar
        ax.barh(y=y_start, width=-passes_to, color="powderblue", edgecolor="black")
        ax.text(x=-passes_to - 0.5, y=y_start,
                s=f"{int(passes_to)}",
                ha="right", va="center", family="avenir next condensed", fontsize=20,
                color="black")

        # passes from player bar
        ax.barh(y=y_start, width=passes_from, color="orange", edgecolor="black")
        ax.text(x=passes_from + 0.5, y=y_start,
                s=f"{int(passes_from)}",
                ha="left", va="center", family="avenir next condensed", fontsize=20,
                color="black")

        y_start -= 1

    # FIGURE
    fig.text(x=.5125, y=1.025, s=f"{focus_player_name} Passing Combinations".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=32, ha="center", va="center")

    fig.text(x=.5125, y=.97,
             s=f"The top 10 positions {focus_player_name} Has Passed to and received from\n"
               f"ordered by total passes".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=13, ha="center", va="center")

    fig.set_facecolor("#FEFAF1")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_passing_combinations_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=True)

    plt.close()


player_pass_combinations(6655)
