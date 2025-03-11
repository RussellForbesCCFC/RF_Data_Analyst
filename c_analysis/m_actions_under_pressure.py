import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
from highlight_text import ax_text, fig_text
import matplotlib.patheffects as path_effects

from matplotlib.colors import LinearSegmentedColormap

from helpers.helper_dictionaries import position_groups
from helpers.helper_functions import get_start_locations, get_carry_end_locations, get_pass_end_locations, \
    calculate_action_distance, assign_zone_to_start_thirds


def ball_receipts_under_pressure_next_action_id(row, all_events_df):
    """
    returns the id of the player next action after receiving the ball under pressure
    :param all_events_df:
    :param row:
    :return: event_id
    """
    player_id = row["player_id"]
    player = row["player"]
    action_type = row["type"]
    timestamp = row["timestamp"]
    possession = row["possession"]
    period = row["period"]
    match_id = row["match_id"]

    # the timestamp needs to be the same or higher as if the player passes on their first touch
    # the timestamp will be the same as the receipt
    player_first_next_action = all_events_df[
        (all_events_df["match_id"] == match_id)
        & (all_events_df["possession"] == possession)
        & (all_events_df["period"] == period)
        & (all_events_df["timestamp"] >= timestamp)
        & (all_events_df["player_id"] == player_id)
        & (all_events_df["type"] != "Ball Receipt*")].sort_values("index", ascending=True).iloc[0]

    first_action_type = player_first_next_action["type"]
    first_action_id = player_first_next_action["id"]

    if first_action_type == "Pass":
        pass_outcome = player_first_next_action["pass_outcome"]
        if pass_outcome not in ["Incomplete", "Out", "Unknown", "Pass Offside", "Injury Clearance"]:
            first_action_outcome = "Successful"
        elif pass_outcome in ["Pass Offside", "Injury Clearance"]:
            first_action_outcome = "Exclude"
        else:
            first_action_outcome = "Unsuccessful"

    elif first_action_type in ["Miscontrol", "Dispossessed"]:
        first_action_outcome = "Unsuccessful"
    elif first_action_type == "Carry":
        try:
            player_action_after_carry = all_events_df[
                (all_events_df["match_id"] == match_id)
                & (all_events_df["possession"] == possession)
                & (all_events_df["period"] == period)
                & (all_events_df["timestamp"] >= timestamp)
                & (all_events_df["player_id"] == player_id)
                & (all_events_df["type"] != "Ball Receipt*")].sort_values("index", ascending=True).iloc[1]

            player_action_after_carry_type = player_action_after_carry["type"]
            if player_action_after_carry_type == "Pass":
                pass_outcome_after_carry = player_action_after_carry["pass_outcome"]
                if pass_outcome_after_carry not in ["Incomplete", "Out", "Unknown", "Pass Offside", "Injury Clearance"]:
                    first_action_outcome = "Successful"
                elif pass_outcome_after_carry in ["Pass Offside", "Injury Clearance"]:
                    first_action_outcome = "Exclude"
                else:
                    first_action_outcome = "Unsuccessful"

            elif player_action_after_carry_type in ["Miscontrol", "Dispossessed"]:
                first_action_outcome = "Unsuccessful"
            elif player_action_after_carry_type in ["Foul Won", "Shot"]:
                first_action_outcome = "Successful"
            elif player_action_after_carry_type in ["Dribble"]:
                dribble_outcome_after_carry = player_action_after_carry["dribble_outcome"]
                if dribble_outcome_after_carry == "Complete":
                    first_action_outcome = "Successful"
                else:
                    first_action_outcome = "Unsuccessful"

            else:
                first_action_outcome = "Exclude"

        except IndexError:
            first_action_outcome = "Exclude"

    elif first_action_type in ["Shot", "Foul Won"]:  # other options are shot a
        first_action_outcome = "Successful"
    else:
        first_action_outcome = "Exclude"

    return first_action_id, first_action_outcome


