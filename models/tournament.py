from pathlib import Path
from typing import List

from tinydb import TinyDB, where

from models.player import Player
from models.match import Match
from models.round import Round


db = TinyDB(Path(__file__).parent.parent / "db.json", indent=4)
tournaments_table = db.table("tournaments")


class Tournament():

    def __init__(
        self,
        name: str,
        description: str,
        location: str,
        time_control: str,
        date: str,
        total_rounds: int = 4,
        rounds_completed: int = 0,
        players: List[Player] = [],
        rounds: List[Round] = [],
    ):
        self.id = -1
        self.name = name.title()
        self.description = description
        self.location = location.title()
        self.time_control = time_control
        self.date = date
        self.total_rounds = total_rounds
        self.rounds_completed = rounds_completed
        self.players = players
        self.rounds = rounds

    def __str__(self):
        return (
            f"\nID {self.id}" +
            f"\t{self.name}" + "\n"
            f"\tDescription : {self.description}" + "\n"
            f"\tLieu : {self.location}" + "\n"
            f"\tContrôle de temps : {self.time_control}" + "\n"
            f"\tDate : {self.date}" + "\n"
            f"\tNombre de joueurs : {len(self.players)}" + "\n"
            f"\tTours réalisés : {self.rounds_completed} / {self.total_rounds}"
        )

    @property
    def serialized(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "time_control": self.time_control,
            "date": self.date,
            "total_rounds": self.total_rounds,
            "rounds_completed": self.rounds_completed,
            "players": [player.serialized for player in self.players],
            "rounds": [round.serialized for round in self.rounds],
        }

    def save(self):
        if self.id < 0:
            self.id = tournaments_table.insert(self.serialized)
            tournaments_table.update({"id": self.id}, doc_ids=[self.id])
        else:
            tournaments_table.update(
                self.serialized,
                where("id") == self.id  # type: ignore
            )

    def get_players_sorted_by_name(self) -> List[Player]:
        return sorted(
            self.players,
            key=lambda player: player.name
        )

    def get_players_sorted_by_ranking(self) -> List[Player]:
        return sorted(
            self.players,
            key=lambda player: (player.ranking, player.name)
        )

    def get_players_sorted_by_points(self) -> List[Player]:
        return sorted(
            self.players,
            key=lambda player: (player.points, player.ranking, player.name),
            reverse=True
        )

    def add_player(self, player: Player):
        self.players.append(player)
        self.save()

    def add_round(self):
        if self.rounds_completed == self.total_rounds:
            print("Le tournois est terminé.")
        else:
            round_name = f"Round {self.rounds_completed + 1}"
            round = Round(round_name)
            round.save()
            self.rounds.append(round)

    def add_matches(self):
        current_round = self.rounds[-1]
        if self.rounds_completed == 0:  # first_round
            players = self.get_players_sorted_by_ranking()
            best_players = players[:len(players)//2]
            print("best_players")
            print([p.name + " " for p in best_players])
            worst_players = players[len(players)//2:]
            print("worst_players")
            print([p.name + " " for p in worst_players])
            for player_1, player_2 in zip(best_players, worst_players):
                player_1.opponent_ids.append(player_2.id)
                player_2.opponent_ids.append(player_1.id)
                match = Match(player_1, player_2)
                match.save()
                current_round.add_match(match)
        else:
            players = self.get_players_sorted_by_ranking()
            even_players = [p for i, p in enumerate(players)if i % 2 == 0]
            odd_players = [p for i, p in enumerate(players) if i % 2 != 0]
            while even_players != []:
                player_1 = even_players[0]
                player_2 = odd_players[0]
                if player_1.already_played(player_2):
                    odd_players = odd_players[1:] + odd_players[:1]
                    continue
                even_players.remove(player_1)
                odd_players.remove(player_2)
                player_1.opponent_ids.append(player_2.id)
                player_2.opponent_ids.append(player_1.id)
                match = Match(player_1, player_2)
                match.save()
                current_round.add_match(match)
                odd_players = sorted(
                    odd_players,
                    key=lambda player: (player.points, player.ranking),
                    reverse=True
                )

    def start_round(self):
        self.add_round()
        self.add_matches()
        self.save()

    def finish_round(self):
        current_round = self.rounds[-1]
        current_round.finish()
        self.rounds_completed += 1
        self.save()
