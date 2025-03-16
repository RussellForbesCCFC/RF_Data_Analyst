import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


def player_shot_sequence_involvement(focus_player_id):
    positive_cmap_list = ["#FEFAF1", "#9cb7d8", "#1974b1"]
    positive_cmap = LinearSegmentedColormap.from_list("", positive_cmap_list)
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

    focus_player_name = player_events_df[
        (player_events_df["player_id"] == focus_player_id)]["player"].iloc[0]

    focus_player_team = player_events_df[
        (player_events_df["player_id"] == focus_player_id)]["team"].iloc[0]

    focus_player_competition = player_events_df[
        (player_events_df["player_id"] == focus_player_id)]["competition_name"].iloc[0]

    # get all team possession that contain a shot

    team_shot_possessions = player_events_df[
        (player_events_df["team"] == focus_player_team)
        & (player_events_df["type"] == "Shot")
        & ~(player_events_df["shot_type"].isin(["Penalty", "Free Kick"]))].drop_duplicates(
        ["match_id", "possession"], keep="last")

    team_all_shots = player_events_df[
        (player_events_df["team"] == focus_player_team)
        & (player_events_df["type"] == "Shot")
        & ~(player_events_df["shot_type"].isin(["Penalty", "Free Kick"]))]

    shot_possession_passes_list = []

    for index, row in team_shot_possessions.iterrows():
        row_match_id = row["match_id"]
        row_possession = row["possession"]
        row_index_of_shot = row["index"]

        pass_events_leading_to_shot = player_events_df[
            (player_events_df["match_id"] == row_match_id)
            & (player_events_df["possession"] == row_possession)
            & (player_events_df["index"] < row_index_of_shot)
            & (player_events_df["type"] == "Pass")
            & ~(player_events_df["pass_type"].isin(["Corner", "Free Kick", "Throw-in", "Kick Off"]))
            & (player_events_df["team"] == focus_player_team)]

        shot_possession_passes_list.append(pass_events_leading_to_shot)

    shot_possession_passes_df = pd.concat(shot_possession_passes_list)
    shot_possession_passes_df["chance_created"] = (shot_possession_passes_df["pass_shot_assist"] == True) | (
            shot_possession_passes_df["pass_goal_assist"] == True)

    # only want to count build up involvements once
    build_up_pass_counts = shot_possession_passes_df[
        (shot_possession_passes_df["chance_created"] == False)].drop_duplicates(
        ["match_id", "possession", "player_id"])["player"].value_counts().rename("build_up")

    # build_up_pass_counts = shot_possession_passes_df[
    #     (shot_possession_passes_df["chance_created"] == False)]["player"].value_counts().rename("build_up")

    shot_assist_pass_counts = shot_possession_passes_df[
        (shot_possession_passes_df["chance_created"] == True)]["player"].value_counts().rename("chance_created")
    shot_counts = team_all_shots["player"].value_counts().rename("shots")

    player_attacking_sequence_df = pd.concat(
        [build_up_pass_counts,
         shot_assist_pass_counts,
         shot_counts],
        axis=1).fillna(0).reset_index()

    player_attacking_sequence_df["total_involvements"] = player_attacking_sequence_df[
        ["build_up", "chance_created", "shots"]].sum(axis=1)

    player_attacking_sequence_df.sort_values("total_involvements", ascending=False, inplace=True)
    player_attacking_sequence_df = player_attacking_sequence_df[
        (player_attacking_sequence_df["total_involvements"] >= 5)]

    max_sequences_involvements = player_attacking_sequence_df["total_involvements"].max()

    # create bar graph
    fig = plt.figure(figsize=(15, 15), dpi=100)
    ax = fig.add_subplot()
    ax.set_facecolor("none")
    title_text_color = "black"

    ax.set_ylim(-0.1, player_attacking_sequence_df.shape[0] + 0.1)
    ax.set_xlim(-1, max_sequences_involvements + 10)

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.yaxis.set_ticks([])
    ax.xaxis.set_ticks([])

    # 0 line on y-axis
    ax.plot([0, 0],
            [ax.get_ylim()[0], ax.get_ylim()[1]],
            color="black")

    y_start = ax.get_ylim()[1] - 0.5
    for index, row in player_attacking_sequence_df.iterrows():
        player = row["player"]

        player_name_split = player.split(" ")
        len_name_elements = len(player_name_split)

        if len_name_elements == 1:
            name_string = player_name_split[0]
        elif len_name_elements == 2:
            name_string = f"{player_name_split[0]} {player_name_split[1]}"
        elif len_name_elements == 3:
            name_string = (f"{player_name_split[0]} {player_name_split[1]}\n"
                           f"{player_name_split[2]}")
        elif len_name_elements == 4:
            name_string = (f"{player_name_split[0]} {player_name_split[1]}\n"
                           f"{player_name_split[2]} {player_name_split[2]}")

        elif len_name_elements == 5:
            name_string = (f"{player_name_split[0]} {player_name_split[1]}\n"
                           f"{player_name_split[2]} {player_name_split[2]} {player_name_split[3]}")
        else:
            name_string = "\n".join(player_name_split)

        build_up_count = row["build_up"]
        chance_created_count = row["chance_created"]
        shots_count = row["shots"]

        if player == focus_player_name:
            alpha_ref = 1
            text_size = 18
        else:
            alpha_ref = .7
            text_size = 12

        # build up
        ax.barh(y=y_start, width=build_up_count, color="lightgrey", edgecolor="black", alpha=alpha_ref)
        ax.text(x=build_up_count - 0.5, y=y_start, s=build_up_count, ha="right", va="center",
                family="avenir next condensed", fontsize=15, alpha=alpha_ref)

        # chances created
        ax.barh(y=y_start, width=chance_created_count, left=build_up_count, color="orange",
                edgecolor="black", alpha=alpha_ref)
        if chance_created_count > 1:
            ax.text(x=build_up_count + chance_created_count - 0.5, y=y_start, s=f"{int(chance_created_count)}",
                    ha="right", va="center",
                    family="avenir next condensed", fontsize=15, alpha=alpha_ref)

        # shots
        ax.barh(y=y_start, width=shots_count,
                left=build_up_count + chance_created_count, color="red",
                edgecolor="black", alpha=alpha_ref)

        if shots_count > 1:
            ax.text(x=build_up_count + chance_created_count + shots_count - 0.5,
                    y=y_start, s=f"{int(shots_count)}",
                    ha="right", va="center",
                    family="avenir next condensed", fontsize=15, alpha=alpha_ref)

        ax.text(x=build_up_count + chance_created_count + shots_count + 0.5,
                y=y_start, s=name_string.upper(), ha="left", va="center",
                family="avenir next condensed", fontsize=text_size, alpha=alpha_ref)

        y_start -= 1

    # legend
    ax.barh(y=-10, width=10, color="lightgrey", edgecolor="black", label="BUILD UP")
    ax.barh(y=-10, width=10, color="orange", edgecolor="black", label="CHANCE CREATED")
    ax.barh(y=-10, width=10, color="red", edgecolor="black", label="SHOT TAKEN")

    ax.legend(bbox_to_anchor=(0.2, 0.775, 0.6, 0.5),
              loc='center', frameon=False, ncols=3, labelcolor='black',
              mode='expand', borderaxespad=.2, handlelength=2, handleheight=2, handletextpad=0.3,
              prop={"family": "avenir next condensed", "size": 14})

    # figure text
    fig.text(x=.5125, y=.96, s=f"{focus_player_team} Shot Sequences Involvements".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=40, ha="center", va="center")

    fig.text(x=.5125, y=.94,
             s=f"Involvements in Open Play Shot Ending Sequences at {focus_player_competition}".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=18, ha="center", va="center")

    fig.text(x=.5125, y=.1,
             s=f"Players with 5+ shot sequences involvements\n"
               f"Build Up Passes counted as 1 per possession".upper(),
             color=title_text_color,
             family="avenir",
             fontsize=15, ha="center", va="center")

    fig.set_facecolor("none")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_team_shot_sequences_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


player_shot_sequence_involvement(6655)
