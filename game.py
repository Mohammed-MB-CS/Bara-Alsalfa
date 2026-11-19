"""Stage 3: the game rules, with no UI and no network.

Everything the game needs to be correct lives here, so it can be tested
without opening a window.

The Arabic in this file is not UI: it is the answer a rule gives, and the
screens draw it as it comes back. One copy, so the two cannot drift.
"""

import random

# The spy's card. The break is where the card wants it.
SPY_CARD = "أنت برا\nالسالفة"


class Category:
    """One category of the word list: a name and the words in it."""

    def __init__(self, name, words):
        self.name = name
        self.words = words


def parse_players(text):
    """One name per line. Blank lines and stray spaces are ignored."""
    return [line.strip() for line in text.splitlines() if line.strip()]


def choose_category(categories, name=None):
    """Return one category from the list. Random if no name is given."""
    if name is None:
        return random.choice(categories)
    for cat in categories:
        if cat.name == name:
            return cat
    raise ValueError(f"no category named {name}")


class Game:
    def __init__(self, players, words):
        # The messages are what the setup screen shows, so they live next to
        # the rule that refuses the input instead of a second copy on screen.
        if len(players) < 3:
            raise ValueError("تحتاج 3 لاعبين على الأقل")
        if len(set(players)) != len(players):
            raise ValueError("لا تكرر نفس الاسم مرتين")
        if not words:
            raise ValueError("لا توجد كلمات في هذه الفئة")

        self.players = list(players)
        self.words = list(words)  # the category, kept for the next round
        self.word = random.choice(words)
        self.spy = random.choice(self.players)
        self.round = 0
        self.last_pair = None
        self.played = set()  # everybody who has asked or answered at least once
        self.vote_requests = 0  # presses of "we want to vote", kept across rounds
        self.scores = {name: 0 for name in self.players}
        self.finished = False

    def start_again(self):
        """A new round for the same match.

        The players, the category and the scores stay: only leaving for home
        or cancelling the game ends a match. Everything a single round owns
        starts over, so the spy and the word are picked again.
        """
        self.word = random.choice(self.words)
        self.spy = random.choice(self.players)
        self.round = 0
        self.last_pair = None
        self.played = set()
        self.vote_requests = 0
        self.finished = False

    def reveal(self):
        """The cards in the order the phone is passed.

        Each is (player, text, is_spy): only the spy gets the card, everybody
        else gets the word.
        """
        return [
            (name, SPY_CARD, True) if name == self.spy else (name, self.word, False)
            for name in self.players
        ]

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

    def advance(self):
        """The next question, or None when the questions are over.

        The pair is made before the vote is checked, so round 10 is still the
        round that closes the questions. By then everybody has played, so
        marking that pair as played changes nothing.
        """
        self.next_pair()
        return None if self.should_vote() else self.last_pair

    def everyone_played(self):
        return len(self.played) == len(self.players)

    def votes_needed(self):
        """How many requests make a majority."""
        return len(self.players) // 2 + 1

    def request_vote(self):
        """One player pressed 'we want to vote'."""
        self.vote_requests += 1

    def should_vote(self):
        """Voting starts when everybody has played, and round 10 or the
        majority asked for it. Requests are not per round, so one made in
        round 3 still counts in round 7."""
        if not self.everyone_played():
            return False
        return self.round >= 10 or self.vote_requests >= self.votes_needed()

    def start_vote(self):
        """Voting begins, so the requests that caused it are used up."""
        self.vote_requests = 0

    def choices_for(self, voter):
        """Who this player may accuse: everybody else."""
        return [name for name in self.players if name != voter]

    def finish(self, votes, guess=None):
        """Apply the rules and return what happened.

        votes: {voter_name: accused_name}, one entry per player
        guess: what the spy said the word was, or None if he did not guess
        """
        # A bad ballot is refused here rather than trusted from the screen
        # that built it, so the scores mean something from anywhere.
        if self.finished:
            raise ValueError("النقاط تُحسب مرة واحدة")
        if set(votes) != set(self.players):
            raise ValueError("كل لاعب يصوّت مرة واحدة")
        if any(accused not in self.players for accused in votes.values()):
            raise ValueError("التصويت على لاعب من اللعبة")
        if any(voter == accused for voter, accused in votes.items()):
            raise ValueError("لا يصوّت اللاعب على نفسه")

        spy_guessed = guess is not None and guess.strip() == self.word

        for voter, accused in votes.items():
            if accused == self.spy:
                self.scores[voter] += 1

        if spy_guessed:
            self.scores[self.spy] += 2

        self.finished = True

        return {
            "spy": self.spy,
            "word": self.word,
            "spy_guessed": spy_guessed,
            "correct_voters": [v for v, a in votes.items() if a == self.spy],
        }
