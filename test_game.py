"""Stage 3 tests: one test per rule.

Run:  python test_game.py
"""

from game import Game, choose_category


def test_scoring():
    # A voter who picks the spy gets +1, even if everybody else picked wrong.
    g = Game(["A", "B", "C", "D"], ["كبسة"])
    g.spy = "A"  # forced, so the test always checks the same thing

    g.finish({"B": "A", "C": "B", "D": "B"}, guess=None)

    assert g.scores["B"] == 1, "the one correct voter must get 1"
    assert g.scores["C"] == 0, "wrong voters get nothing"
    assert g.scores["D"] == 0
    assert g.scores["A"] == 0, "a caught spy with no guess gets nothing"


def test_spy_points():
    # The spy gets +2 only when the guess is right.
    right = Game(["A", "B", "C"], ["كبسة"])
    right.spy = "A"
    result = right.finish({"B": "A", "C": "A"}, guess="كبسة")

    assert result["spy_guessed"] is True
    assert right.scores["A"] == 2
    assert right.scores["B"] == 1, "voters keep their point even when the spy wins"

    wrong = Game(["A", "B", "C"], ["كبسة"])
    wrong.spy = "A"
    result = wrong.finish({"B": "A", "C": "A"}, guess="مندي")

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

    h = Game(["A", "B", "C", "D"], ["كبسة"])
    h.played = {"A", "B", "C", "D"}
    assert h.should_vote(0) is False, "round 0, nobody asked"
    assert h.should_vote(2) is False, "2 of 4 is not a majority"
    assert h.should_vote(3) is True, "3 of 4 is a majority"


def test_category():
    data = {"categories": [{"name": "أكلات", "words": ["كبسة"]}]}

    assert choose_category(data)["name"] == "أكلات"
    assert choose_category(data, "أكلات")["words"] == ["كبسة"]

    try:
        choose_category(data, "لا يوجد")
        raise AssertionError("a missing category must raise")
    except ValueError:
        pass


if __name__ == "__main__":
    tests = [
        test_scoring,
        test_spy_points,
        test_pair_rule,
        test_min_players,
        test_everyone_played,
        test_end_condition,
        test_category,
    ]
    for test in tests:
        test()
        print("ok  ", test.__name__)
    print("all tests passed")
