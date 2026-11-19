"""Stage 3 tests: one test per rule.

Run:  python test_game.py
"""

from game import SPY_CARD, Category, Game, choose_category, parse_players


def test_scoring():
    # A voter who picks the spy gets +1, even if everybody else picked wrong.
    g = Game(["A", "B", "C", "D"], ["كبسة"])
    g.spy = "A"  # forced, so the test always checks the same thing

    g.finish({"A": "B", "B": "A", "C": "B", "D": "B"}, guess=None)

    assert g.scores["B"] == 1, "the one correct voter must get 1"
    assert g.scores["C"] == 0, "wrong voters get nothing"
    assert g.scores["D"] == 0
    assert g.scores["A"] == 0, "a caught spy with no guess gets nothing"


def test_spy_points():
    # The spy gets +2 only when the guess is right.
    right = Game(["A", "B", "C"], ["كبسة"])
    right.spy = "A"
    result = right.finish({"A": "B", "B": "A", "C": "A"}, guess="كبسة")

    assert result["spy_guessed"] is True
    assert right.scores["A"] == 2
    assert right.scores["B"] == 1, "voters keep their point even when the spy wins"

    wrong = Game(["A", "B", "C"], ["كبسة"])
    wrong.spy = "A"
    result = wrong.finish({"A": "B", "B": "A", "C": "A"}, guess="مندي")

    assert result["spy_guessed"] is False
    assert wrong.scores["A"] == 0


def test_pair_rule():
    # The same pair never repeats back to back, in either order.
    g = Game(["A", "B", "C", "D"], ["كبسة"])
    previous = None

    for _ in range(60):
        pair = g.next_pair()
        assert pair[0] != pair[1], "a player cannot ask himself"
        if previous:
            assert pair != previous, "same pair twice in a row"
            assert pair != previous[::-1], "same pair in reverse order"
        previous = pair

    assert g.round == 60


def test_min_players():
    # Three is the minimum: two players cannot respect the pair rule.
    for names in (["A"], ["A", "B"]):
        try:
            Game(names, ["كبسة"])
            raise AssertionError("fewer than 3 players must raise")
        except ValueError:
            pass

    Game(["A", "B", "C"], ["كبسة"])  # three is accepted


def test_duplicate_names():
    # Two players with one name would share one score line.
    try:
        Game(["A", "A", "B"], ["كبسة"])
        raise AssertionError("repeated names must raise")
    except ValueError:
        pass


def test_empty_words():
    # An empty category must say so instead of failing inside random.choice.
    try:
        Game(["A", "B", "C"], [])
        raise AssertionError("a category with no words must raise")
    except ValueError:
        pass


def test_parse_players():
    # One name per line; blank lines and stray spaces are ignored.
    assert parse_players(" علي\n\nسارة \n") == ["علي", "سارة"]
    assert parse_players("") == []


def test_everyone_played():
    # Nobody sits out: every player appears within a few rounds.
    players = ["A", "B", "C", "D", "E", "F"]
    g = Game(players, ["كبسة"])
    assert g.everyone_played() is False, "nobody has played at round 0"

    while not g.everyone_played():
        g.next_pair()
        assert g.round <= len(players), "too many rounds to involve everybody"

    assert g.played == set(players)


def test_end_condition():
    g = Game(["A", "B", "C", "D"], ["كبسة"])
    g.played = {"A", "B", "C"}  # forced: D has not played
    g.round = 10

    assert g.should_vote() is False, "round 10 is not enough while someone has not played"

    g.played.add("D")
    assert g.should_vote() is True, "round 10 with everybody played"


def test_requests_survive_round():
    # A request made before a round still counts after it.
    g = Game(["A", "B", "C", "D"], ["كبسة"])
    g.played = set(g.players)  # forced: everybody has played
    g.request_vote()
    g.request_vote()
    g.next_pair()

    assert g.should_vote() is False, "2 of 4 is not a majority"
    g.request_vote()
    assert g.should_vote() is True, "the two older requests plus this one"


def test_request_ignored_until_everyone_played():
    # Pressing does not start a vote while somebody has not played, but the
    # press is not thrown away either.
    g = Game(["A", "B", "C", "D"], ["كبسة"])
    g.played = {"A", "B", "C"}  # forced: D has not played
    for _ in range(3):
        g.request_vote()

    assert g.should_vote() is False, "somebody has not played"

    g.played.add("D")
    assert g.should_vote() is True, "the same three requests now count"


def test_ten_rounds():
    # Round 10 ends the questions with zero requests.
    g = Game(["A", "B", "C", "D"], ["كبسة"])
    g.played = set(g.players)

    g.round = 9
    assert g.should_vote() is False
    g.round = 10
    assert g.should_vote() is True


def test_advance():
    # One call moves a round: a pair to ask, or "the questions are over".
    g = Game(["A", "B", "C", "D"], ["كبسة"])
    assert g.advance() == g.last_pair, "round 1 asks a question"
    assert g.round == 1

    g.played = set(g.players)  # forced: everybody has played
    g.round = 8
    assert g.advance() == g.last_pair, "round 9 is the last question"
    assert g.round == 9
    assert g.advance() is None, "round 10 closes the questions"


