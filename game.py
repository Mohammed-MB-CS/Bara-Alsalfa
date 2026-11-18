"""Stage 3: the game rules, with no UI and no network.

Everything the game needs to be correct lives here, so it can be tested
without opening a window.
"""

import random


def choose_category(data, name=None):
    """Return one category dict from words.json. Random if no name is given."""
    if name is None:
        return random.choice(data["categories"])
    for cat in data["categories"]:
        if cat["name"] == name:
            return cat
    raise ValueError(f"no category named {name}")


class Game:
    def __init__(self, players, words):
        if len(players) < 3:
            raise ValueError("need at least 3 players")
        if len(set(players)) != len(players):
            raise ValueError("player names must be unique")

        self.players = list(players)
        self.word = random.choice(words)
        self.spy = random.choice(self.players)
        self.round = 0
        self.last_pair = None
        self.played = set()  # everybody who has asked or answered at least once
        self.scores = {name: 0 for name in self.players}

    def next_pair(self):
        """Pick (asker, answerer). The same pair cannot repeat back to back."""
        self.round += 1

        # every ordered pair of different players
        pairs = [(a, b) for a in self.players for b in self.players if a != b]

        # drop the previous pair, in both orders
        if self.last_pair:
            last = self.last_pair
            reverse = self.last_pair[::-1]
            pairs = [p for p in pairs if p != last and p != reverse]

        # while somebody has not played yet, every round must include him,
        # and two newcomers together when we can, so nobody waits long
        newcomers = [p for p in self.players if p not in self.played]
        if newcomers:
            both = [p for p in pairs if p[0] in newcomers and p[1] in newcomers]
            fresh = [p for p in pairs if p[0] in newcomers or p[1] in newcomers]
            if both:
                pairs = both
            elif fresh:
                pairs = fresh

        pair = random.choice(pairs)
        self.last_pair = pair
        self.played.add(pair[0])
        self.played.add(pair[1])
        return pair

    def everyone_played(self):
        return len(self.played) == len(self.players)

    def majority_wants_vote(self, wanted):
        """True when more than half the players pressed 'go to vote'."""
        return wanted > len(self.players) / 2

    def should_vote(self, wanted=0):
        """Voting starts when everybody has played, and round 10 or the
        majority asks for it."""
        if not self.everyone_played():
            return False
        return self.round >= 10 or self.majority_wants_vote(wanted)

    def finish(self, votes, guess=None):
        """Apply the rules and return what happened.

        votes: {voter_name: accused_name}
        guess: what the spy said the word was, or None if he did not guess
        """
        spy_guessed = guess is not None and guess.strip() == self.word

        for voter, accused in votes.items():
            if accused == self.spy:
                self.scores[voter] += 1

        if spy_guessed:
            self.scores[self.spy] += 2

        return {
            "spy": self.spy,
            "word": self.word,
            "spy_guessed": spy_guessed,
            "correct_voters": [v for v, a in votes.items() if a == self.spy],
        }