def player_actions_under_pressure(focus_player_id):
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

    focus_player_ball_receipts_under_pressure_df = player_events_df[
        (player_events_df["player_id"] == focus_player_id)
        & (player_events_df["type"] == "Ball Receipt*")
        & (player_events_df["under_pressure"] == True)
        & (player_events_df["ball_receipt_outcome"].isnull())].copy()

    focus_player_name = focus_player_ball_receipts_under_pressure_df["player"].iloc[0]

    focus_player_ball_receipts_under_pressure_df[
        ['location_x', 'location_y']] = focus_player_ball_receipts_under_pressure_df.apply(
        lambda _row_: pd.Series(get_start_locations(_row_)), axis=1)

    focus_player_ball_receipts_under_pressure_df["start_zone"] = focus_player_ball_receipts_under_pressure_df.apply(
        assign_zone_to_start_thirds, axis=1)

    focus_player_ball_receipts_under_pressure_df[
        ["next_action_id", "next_action_outcome"]] = focus_player_ball_receipts_under_pressure_df.apply(
        lambda row_: pd.Series(ball_receipts_under_pressure_next_action_id(row_, player_events_df)), axis=1)

    print(focus_player_ball_receipts_under_pressure_df.head().to_string())

    fig = plt.figure(figsize=(20, 12), dpi=100)
    title_text_color = "black"

    ax = fig.add_subplot()

    pitch = VerticalPitch(pitch_type="statsbomb",
                          pitch_color='none',
                          half=False, line_zorder=2, corner_arcs=True,
                          linewidth=1, line_alpha=1, line_color='black',
                          pad_left=0, pad_right=0, pad_bottom=0, pad_top=0)

    pitch.draw(ax=ax)

    ax.set_facecolor("#FEFAF1")

    x_plot_points = [18, 30, 50, 62]
    y_plot_points = [18, 40, 60, 80, 102]
    for y in y_plot_points:
        ax.plot([0, 80], [y, y], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

    for x in x_plot_points:
        ax.plot([x, x], [0.1, 120], color='black', linewidth=.5, zorder=2, alpha=0.5, ls="--")

    # CREATING DF OF ZONE REFERENCES -----------------------------------------------------------------------------------
    positional_y_range = [0, 18, 30, 50, 62]
    positional_y_step = [18, 12, 20, 12, 18]
    positional_x_range = [0, 18, 40, 60, 80, 102]
    positional_x_step = [18, 22, 20, 20, 22, 18]

    count = 0
    zone_list = []
    for n, x in enumerate(positional_x_range):
        for n_2, y in enumerate(positional_y_range):
            x_start = x
            x_step = positional_x_step[n]
            x_end = x + x_step

            y_start = y
            y_step = positional_y_step[n_2]
            y_end = y_start + y_step

            count += 1

            zone_dict = {"x_start": y_start, "x_end": y_end, "y_start": x_start, "y_end": x_end,
                         "zone_name": count}
            zone_list.append(zone_dict)

    y_plotted = [0]
    x_plotted = [0]
    for r in zone_list:
        x_start = r["x_start"]
        x_end = r["x_end"]
        y_start = r["y_start"]
        y_end = r["y_end"]

        y_plotted.append(y_start)
        x_plotted.append(x_start)

    # ZONE SHADING
    zone_df = pd.DataFrame(zone_list)
    zone_df["x_range"] = zone_df["x_end"] - zone_df["x_start"]
    zone_df["x_center"] = zone_df["x_start"] + (zone_df["x_range"] / 2)

    zone_df["y_range"] = zone_df["y_end"] - zone_df["y_start"]
    zone_df["y_center"] = zone_df["y_start"] + (zone_df["y_range"] / 2)

    start_zone_counts = focus_player_ball_receipts_under_pressure_df["start_zone"].value_counts().reset_index()
    max_start_zone = start_zone_counts["count"].max()

    for index, row in start_zone_counts.iterrows():
        zone_ref = row["start_zone"]
        count = row["count"]
        count_per_max = (count / max_start_zone)

        # Shading the Zone
        end_zone_reference = zone_df[zone_df["zone_name"] == zone_ref]

        end_x_start = end_zone_reference["x_start"].iloc[0]
        end_y_start = end_zone_reference["y_start"].iloc[0]

        end_x_end = end_zone_reference["x_end"].iloc[0]
        end_y_end = end_zone_reference["y_end"].iloc[0]

        c_fill = positive_cmap(count_per_max)

        ax.fill_between([end_x_start, end_x_end],
                        end_y_start,
                        end_y_end,
                        color=c_fill, alpha=.6, zorder=1, linewidth=0, edgecolor="white")

    next_action_colors = {"Exclude": "lightgrey",
                          "Unsuccessful": "indianred",
                          "Successful": "palegreen"}

    for index, row in focus_player_ball_receipts_under_pressure_df.iterrows():
        location_x = row["location_x"]
        location_y = row["location_y"]
        next_action_id = row["next_action_id"]
        next_action_outcome = row["next_action_outcome"]
        next_action_event = player_events_df[
            (player_events_df["id"] == next_action_id)]
        next_action_type = next_action_event["type"].iloc[0]
        color = next_action_colors[next_action_outcome]

        pitch.scatter(location_x, location_y,
                      color=color, ec='black', linewidth=.5,
                      ax=ax, s=250, alpha=1, zorder=3)

        # if next_action_type == "Pass":
        #     next_action_location = next_action_event["location"].iloc[0]
        #     next_action_end_location = next_action_event["pass_end_location"].iloc[0]
        #     next_action_end_location_x = eval(next_action_end_location)[0]
        #     next_action_end_location_y = eval(next_action_end_location)[1]
        #
        #     pitch.arrows(location_x, location_y,
        #                  next_action_end_location_x, next_action_end_location_y,
        #                  color=color, ec='black', linewidth=.5,
        #                  ax=ax, width=2, headwidth=4.5, headlength=4.5, alpha=1, zorder=2)
        #
        # elif next_action_type == "Carry":
        #     next_action_location = next_action_event["location"].iloc[0]
        #     next_action_end_location = next_action_event["carry_end_location"].iloc[0]
        #     next_action_end_location_x = eval(next_action_end_location)[0]
        #     next_action_end_location_y = eval(next_action_end_location)[1]
        #
        #     pitch.arrows(location_x, location_y,
        #                  next_action_end_location_x, next_action_end_location_y,
        #                  color=color, ec='black', linewidth=.5,
        #                  ax=ax, width=2, headwidth=4.5, headlength=4.5, alpha=1, zorder=2)

    # FIGURE
    fig.text(x=.5125, y=.95, s=f"Ball Receipts Under Pressure".upper(),
             color=title_text_color,
             family="avenir next condensed",
             fontsize=32, ha="center", va="center")

    pe = [path_effects.Stroke(linewidth=1, foreground="black", alpha=1),
          path_effects.Normal()]

    fig_text(x=.5125, y=.91,
             s=f"Pitch Shows all {focus_player_name} Ball Receipts Under Pressure\n"
               f"Colors show if the next action was <successful> or <unsuccessful>".upper(),
             highlight_textprops=[{"family": "avenir next condensed", "color": "palegreen", "path_effects": pe},
                                  {"family": "avenir next condensed", "color": "indianred", "path_effects": pe}],
             textalign="center",
             color=title_text_color,
             family="avenir",
             fontsize=13, ha="center", va="center")

    # fig.text(x=.5125, y=.92,
    #          s=f"Pitch Shows all progressive Carries made by {focus_player_name}\n"
    #            f"Progressive Carries are carries that travel over 10m\n"
    #            f"and at least 10% of the remaining distance towards goal".upper(),
    #          color=title_text_color,
    #          family="avenir",
    #          fontsize=16, ha="center", va="center")

    fig.set_facecolor("none")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_actions_under_pressure_{focus_player_id}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=False)

    plt.close()


player_actions_under_pressure(6655)
