"""برا السالفة — the app.

Stage 5: the screens, the Arabic font, the reveal animation, vibration.
Run with:  python app.py
"""

import json
import pathlib

import flet as ft
import httpx

from game import Game, choose_category

HERE = pathlib.Path(__file__).parent
WORDS_FILE = HERE / "local_words.json"  # the copy the phone keeps
ADDRESS_FILE = HERE / "pc_address.txt"  # last PC address the user typed


# ---------------------------------------------------------------- files


def load_words():
    if WORDS_FILE.exists():
        return json.loads(WORDS_FILE.read_text(encoding="utf-8"))
    return None


def save_words(data):
    WORDS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_address():
    if ADDRESS_FILE.exists():
        return ADDRESS_FILE.read_text(encoding="utf-8").strip()
    return ""


def save_address(address):
    ADDRESS_FILE.write_text(address, encoding="utf-8")


# ---------------------------------------------------------------- sync


def sync_words(address):
    """Ask the PC for the newest list. Returns (ok, message)."""
    base = "http://" + address.strip().rstrip("/").removeprefix("http://")
    try:
        remote = httpx.get(f"{base}/version", timeout=5).json()["version"]
        local = load_words()

        if local and local.get("version") == remote:
            message = f"الكلمات محدثة (نسخة {remote})"
        else:
            save_words(httpx.get(f"{base}/data", timeout=10).json())
            message = f"تم تنزيل نسخة {remote}"

        save_address(base)
        return True, message
    except Exception:
        return False, "تعذر الاتصال بالحاسب"


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

    theme = ft.Theme(font_family="Tajawal", color_scheme_seed=ft.Colors.PURPLE)

    # Both themes, because the app is dark: with theme_mode DARK, Flet uses
    # dark_theme, and a font set only on theme would be ignored.
    page.theme = theme
    page.dark_theme = theme

    haptics = ft.HapticFeedback()

    def buzz():
        """One short vibration. Phones only: a desktop has nothing to shake."""
        if page.platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS):
            page.run_task(haptics.vibrate)

    # everything the screens share
    S = {
        "game": None,  # the Game object, once a game starts
        "names": "",  # last names typed, to prefill next time
        "i": 0,  # reveal / vote progress
        "shown": False,  # reveal: is the card open?
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
        data = load_words()
        count = len(data["categories"]) if data else 0

        # one line that holds either the count or the sync result,
        # so the buttons above it never move
        status = ft.Text(
            f"عدد الفئات: {count}" if count else "لا توجد كلمات بعد",
            color=ft.Colors.GREY,
        )

        def refresh(e):
            address = load_address()
            if not address:
                status.value = "أدخل عنوان الحاسب من الإعدادات"
                status.color = ft.Colors.AMBER
                page.update()
                return

            status.value = "جاري التحديث..."
            status.color = ft.Colors.GREY
            page.update()

            ok, message = sync_words(address)
            status.value = message
            status.color = ft.Colors.GREEN if ok else ft.Colors.RED
            page.update()

        show(
            ft.Text("برا السالفة", size=44, font_family="Tajawal Bold"),
            ft.Text("لعبة الجاسوس", size=16, color=ft.Colors.GREY),
            ft.Container(height=30),
            ft.FilledButton(
                "لعبة جديدة",
                icon=ft.Icons.PLAY_ARROW,
                height=60,
                width=280,
                on_click=lambda e: setup(),
            ),
            ft.OutlinedButton(
                "تحديث الكلمات",
                icon=ft.Icons.SYNC,
                width=280,
                on_click=refresh,
            ),
            ft.Container(height=16),
            ft.Container(height=24, alignment=ft.Alignment.CENTER, content=status),
            ft.TextButton("الإعدادات", on_click=lambda e: settings()),
            center=True,
        )

    # ------------------------------------------------------------ setup

    def setup():
        data = load_words()
        if not data:
            show(
                ft.Text("لا توجد كلمات محفوظة."),
                ft.Text("شغّل برنامج الحاسب ثم اضغط تحديث الكلمات.", color=ft.Colors.GREY),
                ft.FilledButton("تحديث الكلمات", on_click=lambda e: settings()),
                center=True,
            )
            return

        names = ft.TextField(
            label="أسماء اللاعبين (اسم في كل سطر)",
            multiline=True,
            min_lines=4,
            value=S["names"],
            text_size=18,
        )
        category = ft.Dropdown(
            label="الفئة",
            value="عشوائي",
            options=[ft.DropdownOption(key="عشوائي", text="عشوائي")]
            + [ft.DropdownOption(key=c["name"], text=c["name"]) for c in data["categories"]],
        )
        error = ft.Text("", color=ft.Colors.RED)

        def start(e):
            players = [line.strip() for line in names.value.splitlines() if line.strip()]

            if len(players) < 3:
                error.value = "تحتاج 3 لاعبين على الأقل"
                page.update()
                return
            if len(set(players)) != len(players):
                error.value = "لا تكرر نفس الاسم مرتين"
                page.update()
                return

            words = choose_category(
                data, None if category.value == "عشوائي" else category.value
            )["words"]

            S["game"] = Game(players, words)
            S["names"] = names.value
            S["i"] = 0
            S["shown"] = False
            S["votes"] = {}
            S["summary"] = None
            S["words"] = words
            reveal()

        show(
            ft.Text("لاعبون", size=30, font_family="Tajawal Bold"),
            names,
            category,
            ft.Container(height=28, alignment=ft.Alignment.CENTER, content=error),
            ft.FilledButton("ابدأ", height=55, width=240, on_click=start),
            ft.TextButton("رجوع", on_click=lambda e: home()),
        )

    # ------------------------------------------------------------ reveal

    def reveal():
        g = S["game"]
        if S["i"] >= len(g.players):
            round_screen()
            return

        name = g.players[S["i"]]
        is_spy = name == g.spy

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
                        ft.Text("أعطِ الجوال إلى", color=ft.Colors.GREY),
                        ft.Text(name, size=34, font_family="Tajawal Bold"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
            )

        def face_up():
            return ft.Container(
                width=320,
                height=220,
                alignment=ft.Alignment.CENTER,
                content=ft.Container(
                    content=ft.Text(
                        "أنت برا السالفة" if is_spy else g.word,
                        size=40,
                        font_family="Tajawal Bold",
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.RED if is_spy else ft.Colors.WHITE,
                    ),
                    padding=40,
                    border=ft.Border.all(2, ft.Colors.PURPLE),
                    border_radius=20,
                ),
            )

        card = ft.AnimatedSwitcher(
            content=face_up() if S["shown"] else face_down(),
            width=320,
            height=220,
            duration=220,
            transition=ft.AnimatedSwitcherTransition.SCALE,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
        )
        button = ft.FilledButton(
            "إخفاء وتمرير" if S["shown"] else "اضغط لعرض الكلمة",
            height=80,
            width=320,
            on_click=lambda e: tap(),
        )

        def tap():
            """First tap shows the word, the second hides it and passes on."""
            if S["shown"]:
                S["i"] += 1
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
            button,
            ft.Container(height=12),
            ft.Container(
                height=24,
                alignment=ft.Alignment.CENTER,
                content=ft.Text(
                    f"{S['i'] + 1} من {len(g.players)}", color=ft.Colors.GREY
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
            ft.Text(asker, size=44, font_family="Tajawal Bold"),
            ft.Text(f"يسأل: {answerer}", size=20, color=ft.Colors.GREY),
            ft.Container(height=8),
            ft.Text("الإجابة بنعم أو لا فقط", color=ft.Colors.GREY),
            ft.Container(height=30),
            ft.FilledButton(
                "الجولة التالية",
                height=55,
                width=300,
                on_click=lambda e: next_round(),
            ),
            ft.OutlinedButton(
                "نريد التصويت",
                icon=ft.Icons.HOW_TO_VOTE,
                height=55,
                width=300,
                on_click=lambda e: ask_vote(),
            ),
            ft.Container(height=8),
            ft.Container(
                height=22,
                alignment=ft.Alignment.CENTER,
                content=ft.Text(
                    f"طلبات التصويت: {g.vote_requests} من {g.votes_needed()}",
                    color=ft.Colors.GREY,
                ),
            ),
            ft.Container(
                height=22,
                alignment=ft.Alignment.CENTER,
                content=ft.Text(
                    "" if g.everyone_played() else "ينتظر: لم يلعب الجميع بعد",
                    size=13,
                    color=ft.Colors.AMBER,
                ),
            ),
            ft.TextButton("إلغاء اللعبة", on_click=lambda e: home()),
            center=True,
        )

    def next_round():
        S["game"].next_pair()
        # round 10 ends the questions whether anybody asked or not
        if S["game"].should_vote():
            start_vote()
        else:
            round_screen()

    def ask_vote():
        S["game"].request_vote()
        if S["game"].should_vote():
            start_vote()
        else:
            round_screen()

    # ------------------------------------------------------------ vote

    def start_vote():
        S["game"].start_vote()
        S["i"] = 0
        S["votes"] = {}
        vote_screen()

    def vote_screen():
        g = S["game"]
        if S["i"] >= len(g.players):
            result_screen()
            return

        voter = g.players[S["i"]]

        def pick(accused):
            S["votes"][voter] = accused
            S["i"] += 1
            vote_screen()

        show(
            ft.Text("التصويت", size=30, font_family="Tajawal Bold"),
            ft.Text("أعطِ الجوال إلى", color=ft.Colors.GREY),
            ft.Text(voter, size=30, font_family="Tajawal Bold"),
            ft.Text("من تظنه برا السالفة؟", color=ft.Colors.GREY),
            ft.Container(height=10),
            *[
                ft.FilledButton(
                    name,
                    width=260,
                    height=50,
                    on_click=lambda e, n=name: pick(n),
                )
                for name in g.players
                if name != voter
            ],
            ft.Container(height=10),
            ft.Text(f"{S['i'] + 1} من {len(g.players)}", color=ft.Colors.GREY),
            center=True,
        )

    # ------------------------------------------------------------ result

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
                        height=48,
                        on_click=lambda e, w=word: confirm(w),
                    )
                    for word in S["words"]
                ]
                + [
                    ft.Container(height=6),
                    ft.TextButton("لم يعرف", on_click=lambda e: confirm(None)),
                ],
            )

            show(
                ft.Text("انتهى التصويت", size=26, font_family="Tajawal Bold"),
                ft.Text(f"برا السالفة: {g.spy}", size=30, color=ft.Colors.PURPLE_200),
                ft.Container(height=10),
                ft.Text("سلّم الجوال إلى الجاسوس واختر الكلمة", color=ft.Colors.AMBER),
                picks,
                center=True,
            )
        else:
            summary = S["summary"]
            board = sorted(g.scores.items(), key=lambda item: item[1], reverse=True)

            show(
                ft.Text(f"الكلمة كانت: {summary['word']}", size=24),
                ft.Text(
                    "عرفها الجاسوس! +2" if summary["spy_guessed"] else "الجاسوس لم يعرفها",
                    color=ft.Colors.AMBER if summary["spy_guessed"] else ft.Colors.GREY,
                ),
                ft.Divider(),
                ft.Text("النقاط", size=22, font_family="Tajawal Bold"),
                *[ft.Text(f"{name} — {points}", size=20) for name, points in board],
                ft.Container(height=20),
                ft.FilledButton(
                    "العب مرة أخرى",
                    height=55,
                    width=280,
                    on_click=lambda e: setup(),
                ),
                ft.TextButton("الرئيسية", on_click=lambda e: home()),
                center=True,
            )

    # ------------------------------------------------------------ settings

    def settings():
        status = ft.Text("", color=ft.Colors.GREY)
        cats = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        address = ft.TextField(
            label="عنوان الحاسب",
            hint_text="192.168.1.5:8000",
            value=load_address(),
            text_size=18,
            expand=True,
        )

        def draw():
            cats.controls.clear()
            data = load_words()
            if not data:
                cats.controls.append(ft.Text("لا توجد كلمات محفوظة"))
                return
            for cat in data["categories"]:
                cats.controls.append(
                    ft.Text(f"{cat['name']} — {len(cat['words'])} كلمة", size=18)
                )

        def sync(e):
            status.value = "جاري المزامنة..."
            status.color = ft.Colors.GREY
            page.update()

            ok, message = sync_words(address.value)
            status.value = message
            status.color = ft.Colors.GREEN if ok else ft.Colors.RED
            draw()
            page.update()

        draw()
        show(
            ft.Text("الإعدادات", size=30, font_family="Tajawal Bold"),
            ft.Text(
                "اكتب عنوان الحاسب الذي يطبعه برنامج server.py",
                size=14,
                color=ft.Colors.GREY,
            ),
            ft.Row([address, ft.FilledButton("مزامنة", icon=ft.Icons.SYNC, on_click=sync)]),
            ft.Container(height=24, alignment=ft.Alignment.CENTER, content=status),
            ft.Divider(),
            cats,
            ft.TextButton("رجوع", on_click=lambda e: home()),
        )

    home()


if __name__ == "__main__":
    ft.run(main)
