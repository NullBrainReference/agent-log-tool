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

if __name__ == "__main__":
    games, actions, events = load_data()
    print("Loaded:", len(games), "games")
    analyze_winrate(games)
    plot_score_trend(games)