def test_majority():
    # Exactly half is not a majority; one more is.
    g = Game(["A", "B", "C", "D"], ["كبسة"])
    g.played = set(g.players)
    assert g.votes_needed() == 3

    g.request_vote()
    g.request_vote()
    assert g.should_vote() is False, "2 of 4 is exactly half"

    g.request_vote()
    assert g.should_vote() is True, "3 of 4 is a majority"


def test_vote_clears_requests():
    g = Game(["A", "B", "C", "D"], ["كبسة"])
    g.played = set(g.players)
    for _ in range(3):
        g.request_vote()
    assert g.should_vote() is True

    g.start_vote()
    assert g.vote_requests == 0, "the requests that started the vote are used up"
    assert g.should_vote() is False, "the next round starts with no requests"


def test_spy_guess_is_exact():
    # Only the exact word from the list scores. "لم يعرف" arrives as None.
    for guess, expected in ((None, 0), ("مندي", 0), ("كبسة", 2)):
        g = Game(["A", "B", "C"], ["كبسة"])
        g.spy = "A"
        g.finish({"A": "B", "B": "A", "C": "B"}, guess=guess)

        assert g.scores["A"] == expected, "spy points"
        assert g.scores["B"] == 1, "voters keep their point either way"


def test_vote_must_name_everybody():
    # A ballot is one entry per player: none missing, none invented.
    ballots = (
        {},
        {"B": "A", "C": "A"},
        {"B": "A", "C": "B", "Z": "A"},
    )
    for votes in ballots:
        g = Game(["A", "B", "C"], ["كبسة"])
        g.spy = "A"
        try:
            g.finish(votes)
            raise AssertionError(f"incomplete ballot accepted: {votes}")
        except ValueError:
            pass


def test_no_self_vote():
    # Nobody may accuse himself, and the screen is only offered legal names.
    g = Game(["A", "B", "C"], ["كبسة"])
    g.spy = "A"
    assert g.choices_for("B") == ["A", "C"], "a player cannot accuse himself"

    try:
        g.finish({"A": "A", "B": "A", "C": "A"})
        raise AssertionError("a self-vote must raise")
    except ValueError:
        pass


def test_finish_once():
    # Scores move once, however many times the button is pressed.
    g = Game(["A", "B", "C"], ["كبسة"])
    g.spy = "A"
    ballot = {"A": "B", "B": "A", "C": "A"}
    g.finish(ballot)
    points = dict(g.scores)

    try:
        g.finish(ballot)
        raise AssertionError("a second finish must raise")
    except ValueError:
        pass
    assert g.scores == points, "scores must not move on the second call"


def test_play_again_keeps_the_match():
    # A new round keeps the players, the category and the scores. Only leaving
    # for home or cancelling the game starts a new match.
    g = Game(["A", "B", "C"], ["كبسة", "مندي"])
    g.spy = "A"
    g.finish({"A": "B", "B": "A", "C": "A"}, guess=None)
    points = dict(g.scores)

    g.start_again()

    assert g.scores == points, "scores carry into the next round"
    assert g.words == ["كبسة", "مندي"], "the category is chosen once"
    assert g.round == 0 and g.played == set(), "the round starts over"
    assert g.finished is False, "the next round may finish"

    g.spy = "B"
    g.finish({"A": "B", "B": "A", "C": "B"}, guess=None)
    assert g.scores["A"] == 1, "A's first point"
    assert g.scores["C"] == 2, "C keeps last round's point and adds one"


def test_reveal():
    # One card per player, in the order the phone is passed.
    g = Game(["A", "B", "C"], ["كبسة"])
    g.spy = "B"
    cards = g.reveal()

    assert [name for name, text, is_spy in cards] == ["A", "B", "C"], "player order"
    assert sum(is_spy for name, text, is_spy in cards) == 1, "exactly one spy"
    for name, text, is_spy in cards:
        assert text == (SPY_CARD if name == "B" else g.word), name


def test_category():
    cats = [Category("أكلات", ["كبسة"]), Category("أماكن", ["درة"])]

    assert choose_category(cats) in cats
    assert choose_category(cats, "أكلات").words == ["كبسة"]

    try:
        choose_category(cats, "لا يوجد")
        raise AssertionError("a missing category must raise")
    except ValueError:
        pass


if __name__ == "__main__":
    tests = [
        test_scoring,
        test_spy_points,
        test_spy_guess_is_exact,
        test_pair_rule,
        test_min_players,
        test_duplicate_names,
        test_empty_words,
        test_parse_players,
        test_everyone_played,
        test_end_condition,
        test_requests_survive_round,
        test_request_ignored_until_everyone_played,
        test_ten_rounds,
        test_advance,
        test_majority,
        test_vote_clears_requests,
        test_vote_must_name_everybody,
        test_no_self_vote,
        test_finish_once,
        test_play_again_keeps_the_match,
        test_reveal,
        test_category,
    ]
    for test in tests:
        test()
        print("ok  ", test.__name__)
    print("all tests passed")
