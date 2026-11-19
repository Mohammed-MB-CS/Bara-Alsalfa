"""برا السالفة — the app.

Stage 5: the screens, the Arabic font, the reveal animation, vibration.
Run with:  python app.py
"""

import flet as ft

import words
from game import Game, choose_category, parse_players


# ---------------------------------------------------------------- style
# "سوق الليل": one dark ground, one panel, and one accent per phase of the
# game. The colour tells you where you are before you read a word.
INK = "#0B1B22"  # the ground, on every screen
PANEL = "#12313B"  # fields, cards, the word
TEXT = "#F2EBDD"  # body text: warm off-white, easier at night than pure white
MUTED = "#86A2A8"  # captions: "يسأل:", "1 من 4"
CORAL = "#FF7059"  # play: the button that starts or advances something
SAFFRON = "#F4B740"  # talk: the round screen
MINT = "#7FD8BE"  # the word you were dealt
SPY = "#C1334D"  # you are out of the loop
ON_CORAL = "#23120E"  # text on coral
ON_SAFFRON = "#231C08"  # text on saffron
ON_SPY = "#F6E9E4"  # text on the spy card
EDGE = "#1D4A57"  # hairlines: borders and dividers


# ---------------------------------------------------------------- screens


def main(page: ft.Page):
    page.title = "برا السالفة"
    page.rtl = True
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    # The font ships inside the app, in assets/fonts/. Tajawal because it is a
    # static font: Flet cannot load variable fonts yet.
    page.fonts = {
        "Tajawal": "/fonts/Tajawal-Regular.ttf",
        "Tajawal Bold": "/fonts/Tajawal-Bold.ttf",
    }

    theme = ft.Theme(font_family="Tajawal")

    # Both themes, because the app is dark: with theme_mode DARK, Flet uses
    # dark_theme, and a font set only on theme would be ignored.
    page.theme = theme
    page.dark_theme = theme
    page.bgcolor = INK

    # One shape for every button and field, so the screens feel like one app.
    radius = ft.RoundedRectangleBorder(radius=14)

    def action(label, on_click, color=CORAL, on_color=ON_CORAL, width=300, height=56):
        return ft.FilledButton(
            label,
            on_click=on_click,
            width=width,
            height=height,
            bgcolor=color,
            color=on_color,
            elevation=0,
            style=ft.ButtonStyle(
                shape=radius,
                text_style=ft.TextStyle(size=16, font_family="Tajawal Bold"),
            ),
        )

    def quiet(label, on_click, color=MUTED):
        return ft.TextButton(
            label,
            on_click=on_click,
            style=ft.ButtonStyle(
                color=color,
                shape=radius,
                text_style=ft.TextStyle(size=14, font_family="Tajawal"),
            ),
        )

    # One size for the name of a screen, so every screen starts the same way.
    def title(text, color=TEXT):
        return ft.Text(text, size=30, font_family="Tajawal Bold", color=color)

    # A field's name sits above it, flush to the same edge as the field.
    def caption(text, width=300):
        return ft.Text(
            text,
            size=13,
            color=MUTED,
            width=width,
            text_align=ft.TextAlign.RIGHT,
        )

    haptics = ft.HapticFeedback()

    def buzz():
        """One short vibration. Phones only: a desktop has nothing to shake."""
        if page.platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS):
            page.run_task(haptics.vibrate)

    # everything the screens share
    S = {
        "game": None,  # the Game object, once a game starts
        "names": "",  # last names typed, to prefill next time
        "reveal": 0,  # whose card is on screen
        "shown": False,  # reveal: is the card open?
        "voter": 0,  # whose turn it is to vote
        "votes": {},  # voter -> accused
        "summary": None,  # result of game.finish()
        "words": [],  # the words of the chosen category, for the spy's pick
    }

    def show(*controls, center=False):
        """One screen = one scrollable column.

        Without the scroll, a long word list on a small phone is clipped at the
        bottom edge and cannot be reached.
        """
        page.controls.clear()
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.add(
            ft.Column(
                list(controls),
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=(
                    ft.MainAxisAlignment.CENTER
                    if center
                    else ft.MainAxisAlignment.START
                ),
            )
        )
        page.update()

    # ------------------------------------------------------------ home

    def home():
        cats = words.load()

        # one line that holds either the count or the sync result,
        # so the buttons above it never move
        status = ft.Text(
            f"عدد الفئات: {len(cats)}" if cats else "لا توجد كلمات بعد",
            color=MUTED,
            size=13,
        )

        def refresh(e):
            status.value = "جاري التحديث..."
            status.color = MUTED
            page.update()

            # the address check, the download, the fallback and the message
            # are all words.sync's business; this only draws what comes back
            found, message, ok = words.sync(words.saved_address())
            status.value = f"{message} — عدد الفئات: {len(found)}" if ok else message
            status.color = MINT if ok else CORAL
            page.update()

        show(
            ft.Text("برا السالفة", size=40, font_family="Tajawal Bold", color=TEXT),
            ft.Text("لعبة الجاسوس", size=14, color=MUTED),
            ft.Container(height=36),
            action("لعبة جديدة", lambda e: setup()),
            quiet("تحديث الكلمات", refresh, color=MINT),
            quiet("الإعدادات", lambda e: settings()),
            ft.Container(height=14),
            ft.Container(alignment=ft.Alignment.CENTER, content=status),
            center=True,
        )

    # ------------------------------------------------------------ setup

    def setup():
        cats = words.load()
        if not cats:
            show(
                title("لا توجد كلمات محفوظة"),
                ft.Text("شغّل برنامج الحاسب ثم اضغط تحديث الكلمات", color=MUTED, size=14),
                ft.Container(height=10),
                action("تحديث الكلمات", lambda e: settings()),
                center=True,
            )
            return

        # Fields carry their name in a caption above them, not as Material's
        # floating label: that label straddles the border and looks broken once
        # the field has a hairline, and it collides with small widths.
        field = dict(
            filled=True,
            fill_color=PANEL,
            border_color=EDGE,
            border_width=1,
            focused_border_color=MINT,
            border_radius=14,
            text_size=17,
            color=TEXT,
            hint_style=ft.TextStyle(color=MUTED, size=14),
        )

        names = ft.TextField(
            hint_text="اسم في كل سطر",
            multiline=True,
            min_lines=4,
            width=300,
            value=S["names"],
            cursor_color=MINT,
            **field,
        )
        category = ft.Dropdown(
            value="عشوائي",
            width=300,
            options=[ft.DropdownOption(key="عشوائي", text="عشوائي")]
            + [ft.DropdownOption(key=cat.name, text=cat.name) for cat in cats],
            **field,
        )
        error = ft.Text("", color=CORAL, size=13)

        def start(e):
            # The screen does not decide who may play: it asks Game and draws
            # the refusal. Splitting the lines is all the typing it knows.
            try:
                chosen = choose_category(
                    cats, None if category.value == "عشوائي" else category.value
                )
                S["game"] = Game(parse_players(names.value), chosen.words)
            except ValueError as problem:
                error.value = str(problem)
                page.update()
                return

            S["names"] = names.value
            S["reveal"] = 0
            S["shown"] = False
            S["votes"] = {}
            S["summary"] = None
            S["words"] = chosen.words
            reveal()

        show(
            ft.Container(height=16),
            title("لاعبون"),
            ft.Container(height=14),
            caption("أسماء اللاعبين"),
            names,
            ft.Container(height=10),
            caption("الفئة"),
            category,
            ft.Container(height=22, alignment=ft.Alignment.CENTER, content=error),
            action("ابدأ", start),
            quiet("رجوع", lambda e: home()),
        )

    # ------------------------------------------------------------ reveal

    def reveal():
        g = S["game"]
        cards = g.reveal()
        if S["reveal"] >= len(cards):
            round_screen()
            return

        name, text, is_spy = cards[S["reveal"]]

        # Two faces of one card, same size, swapped inside an AnimatedSwitcher:
        # the word appears with a small pop, and the button under the card
        # never moves because the slot keeps its size.
        def face_down():
            return ft.Container(
                width=320,
                height=220,
                alignment=ft.Alignment.CENTER,
                content=ft.Column(
                    [
                        ft.Text("أعطِ الجوال إلى", color=MUTED, size=13),
                        ft.Text(name, size=36, font_family="Tajawal Bold", color=TEXT),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                ),
                bgcolor=PANEL,
                border=ft.Border.all(1, EDGE),
                border_radius=18,
            )

        def face_up():
            return ft.Container(
                width=320,
                height=220,
                alignment=ft.Alignment.CENTER,
                content=ft.Text(
                    text,
                    size=40 if is_spy else 46,
                    font_family="Tajawal Bold",
                    text_align=ft.TextAlign.CENTER,
                    color=ON_SPY if is_spy else MINT,
                ),
                bgcolor=SPY if is_spy else PANEL,
                border=None if is_spy else ft.Border.all(1.5, MINT),
                border_radius=18,
            )

        card = ft.AnimatedSwitcher(
            content=face_up() if S["shown"] else face_down(),
            width=320,
            height=220,
            duration=220,
            transition=ft.AnimatedSwitcherTransition.SCALE,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
        )
        button = action(
            "إخفاء وتمرير" if S["shown"] else "اضغط لعرض الكلمة",
            lambda e: tap(),
            width=320,
            height=64,
        )

        def tap():
            """First tap shows the word, the second hides it and passes on."""
            if S["shown"]:
                S["reveal"] += 1
                S["shown"] = False
                reveal()
                return

            S["shown"] = True
            card.content = face_up()
            button.content = "إخفاء وتمرير"
            buzz()
            page.update()

        show(
            card,
            ft.Container(height=8),
            button,
            ft.Container(height=12),
            ft.Container(
                height=24,
                alignment=ft.Alignment.CENTER,
                content=ft.Text(
                    f"{S['reveal'] + 1} من {len(g.players)}", color=MUTED, size=13
                ),
            ),
            center=True,
        )

    # ------------------------------------------------------------ round

    def round_screen():
        g = S["game"]
        if g.last_pair is None:
            g.next_pair()

        asker, answerer = g.last_pair

        show(
            ft.Text(f"يسأل: {asker}", size=15, color=MUTED),
            ft.Text(answerer, size=44, font_family="Tajawal Bold", color=TEXT),
            ft.Container(height=4),
            ft.Text("أجب بنعم أو لا", size=15, color=MUTED),
            ft.Container(height=30),
            action("الجولة التالية", lambda e: next_round(), color=SAFFRON, on_color=ON_SAFFRON),
            ft.OutlinedButton(
                "نريد التصويت",
                icon=ft.Icons.HOW_TO_VOTE,
                height=56,
                width=300,
                on_click=lambda e: ask_vote(),
                style=ft.ButtonStyle(
                    color=SAFFRON,
                    side=ft.BorderSide(1, EDGE),
                    shape=radius,
                ),
            ),
            ft.Container(height=8),
            ft.Container(
                height=22,
                alignment=ft.Alignment.CENTER,
                content=ft.Text(
                    f"طلبات التصويت: {g.vote_requests} من {g.votes_needed()}",
                    color=MUTED,
                    size=13,
                ),
            ),
            ft.Container(
                height=22,
                alignment=ft.Alignment.CENTER,
                content=ft.Text(
                    "" if g.everyone_played() else "التصويت يفتح بعد أن يلعب الجميع",
                    size=13,
                    color=SAFFRON,
                ),
            ),
            quiet("إلغاء اللعبة", lambda e: home()),
            center=True,
        )

    def next_round():
        # advance() answers "a pair to ask about, or the questions are over"
        if S["game"].advance() is None:
            vote_now()
        else:
            round_screen()

    def ask_vote():
        g = S["game"]
        g.request_vote()
        if g.should_vote():
            vote_now()
        else:
            round_screen()

    # ------------------------------------------------------------ vote

    def vote_now():
        """Voting begins: the requests that earned it are used up."""
        S["game"].start_vote()
        S["voter"] = 0
        S["votes"] = {}
        vote_screen()

    def vote_screen():
        g = S["game"]
        if S["voter"] >= len(g.players):
            result_screen()
            return

        voter = g.players[S["voter"]]

        def pick(accused):
            S["votes"][voter] = accused
            S["voter"] += 1
            vote_screen()

        show(
            title("التصويت", CORAL),
            ft.Container(height=6),
            ft.Text("أعطِ الجوال إلى", color=MUTED, size=14),
            ft.Text(voter, size=34, font_family="Tajawal Bold", color=TEXT),
            ft.Text("من تظنه برا السالفة؟", color=MUTED, size=15),
            ft.Container(height=16),
            *[
                ft.FilledButton(
                    name,
                    width=300,
                    height=56,
                    on_click=lambda e, n=name: pick(n),
                    bgcolor=PANEL,
                    color=TEXT,
                    elevation=0,
                    style=ft.ButtonStyle(
                        shape=radius,
                        side=ft.BorderSide(1, EDGE),
                        text_style=ft.TextStyle(size=17, font_family="Tajawal Bold"),
                    ),
                )
                for name in g.choices_for(voter)
            ],
            ft.Container(height=12),
            ft.Text(f"{S['voter'] + 1} من {len(g.players)}", color=MUTED, size=13),
            center=True,
        )

    # ------------------------------------------------------------ result

    def play_again(e):
        """Another round: same players, same category, scores kept.

        The setup screen is deliberately skipped. It is where a new match
        begins, and a new match is what resets the scores.
        """
        S["game"].start_again()
        S["reveal"] = 0
        S["shown"] = False
        S["votes"] = {}
        S["summary"] = None
        reveal()

    def result_screen():
        g = S["game"]

        if S["summary"] is None:
            # the word stays hidden until the spy has picked one
            def confirm(word):
                S["summary"] = g.finish(S["votes"], word)
                result_screen()

            picks = ft.Column(
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.FilledButton(
                        word,
                        width=300,
                        height=52,
                        on_click=lambda e, w=word: confirm(w),
                        bgcolor=PANEL,
                        color=TEXT,
                        elevation=0,
                        style=ft.ButtonStyle(
                            shape=radius,
                            side=ft.BorderSide(1, EDGE),
                            text_style=ft.TextStyle(size=17, font_family="Tajawal Bold"),
                        ),
                    )
                    for word in S["words"]
                ]
                + [
                    ft.Container(height=6),
                    quiet("لم يعرف", lambda e: confirm(None)),
                ],
            )

            show(
                ft.Text("انتهى التصويت", size=14, color=MUTED),
                ft.Container(height=10),
                # the same red as the spy's card, so "you are out" looks the
                # same wherever it appears
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=28, vertical=12),
                    bgcolor=SPY,
                    border_radius=18,
                    content=ft.Column(
                        [
                            ft.Text("برا السالفة", size=13, color=ON_SPY),
                            ft.Text(
                                g.spy,
                                size=32,
                                font_family="Tajawal Bold",
                                color=ON_SPY,
                            ),
                        ],
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(height=16),
                ft.Text("سلّم الجوال إلى الجاسوس واختر الكلمة", color=SAFFRON, size=14),
                ft.Container(height=8),
                picks,
                center=True,
            )
        else:
            summary = S["summary"]
            board = sorted(g.scores.items(), key=lambda item: item[1], reverse=True)

            show(
                ft.Row(
                    [
                        ft.Text("الكلمة كانت:", size=15, color=MUTED),
                        ft.Text(
                            summary["word"],
                            size=28,
                            font_family="Tajawal Bold",
                            color=MINT,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
                ft.Text(
                    "عرفها الجاسوس! +2" if summary["spy_guessed"] else "الجاسوس لم يعرفها",
                    color=MINT if summary["spy_guessed"] else MUTED,
                    size=14,
                ),
                ft.Container(height=14),
                ft.Container(width=300, height=1, bgcolor=EDGE),
                ft.Container(height=14),
                ft.Text("النقاط", size=16, color=MUTED),
                *[
                    ft.Text(f"{name} — {points}", size=19, color=TEXT)
                    for name, points in board
                ],
                ft.Container(height=24),
                action("العب مرة أخرى", play_again),
                quiet("الرئيسية", lambda e: home()),
                center=True,
            )

    # ------------------------------------------------------------ settings

    def settings():
        status = ft.Text("", color=MUTED, size=13)
        cats = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)
        address = ft.TextField(
            hint_text="192.168.1.5:8000",
            value=words.saved_address(),
            expand=True,
            text_size=16,
            filled=True,
            fill_color=PANEL,
            border_color=EDGE,
            border_width=1,
            focused_border_color=MINT,
            border_radius=14,
            color=TEXT,
            hint_style=ft.TextStyle(color=MUTED, size=14),
            cursor_color=MINT,
        )

        def draw():
            cats.controls.clear()
            saved = words.load()
            if not saved:
                cats.controls.append(ft.Text("لا توجد كلمات محفوظة", color=MUTED, size=14))
                return
            for cat in saved:
                n = len(cat.words)
                # Arabic counts change the word: 3-10 takes the plural
                if n == 1:
                    count = "كلمة واحدة"
                elif n == 2:
                    count = "كلمتان"
                elif 3 <= n <= 10:
                    count = f"{n} كلمات"
                else:
                    count = f"{n} كلمة"
                cats.controls.append(
                    ft.Text(
                        f"{cat.name} — {count}",
                        size=15,
                        color=TEXT,
                    )
                )

        def sync(e):
            status.value = "جاري المزامنة..."
            status.color = MUTED
            page.update()

            # the same call home makes; only the screen around it differs
            _, message, ok = words.sync(address.value)
            status.value = message
            status.color = MINT if ok else CORAL
            draw()
            page.update()

        draw()
        show(
            title("الإعدادات"),
            ft.Container(height=6),
            ft.Text(
                "اكتب عنوان الحاسب الذي يطبعه برنامج server.py",
                size=13,
                color=MUTED,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=18),
            caption("عنوان الحاسب", width=340),
            ft.Row(
                [
                    address,
                    ft.FilledButton(
                        "مزامنة",
                        icon=ft.Icons.SYNC,
                        on_click=sync,
                        height=56,
                        bgcolor=PANEL,
                        color=MINT,
                        elevation=0,
                        style=ft.ButtonStyle(
                            shape=radius,
                            side=ft.BorderSide(1, EDGE),
                            text_style=ft.TextStyle(size=14, font_family="Tajawal"),
                        ),
                    ),
                ],
                width=340,
                spacing=10,
            ),
            ft.Container(height=16, alignment=ft.Alignment.CENTER, content=status),
            ft.Container(width=340, height=1, bgcolor=EDGE),
            ft.Container(height=10),
            cats,
            quiet("رجوع", lambda e: home()),
        )

    home()


if __name__ == "__main__":
    ft.run(main)
