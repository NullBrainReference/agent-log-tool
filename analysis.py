import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

DB_PATH = "games.db"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    games = pd.read_sql_query("SELECT * FROM games", conn)
    actions = pd.read_sql_query("SELECT * FROM actions", conn)
    events = pd.read_sql_query("SELECT * FROM events", conn)
    conn.close()
    return games, actions, events

def analyze_winrate(games: pd.DataFrame):
    games["win"] = games["result"].apply(lambda r: 1 if r == "win" else 0)
    winrate = games["win"].mean()
    print(f"Winrate: {winrate:.2%}")
    return winrate

def plot_score_trend(games: pd.DataFrame):
    plt.figure(figsize=(8,4))
    plt.plot(games["id"], games["totalScore"], marker="o")
    plt.xlabel("Game ID")
    plt.ylabel("Total Score")
    plt.title("Score trend over games")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_heals(events):
    heals = events[events["eventType"] == "Heal"]
    heals_per_game = heals.groupby("game_id").size()
    heals_per_game.plot(kind="bar", figsize=(8,4))
    plt.title("Количество лечений по играм")
    plt.xlabel("Game ID")
    plt.ylabel("Heals")
    plt.tight_layout()
    plt.show()

def plot_attack_ratio(events):
    hits = events[events["eventType"].isin(["RedHit","WhiteHit"])]
    counts = hits.groupby(["game_id","eventType"]).size().unstack(fill_value=0)
    counts.plot(kind="bar", stacked=True, figsize=(10,5))
    plt.title("Соотношение атак (Red vs White)")
    plt.xlabel("Game ID")
    plt.ylabel("Hits")
    plt.tight_layout()
    plt.show()

def plot_attacks_by_unit(actions):
    attacks = actions[actions["actionType"]=="attack"]
    counts = attacks.groupby("unitType").size()
    counts.plot(kind="bar", figsize=(8,4))
    plt.title("Количество атак по типам юнитов")
    plt.xlabel("Unit Type")
    plt.ylabel("Attacks")
    plt.tight_layout()
    plt.show()

def plot_attacks_by_team(actions):
    attacks = actions[actions["actionType"]=="attack"].copy()
    attacks["team"] = attacks["order"].apply(lambda x: "Red" if x%2==0 else "White")
    counts = attacks.groupby(["team","unitType"]).size().unstack(fill_value=0)
    counts.plot(kind="bar", figsize=(10,5))
    plt.title("Атаки по юнитам и командам")
    plt.xlabel("Team")
    plt.ylabel("Attacks")
    plt.tight_layout()
    plt.show()


def red_leader_heals(actions: pd.DataFrame) -> pd.DataFrame:
    heals = actions[
        (actions["actionType"] == "respawn") &
        (actions["unitType"] == "DefaultLeader") &
        (actions["order"] % 2 == 0)
    ]
    heals_per_game = heals.groupby("game_id").size()
    return heals_per_game

def red_leader_damage(events: pd.DataFrame) -> pd.DataFrame:
    damage = events[events["eventType"] == "RedLeaderHit"]
    damage_per_game = damage.groupby("game_id").size()
    return damage_per_game

def plot_red_leader_heals_vs_damage(actions: pd.DataFrame, events: pd.DataFrame):
    heals_per_game = red_leader_heals(actions)
    damage_per_game = red_leader_damage(events)

    df = pd.DataFrame({
        "Heals": heals_per_game,
        "Damage": damage_per_game
    }).fillna(0)

    plt.figure(figsize=(10,5))
    plt.plot(df.index, df["Damage"], label="RedLeaderHit (урон)", marker="o", color="red")
    plt.plot(df.index, df["Heals"], label="Heals (лечения)", marker="s", color="green")
    plt.xlabel("Game ID")
    plt.ylabel("Количество событий")
    plt.title("Урон по красному лидеру vs его лечения")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def red_attack_efficiency(actions: pd.DataFrame, events: pd.DataFrame):
    planned = actions[
        (actions["actionType"] == "attack") &
        (actions["order"] % 2 == 0)
    ].groupby(["game_id", "round"]).size().rename("Planned")

    realized = events[events["eventType"] == "RedHit"] \
        .groupby(["game_id", "round"]).size().rename("Realized")

    df = pd.concat([planned, realized], axis=1).fillna(0)
    # Ивенты атаки поднимаются за попадание и сам урон тоесть дважды
    df["Realized"] = df["Realized"] / 2

    per_game = df.groupby("game_id")[["Planned", "Realized"]].sum()
    per_game["Efficiency"] = per_game["Realized"] / per_game["Planned"]

    return per_game

