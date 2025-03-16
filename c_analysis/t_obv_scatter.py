import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import pandas as pd
from adjustText import adjust_text
from highlight_text import ax_text
from matplotlib import ticker


def create_obv_scatter(focus_player_id, position_group, min_minutes, scatter_metric_dict):
    player_df = pd.read_csv(
        "/Users/russellforbes/PycharmProjects/RF_Data_Analyst/a_data/b_aggregated_data/player_aggregated_data.csv")

    player_df = player_df[
        (player_df["total_time_minutes"] >= min_minutes)
        & (player_df["position_group"] == position_group)].copy()

    focus_player_name = player_df[player_df["player_id"] == focus_player_id]["player"].iloc[0]

    fig = plt.figure(figsize=(20, 14), dpi=100)
    ax = fig.add_subplot()

    metric_names = [i for i in scatter_metric_dict.keys()]
    metric_one = metric_names[0]
    metric_two = metric_names[1]

    metric_one_range = [player_df[metric_one].min(),
                        player_df[metric_one].max()]

    metric_one_ten_per = (metric_one_range[1] - metric_one_range[0]) * 0.1

    metric_two_range = [player_df[metric_two].min(),
                        player_df[metric_two].max()]

    metric_two_ten_per = (metric_two_range[1] - metric_two_range[0]) * 0.1

    ax.set_ylim(metric_one_range[0] - metric_one_ten_per, metric_one_range[1] + metric_one_ten_per)
    ax.set_xlim(metric_two_range[0] - metric_two_ten_per, metric_two_range[1] + metric_two_ten_per)

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    metric_one_rename = scatter_metric_dict[metric_one]
    metric_two_rename = scatter_metric_dict[metric_two]

    ax.set_ylabel(metric_one_rename.upper(),
                  family="avenir next condensed", ha="center", va="bottom", fontsize=22)

    ax.set_xlabel(metric_two_rename.upper(),
                  family="avenir next condensed", ha="center", va="top", fontsize=22)

    ax.tick_params(labelfontfamily="avenir", labelsize=14)

    ax.grid(ls="--", alpha=.6, color="black")
    ax.fill_between([ax.get_xlim()[0], ax.get_xlim()[1]], ax.get_ylim()[0], ax.get_ylim()[1], color="#fefaf1",
                    alpha=.5)

    player_df[f"{metric_one}_percentile"] = player_df[metric_one].rank(pct=True, ascending=True)
    player_df[f"{metric_two}_percentile"] = player_df[metric_two].rank(pct=True, ascending=True)

    # adding average lines
    average_metric_one = player_df[metric_one].mean()
    ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]],
            [average_metric_one, average_metric_one], ls="--", color="black")

    ax.text(x=ax.get_xlim()[0] + (metric_one_ten_per / 5),
            y=average_metric_one, s=f"average {metric_one_rename}".upper(),
            family="avenir next condensed", ha="left", va="center", fontsize=18,
            bbox=dict(facecolor="#FEFAF1", alpha=1, boxstyle='round,pad=0.2'))

    average_metric_two = player_df[metric_two].mean()
    ax.plot([average_metric_two, average_metric_two],
            [ax.get_ylim()[0], ax.get_ylim()[1]], ls="--", color="black")

    ax.text(x=average_metric_two,
            y=ax.get_ylim()[0] + (metric_two_ten_per / 5), s=f"average {metric_two_rename}".upper(),
            family="avenir next condensed", ha="center", va="bottom", fontsize=18, rotation=90,
            bbox=dict(facecolor="#FEFAF1", alpha=1, boxstyle='round,pad=0.2'))

    if metric_one in ["open_play_forward_pass_percentage"]:
        ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f%%'))
    if metric_two in ["open_play_forward_pass_percentage"]:
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f%%'))

    # adding player data
    top_players = []
    x_points_repel = []
    y_points_repel = []
    for index, row in player_df.iterrows():
        player_id_ref = row["player_id"]
        player_name_ref = row["player"]
        player_metric_one = row[metric_one]
        player_metric_two = row[metric_two]
        player_metric_one_percentile = row[f"{metric_one}_percentile"]
        player_metric_two_percentile = row[f"{metric_two}_percentile"]
        x_points_repel.append(player_metric_two)
        y_points_repel.append(player_metric_one)

        if player_id_ref == focus_player_id:
            col = "powderblue"
            z_ref = 5
            size = 1000
            al = 1
            lw = 2

        else:
            col = "lightgrey"
            z_ref = 2
            size = 350
            al = .8
            lw = 1

        ax.scatter(
            x=player_metric_two, y=player_metric_one,
            s=size, color=col, edgecolor="black", linewidth=lw, zorder=z_ref, alpha=al)

        # workings to label players above average for both metrics
        if player_metric_one_percentile > .8 or player_metric_two_percentile > .8:
            top_players += [
                ax.text(x=player_metric_two, y=player_metric_one,
                        s=player_name_ref, family="avenir next condensed",
                        fontsize=15, alpha=0.7, ha="right", va="center", zorder=3,
                        path_effects=[path_effects.Stroke(linewidth=2, foreground="#FEFAF1", alpha=0.7),
                                      path_effects.Normal()])]

    adjust_text(top_players, x=x_points_repel, y=y_points_repel,
                avoid_self=True, ensure_inside_axes=True,
                arrowprops=dict(arrowstyle='-', color='black'),
                expand=(1.2, 1.2),
                ax=ax)

    # focus player string - needs to be after all scatter points as z order does not work with ax_text
    focus_player_row = (
        player_df[(player_df["player_id"] == focus_player_id)].iloc)[0]

    focus_player_metric_one = focus_player_row[metric_one]
    focus_player_metric_two = focus_player_row[metric_two]

    if metric_one in ["open_play_forward_pass_percentage"]:
        label_one_string = f"{round(focus_player_metric_one, 1)}%"
    else:
        label_one_string = f"{round(focus_player_metric_one, 2)}"

    if metric_two in ["open_play_forward_pass_percentage"]:
        label_two_string = f"{round(focus_player_metric_two, 1)}%"
    else:
        label_two_string = f"{round(focus_player_metric_two, 2)}"

    player_string = (f"{focus_player_name}\n"
                     f"<{metric_one_rename}: {label_one_string}>\n"
                     f"<{metric_two_rename}: {label_two_string}>")

    ax_text(x=focus_player_metric_two, y=focus_player_metric_one - (metric_one_ten_per / 3),
            s=player_string.upper(), ha="center", va="top",
            family="avenir next condensed", fontsize=18, color="black", zorder=10,
            highlight_textprops=[{"fontsize": 12}, {"fontsize": 12}],
            textalign="center",
            annotationbbox_kw={"frameon": True, 'bboxprops': {
                'facecolor': 'powderblue', 'edgecolor': 'black', 'linewidth': 1}},
            ax=ax)

    # scatter annotations
    scatter_annotations_dict = {
        "high_high": {"text": f"High {metric_one_rename}\nHigh {metric_two_rename}",
                      "y_location": ax.get_ylim()[1] - (metric_one_ten_per / 2),
                      "x_location": ax.get_xlim()[1] - (metric_two_ten_per / 5),
                      "text_align": "right"},
        "high_low": {"text": f"High {metric_one_rename}\nLow {metric_two_rename}",
                     "y_location": ax.get_ylim()[1] - (metric_one_ten_per / 2),
                     "x_location": ax.get_xlim()[0] + (metric_two_ten_per / 5),
                     "text_align": "left"},
        "low_high": {"text": f"Low {metric_one_rename}\nHigh {metric_two_rename}",
                     "y_location": ax.get_ylim()[0] + (metric_one_ten_per / 2),
                     "x_location": ax.get_xlim()[1] - (metric_two_ten_per / 5),
                     "text_align": "right"}
    }

    for sa in scatter_annotations_dict:
        text_s = scatter_annotations_dict[sa]["text"]
        x_location = scatter_annotations_dict[sa]["x_location"]
        y_location = scatter_annotations_dict[sa]["y_location"]
        text_align = scatter_annotations_dict[sa]["text_align"]

        ax.text(x=x_location, y=y_location, s=text_s.upper(), family="avenir next condensed",
                alpha=.5, ha=text_align,
                va="center", fontsize=20)

    # FIGURE
    fig.text(x=.5125, y=.95,
             s=f"{focus_player_name}\n"
               f"{metric_one_rename} vs {metric_two_rename}".upper(),
             color="black",
             family="avenir next condensed",
             fontsize=34, ha="center", va="center")

    fig.text(x=.5125, y=.9,
             s=f"A scatter plot of {position_group.replace('_', ' ')}'s to player at least {min_minutes} Minutes".upper(),
             color="black",
             family="avenir",
             fontsize=18, ha="center", va="center")

    fig.set_facecolor("none")
    plt.savefig(
        f"/Users/russellforbes/PycharmProjects/RF_Data_Analyst/c_analysis/a_data_visualisations/player_position_scatter_{focus_player_id}_{metric_one}_{metric_two}.png",
        dpi=300,
        bbox_inches="tight",
        edgecolor="none",
        transparent=True)

    plt.close()


raw_scatter_metric_dict = {"pass_obv_per_90": "Pass OBV",
                           "total_dribble_carry_obv_per_90": "Carry OBV"}

create_obv_scatter(6655, "Central / Defensive Midfielder", 300, raw_scatter_metric_dict)