def plot_red_attack_efficiency(actions, events):
    per_game = red_attack_efficiency(actions, events)

    plt.figure(figsize=(10,5))
    plt.bar(per_game.index, per_game["Efficiency"], color="crimson")
    plt.xlabel("Game ID")
    plt.ylabel("Эффективность атак (Realized / Planned)")
    plt.title("Эффективность атак красной команды по играм")
    plt.ylim(0,3.05)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.show()

    print(per_game)

def red_attack_share(actions: pd.DataFrame):
    red_actions = actions[actions["order"] % 2 == 0]
    total_per_game = red_actions.groupby("game_id").size().rename("AllActions")

    attacks_per_game = red_actions[red_actions["actionType"] == "attack"] \
        .groupby("game_id").size().rename("Attacks")

    df = pd.concat([total_per_game, attacks_per_game], axis=1).fillna(0)
    df["AttackShare"] = df["Attacks"] / df["AllActions"]

    return df

def plot_red_attack_share(actions):
    df = red_attack_share(actions)

    plt.figure(figsize=(10,5))
    plt.bar(df.index, df["AttackShare"], color="darkred")
    plt.xlabel("Game ID")
    plt.ylabel("Доля атак среди всех действий")
    plt.title("Доля атак красной команды по играм")
    plt.ylim(0,1.05)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.show()

    print(df)

def red_units_usage(actions: pd.DataFrame):
    red_actions = actions[actions["order"] % 2 == 0]
    usage = red_actions.groupby(["game_id", "unitType"]).size().unstack(fill_value=0)
    return usage

def plot_red_units_usage(actions: pd.DataFrame):
    usage = red_units_usage(actions)

    usage.plot(kind="bar", stacked=False, figsize=(12,6), colormap="tab20")
    plt.xlabel("Game ID")
    plt.ylabel("Количество действий")
    plt.title("Интенсивность использования юнитов красной команды по играм")
    plt.legend(title="Unit Type")
    plt.tight_layout()
    plt.show()

    print("Таблица использования юнитов:\n", usage)

def slice_games(games, actions, events, start_id=None, end_id=None):
    if start_id is not None:
        games = games[games["id"] >= start_id]
        actions = actions[actions["game_id"] >= start_id]
        events = events[events["game_id"] >= start_id]
    if end_id is not None:
        games = games[games["id"] <= end_id]
        actions = actions[actions["game_id"] <= end_id]
        events = events[events["game_id"] <= end_id]
    return games, actions, events

def cut_loses(games, actions, events):
    games = games[games["result"] == "win"]

    win_ids = games["id"].unique()
    actions = actions[actions["game_id"].isin(win_ids)]
    events = events[events["game_id"].isin(win_ids)]
    return games, actions, events

if __name__ == "__main__":
    games, actions, events = load_data()
    games, actions, events = slice_games(games, actions, events, start_id=28, end_id=50)
    print("Loaded:", len(games), "games")
    # analyze_winrate(games)
    # plot_score_trend(games)

    plot_heals(events)
    plot_attack_ratio(events)
    plot_attacks_by_team(actions)
    plot_red_leader_heals_vs_damage(actions, events)
    plot_red_attack_efficiency(actions, events)
    plot_red_attack_share(actions)
    plot_red_units_usage(actions)



