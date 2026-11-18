# -*- coding: utf-8 -*-
"""«Районы и магазины» — игровой движок (без привязки к Telegram).

Game.view()      -> (текст в HTML-разметке Telegram, [подписи кнопок])
Game.choose(i)   -> нажать кнопку i
Game.to_dict() / Game(state) — сохранение и загрузка
"""
import random
import zlib


# ---------------------------------------------------------------- утилиты
def rint(a, b):
    return random.randint(a, b)


def clamp(v, a, b):
    return max(a, min(b, v))


def chance(p):
    return random.random() < clamp(p, 0.03, 0.97)


def pick(a):
    return random.choice(a)


def bar(v, n=10):
    v = clamp(int(v), 0, n)
    return "▰" * v + "▱" * (n - v)


# ---------------------------------------------------------------- данные
DRINKS = {
    "beer":    dict(n="пиво", d=(1, 2), th=3, strong=False),
    "shot":    dict(n="стопку водки", d=(2, 3), th=4, strong=True),
    "vodka":   dict(n="водку из горла", d=(3, 4), th=6, strong=True),
    "samogon": dict(n="самогон", d=(3, 4), th=5, strong=True, poison=0.15),
    "glass":   dict(n="стакан первача", d=(2, 3), th=4, strong=True, poison=0.1),
    "port":    dict(n="портвейн «777»", d=(2, 3), th=4, strong=True),
    "sour":    dict(n="кислое вино", d=(1, 2), th=2, strong=False, poison=0.4),
    "champ":   dict(n="шампанское", d=(1, 2), th=3, strong=False),
    "cognac":  dict(n="коньяк «Хеннесси»", d=(3, 4), th=7, strong=True),
    "kvass":   dict(n="квас", d=(0, 0), th=1, nonalc=True),
    "sip":     dict(n="глоток из общей бутылки", d=(1, 1), th=2, strong=False),
}

ITEMS = {
    "beer": "🍺 Пиво", "vodka": "🍾 Водка", "samogon": "🫙 Самогон",
    "port": "🍷 Портвейн «777»", "sour": "🍷 Кислое вино", "champ": "🥂 Шампанское",
    "cognac": "🥃 Коньяк «Хеннесси»", "galeta": "🦴 Галета для йорка",
    "bun": "🥐 Булка", "bag": "🛍 Пакет пустых бутылок",
    "phone": "📱 Старый телефон", "lighter": "🔥 Зажигалка",
}
BOTTLES = ("beer", "vodka", "samogon", "port", "sour", "champ", "cognac")
MAX_INV = 5

OUTFITS = {
    "casual": "повседневное",
    "dress": "вечернее платье с блёстками",
    "scarf": "бабушкин платок (образ скромницы)",
}

LOCS = {
    "home": "🏠 Квартира",
    "yard": "🌳 Двор",
    "bar": "🍻 Наливайка «Угол»",
    "kb": "🍷 «Красное&amp;Белое»",
    "pyat": "🛒 «Пятёрочка»",
    "gar": "🔧 Гаражи за школой",
    "park": "⛲ Парк с фонтаном",
    "vytrez": "🚑 Вытрезвитель",
    "police": "🚔 Участок №5",
}
TRAVEL = ("home", "yard", "bar", "kb", "pyat", "gar", "park", "vytrez")

SLOTN = {"morning": "утро", "day": "день", "evening": "вечер", "night": "ночь"}
DAYN = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

ENEMIES = {
    "guard":  dict(n="Охранник Сергей", hp=5, str=3, hits=["бьёт под дых", "заламывает руку"]),
    "guard5": dict(n="Охранник «Пятёрочки»", hp=4, str=2, hits=["толкает в стеллаж с макаронами", "хватает за шиворот"]),
    "ksy":    dict(n="Ксюха", hp=3, str=2, item=True, hits=["вцепляется в волосы", "царапает щёку"]),
    "elka":   dict(n="Элка", hp=2, str=1, hits=["неуклюже толкает тебя", "машет руками, зажмурившись"]),
    "dron":   dict(n="Дрон", hp=8, str=5, hits=["отвешивает тяжёлую оплеуху", "толкает так, что ты летишь в кусты"]),
    "chicha": dict(n="Чича", hp=4, str=3, dirty=True, hits=["пинает по голени", "бьёт локтем"]),
    "lifon":  dict(n="Лифон", hp=4, str=2, flee=True, hits=["машет кулаками не глядя"]),
    "gop":    dict(n="Гопники", hp=4, str=4, hits=["бьют вдвоём", "сбивают с ног"]),
    "gang":   dict(n="Толпа гопников", hp=8, str=4, hits=["наваливаются гурьбой", "бьют со всех сторон"]),
    "cop":    dict(n="Полицейский", hp=6, str=4, hits=["бьёт дубинкой", "валит на асфальт"]),
    "alkash": dict(n="Толян", hp=3, str=2, hits=["бьёт пустой бутылкой", "толкает в лужу"]),
    "zina":   dict(n="Буфетчица Зинаида", hp=3, str=2, item=True, hits=["лупит половником", "швыряет стакан"]),
    "makar":  dict(n="Внуки деда Макара", hp=5, str=3, hits=["бьют черенком лопаты", "пинают"]),
}


def new_state():
    return dict(
        t=7 * 60, loc="home", thirst=5, drunk=0, hp=10, money=rint(0, 50),
        rep=0, romance=0, arrests=[], fr=dict(chicha=0, dron=0, lifon=0),
        mom=1, inv=[], outfit="casual",
        acc=dict(th=0, dr=0, zero=0), f={}, over=None, meet=None,
        fight=None, seed=rint(1, 10 ** 9), turn=0,
    )


# ================================================================= Game
class Game:
    def __init__(self, state=None):
        self.s = state if state else new_state()
        self.s.setdefault("turn", 0)
        self.buf = []
        self.sc = None          # текущая сцена: dict(title, text, ch=[(label, fn)])
        self.fo = {}            # колбэки текущей драки
        if self.s.get("fight"):  # после перезапуска драку не восстанавливаем
            self.s["fight"] = None
        if state is None:
            self.intro()

    # ------------------------------------------------ сохранение
    def to_dict(self):
        return self.s

    # ------------------------------------------------ время
    @property
    def f(self):
        return self.s["f"]

    def day(self):
        return self.s["t"] // 1440 + 1

    def hour(self):
        return (self.s["t"] % 1440) // 60

    def clock(self):
        m = self.s["t"] % 1440
        return "%02d:%02d" % (m // 60, m % 60)

    def slot(self):
        h = self.hour()
        if 7 <= h < 11:
            return "morning"
        if 11 <= h < 17:
            return "day"
        if 17 <= h < 22:
            return "evening"
        return "night"

    def weekend(self):
        return (self.day() - 1) % 7 in (5, 6)

    def hr(self, key):
        """Детерминированный «случай» на текущий час: NPC не мигают туда-сюда."""
        raw = "%s|%s|%s|%s|%s" % (self.s["seed"], self.day(), self.hour(), self.s["loc"], key)
        return zlib.crc32(raw.encode()) / 4294967296

    def P(self, key, p):
        return self.hr(key) < p

    def sober_path(self):
        return self.f.get("meeting_at") is not None and not self.f.get("ivan_turned")

    def tremor(self):
        return self.s["acc"]["zero"] >= 360

    def advance(self, minutes, sleep=False):
        s = self.s
        while minutes > 0:
            st = min(10, minutes)
            minutes -= st
            s["t"] += st
            rate = 150
            if self.sober_path():
                rate = 300
            if sleep:
                rate *= 2
            s["acc"]["th"] += st
            if s["acc"]["th"] >= rate:
                s["acc"]["th"] -= rate
                s["thirst"] = min(10, s["thirst"] + 1)
            if s["drunk"] > 0:
                s["acc"]["dr"] += st * (1.5 if sleep else 1)
                if s["acc"]["dr"] >= 150:
                    s["acc"]["dr"] -= 150
                    s["drunk"] -= 1
            else:
                s["acc"]["dr"] = 0
            if s["thirst"] == 0:
                s["acc"]["zero"] += st
            else:
                s["acc"]["zero"] = 0

    def minutes_to_morning(self):
        m = self.s["t"] % 1440
        return (7 * 60 - m) if m < 7 * 60 else (1440 - m + 7 * 60)

    # ------------------------------------------------ вывод
    def say(self, text):
        self.buf.append(text)

    def scene(self, title, text, choices):
        pre = "\n\n".join(self.buf)
        self.buf = []
        body = (pre + "\n\n" + text) if pre and text else (pre or text)
        self.sc = dict(title=title, text=body, ch=choices)

    def rep_title(self):
        if self.sober_path():
            return "Святая"
        r = self.s["rep"]
        if r >= 5:
            return "Легенда"
        if r <= -3:
            return "Падшая"
        return "Своя"

    def hud(self):
        s = self.s
        lines = [
            "📅 День %d (%s) · %s, %s" % (self.day(), DAYN[(self.day() - 1) % 7], self.clock(), SLOTN[self.slot()]),
            "🍺 Жажда      %s %d" % (bar(s["thirst"]), s["thirst"]),
            "🥴 Опьянение %s %d" % (bar(s["drunk"]), s["drunk"]),
            "❤️ Здоровье  %s %d" % (bar(s["hp"]), s["hp"]),
            "💰 %d ₽ · 💘 %d/10 · 😎 %s · 🚓 %d" % (s["money"], s["romance"], self.rep_title(), len(s["arrests"])),
        ]
        warn = []
        if s["thirst"] >= 8:
            warn.append("⚠️ Жажда почти невыносима")
        if s["drunk"] >= 8:
            warn.append("⚠️ Ты еле стоишь на ногах")
        if s["hp"] <= 3:
            warn.append("⚠️ Всё болит")
        if self.tremor():
            warn.append("🫨 Руки трясутся")
        if warn:
            lines.append(" · ".join(warn))
        return "\n".join(lines)

    def view(self):
        if self.sc is None:
            self.refresh()
        sc = self.sc
        text = ""
        if not self.s["over"]:
            text = self.hud() + "\n━━━━━━━━━━━━━━\n"
        text += "<b>%s</b>\n%s" % (sc["title"], sc["text"])
        if len(text) > 4000:
            text = text[:3990] + "…"
        return text, [c[0] for c in sc["ch"]]

    def choose(self, i):
        if self.sc is None:
            self.refresh()
        if not (0 <= i < len(self.sc["ch"])):
            return
        fn = self.sc["ch"][i][1]
        fn()
        self.post()
        self.s["turn"] += 1

    def refresh(self):
        if self.s["over"]:
            self.ending(self.s["over"], silent=True)
        else:
            self.go(self.s["loc"])

    def post(self):
        s = self.s
        if s["over"] or s["fight"]:
            return
        s["hp"] = clamp(s["hp"], 0, 10)
        s["thirst"] = clamp(s["thirst"], 0, 10)
        s["drunk"] = clamp(s["drunk"], 0, 10)
        s["romance"] = clamp(s["romance"], 0, 10)
        s["mom"] = clamp(s["mom"], -3, 3)
        s["rep"] = clamp(s["rep"], -10, 10)
        for k in s["fr"]:
            s["fr"][k] = clamp(s["fr"][k], -2, 2)
        if s["hp"] <= 0:
            return self.collapse("hp")
        if s["thirst"] >= 10:
            return self.collapse("thirst")
        if s["drunk"] >= 10:
            return self.collapse("drunk")
        self.check_endings()

    # ------------------------------------------------ инвентарь
    def has(self, item):
        return item in self.s["inv"]

    def add(self, item):
        if len(self.s["inv"]) >= MAX_INV:
            self.say("🎒 Сумка забита (5 вещей) — %s пришлось оставить." % ITEMS[item])
            return False
        self.s["inv"].append(item)
        return True

    def remove(self, item):
        if item in self.s["inv"]:
            self.s["inv"].remove(item)

    def bottles(self):
        return [i for i in self.s["inv"] if i in BOTTLES]

    def pay(self, n):
        if self.s["money"] < n:
            self.say("💸 Не хватает денег.")
            return False
        self.s["money"] -= n
        return True

    def drink(self, kind, note=None):
        s = self.s
        d = DRINKS[kind]
        if not d.get("nonalc"):
            s["drunk"] = clamp(s["drunk"] + rint(*d["d"]), 0, 10)
            s["acc"]["th"] = 0
        s["thirst"] = clamp(s["thirst"] - d["th"], 0, 10)
        msg = note or "Ты пьёшь %s." % d["n"]
        if d.get("poison") and chance(d["poison"]):
            dmg = rint(1, 2)
            s["hp"] -= dmg
            msg += " Живот скручивает — кажется, отравилась. −%d ❤️" % dmg
        if self.sober_path() and d.get("strong"):
            self.f["ivan_turned"] = True
            msg += "\n<i>Иван узнает. Он больше не будет тебя ждать.</i>"
        self.say(msg)

    # ------------------------------------------------ проверки
    def pers_mod(self):
        s = self.s
        m = 0.0
        if s["drunk"] >= 3:
            m -= 0.06 * (s["drunk"] - 2)
        if self.tremor():
            m -= 0.15
        m += 0.02 * s["rep"]
        return m

    def outfit_k(self):
        return {"scarf": 0.2, "dress": 0.05}.get(self.s["outfit"], 0)

    def approvals(self):
        return sum(1 for v in self.s["fr"].values() if v >= 0)

    def queen_ok(self):
        s = self.s
        recent = any(s["t"] - a < 1440 for a in s["arrests"])
        return (s["romance"] >= 8 and self.approvals() >= 2 and self.f.get("ksy_out")
                and self.f.get("elka_ok") and not recent)

    def check_endings(self):
        s = self.s
        lost = s["romance"] <= 3 and s["mom"] <= 0
        if len(s["arrests"]) >= 3 and (s["hp"] <= 3 or s["money"] < 100) and lost:
            return self.ending("bottom")
        if self.sober_path() and not self.f.get("escaped") and s["t"] >= self.f["meeting_at"] + 1440:
            return self.ending("light")
        if self.queen_ok():
            return self.ending("queen")

    # ------------------------------------------------ финалы
    def ending(self, kind, silent=False):
        s = self.s
        s["over"] = kind
        s["fight"] = None
        if kind == "queen":
            title = "👑 ФИНАЛ: «Королева района»"
            text = ("Коля приглашает тебя в свою трёхкомнатную квартиру.\n\n"
                    "Ты лежишь на диване, йорк под боком, Коля наливает ликёр. Чича и Дрон уважительно кивают. "
                    "Мама плачет от гордости. Алкоголь теперь всегда дорогой. Соседи завидуют.\n\n"
                    "<b>Ты — королева района.</b>\n\nРепутация: «Легенда».")
        elif kind == "light":
            title = "🕊 ФИНАЛ: «Просветление»"
            text = ("Иван находит тебя и крепко жмёт руку: «Сутки продержалась. Дальше будет легче».\n\n"
                    "Ты становишься волонтёром реабилитационного центра в бывшем ДК. "
                    "Ты сидишь за столом с надписью «Трезвость — 30 дней». Коля заходит с апельсинами, улыбается, "
                    "но ты спокойна. Мама обнимает и наконец-то не плачет от горя.\n\n"
                    "<b>Жажда отступила.</b>\n\nРепутация: «Святая».")
        else:
            title = "⬛ ФИНАЛ: «На дне»"
            text = ("Ты лежишь на жёсткой койке. Санитар — не Иван, другой — равнодушно бросает: "
                    "«Тахта, ты тут навечно».\n\nМимо проходит Коля с новой девушкой и не узнаёт тебя. "
                    "Мама больше не отвечает.\n\n<i>Холод. Хлорка. Тишина.</i>")
        stats = "\n\n<i>Дней прожито: %d · приводов: %d · роман: %d/10</i>" % (self.day(), len(s["arrests"]), s["romance"])
        if silent:
            self.buf = []
        self.scene(title, text + stats, [("🔄 Начать заново", self.restart)])

    def restart(self):
        self.s.clear()
        self.s.update(new_state())
        self.buf = []
        self.intro()

    def intro(self):
        self.say("<i>Спальный район. Серые девятиэтажки, вечный ремонт. Тебя зовут София, для района — просто Тахта. "
                 "Тебе 32, работы нет, живёшь с мамой. Мечта — сосед Коля-Миллионер. Проблема — жажда.</i>")
        self.say("Мама гремит на кухне: «Софа, я на работу. Борщ в холодильнике. Не вздумай опять!»")
        self.go("home")

    def collapse(self, why):
        s = self.s
        support = s["money"] >= 50 or s["romance"] > 5 or s["mom"] >= 2
        reason = {
            "hp": "Мир гаснет. Ты падаешь и больше не встаёшь.",
            "thirst": "Жажда скручивает так, что темнеет в глазах. Ты теряешь сознание.",
            "drunk": "Ты выпила лишнего и отключаешься прямо там, где стояла.",
        }[why]
        self.say("💥 " + reason)
        if not support:
            self.say("Денег нет, Коля не отвечает, мама не приходит. Никто не придёт.")
            return self.ending("bottom")
        s["fight"] = None
        s["meet"] = None
        s["loc"] = "vytrez"
        self.f["must_stay"] = True
        if why == "hp":
            s["hp"] = 3
            self.say("Скорая, капельница, а потом — вытрезвитель при отделении №5. Здоровье немного восстановили.")
        elif why == "thirst":
            s["thirst"] = 6
            self.say("Очнулась на железной койке. Пахнет хлоркой. Тебе поставили капельницу.")
        else:
            self.say("Патруль погрузил тебя в «бобик». Очнулась в вытрезвителе.")
        self.advance(rint(4, 7) * 60)
        if why != "hp":
            s["hp"] = max(s["hp"], 2)
        self.go("vytrez")

    # ------------------------------------------------ навигация
    def go(self, loc=None):
        s = self.s
        loc = loc or s["loc"]
        s["loc"] = loc
        builder = getattr(self, "b_" + loc)
        title, desc, acts = builder()
        if loc not in ("police",):
            if loc != "vytrez":
                acts.append(("🚶 Пойти в другое место…", self.travel_menu))
            acts.append(("🎒 Сумка (%d/5)" % len(s["inv"]), self.inventory))
            acts.append(("📜 Подсказки", self.help))
        self.scene(title, desc, acts)

    def back(self):
        self.go()

    def travel_menu(self):
        ch = []
        for loc in TRAVEL:
            if loc == self.s["loc"]:
                continue
            label = LOCS[loc] if loc != "vytrez" else "🚑 Вытрезвитель (попроситься)"
            ch.append((label, lambda l=loc: self.travel(l)))
        ch.append(("↩️ Остаться", self.back))
        self.scene("Куда пойти?", "Дорога займёт 10–20 минут.", ch)

    def travel(self, loc):
        s = self.s
        self.advance(rint(10, 20))
        s["loc"] = loc
        s["meet"] = None
        h = self.hour()
        night = h >= 22 or h < 6
        if loc == "vytrez":
            self.f["must_stay"] = False
            self.say("Дежурный пожимает плечами: «Сама пришла? Ну ложись, раз такая сознательная»." )
        if loc in ("yard", "park") and night and s["drunk"] >= 6 and chance(0.12):
            return self.arrest("🚓 Тебя заметил ночной патруль. «Гражданочка, пройдёмте».")
        if loc in ("yard", "park", "gar") and night and chance(0.22):
            return self.gop_event()
        if loc == "home" and self.mom_awake():
            if s["drunk"] >= 5:
                b = self.bottles()
                if b:
                    for x in b:
                        self.remove(x)
                    s["mom"] -= 1
                    self.say("👩 Мама видит тебя в таком виде и отбирает все бутылки: «Опять?! Позор!»")
                if s["drunk"] >= 8 and s["mom"] <= 0 and chance(0.5):
                    return self.arrest("👩 Мама в слезах звонит в полицию: «Заберите её, я больше не могу».")
        self.go(loc)

    # ================================================================= ЛОКАЦИИ
    # ---------------------------------------- Квартира
    def mom_state(self):
        """'away' | 'awake' | 'asleep'"""
        if self.f.get("mom_out") == self.day():
            return "away"
        h = self.hour()
        if h >= 23 or h < 7:
            return "awake" if self.P("momnight", 0.15) else "asleep"
        if self.weekend():
            return "awake" if self.P("momwk", 0.65) else "away"
        if h < 8:
            return "awake"
        if 18 <= h < 23:
            return "awake" if self.P("momev", 0.85) else "away"
        return "away"

    def mom_awake(self):
        return self.mom_state() == "awake"

    def b_home(self):
        s, d = self.s, self.day()
        desc = ("Двушка с коврами и мебельной стенкой. В твоей комнате — продавленная тахта, зеркало и шкаф. "
                "На кухне гудит холодильник, с балкона звякают пустые бутылки.")
        ms = self.mom_state()
        desc += {"awake": "\n\n👩 Мама дома.", "asleep": "\n\n👩 Мама спит за стенкой.", "away": "\n\nМамы нет дома."}[ms]
        desc += "\n👗 На тебе: %s." % OUTFITS[s["outfit"]]
        acts = [
            ("🔍 Осмотреться в комнате", self.home_search),
            ("👗 Порыться в шкафу", self.wardrobe),
            ("🍲 Пойти на кухню", self.kitchen),
        ]
        if self.has("phone"):
            acts.append(("📞 Позвонить по телефону", self.phone))
        if self.f.get("balcony") != d:
            acts.append(("🛍 Собрать бутылки на балконе", self.balcony))
        h = self.hour()
        if h >= 22 or h < 7:
            acts.append(("😴 Лечь спать", self.sleep))
        if ms != "away":
            acts.append(("👩 Поговорить с мамой", self.mom_talk))
        return LOCS["home"], desc, acts

    def home_search(self):
        s = self.s
        self.advance(15)
        if not self.f.get("searched"):
            self.f["searched"] = True
            m = rint(10, 30)
            s["money"] += m
            self.add("phone")
            self.add("lighter")
            self.say("🔍 Под тахтой — заначка %d ₽, старый телефон с контактами («Коля», «Мама», «Бывший») "
                     "и зажигалка. Неплохо." % m)
        elif self.f.get("search_day") != self.day() and chance(0.4):
            m = rint(5, 20)
            s["money"] += m
            self.say("🔍 В кармане старой куртки нашлось %d ₽." % m)
        else:
            self.say("🔍 Пыль, фантики и фото с выпускного. Ничего полезного.")
        self.f["search_day"] = self.day()
        self.go()

    def wardrobe(self):
        ch = [("👕 Повседневное", lambda: self.wear("casual")),
              ("✨ Вечернее платье с блёстками", lambda: self.wear("dress")),
              ("🧕 Бабушкин платок", lambda: self.wear("scarf")),
              ("↩️ Назад", self.back)]
        self.scene("Шкаф", "Что надеть? Наряд влияет на то, как на тебя смотрят.\n"
                   "<i>Платок — скромница (Коле нравится), платье — вызывающе, повседневное — нейтрально.</i>", ch)

    def wear(self, o):
        self.s["outfit"] = o
        self.advance(10)
        self.say("👗 Ты переодеваешься: %s." % OUTFITS[o])
        self.go()

    def kitchen(self):
        d = self.day()
        ch = []
        if self.f.get("borsch") != d:
            ch.append(("🍲 Съесть мамин борщ", self.eat_borsch))
        for b in sorted(set(self.bottles())):
            ch.append(("Выпить: %s" % ITEMS[b], lambda b=b: self.drink_item(b, back=self.kitchen)))
        ch.append(("↩️ Назад в комнату", self.back))
        txt = "Кухня. Клеёнка в цветочек, холодильник «Атлант»."
        if self.f.get("borsch") != d:
            txt += " В холодильнике — кастрюля борща."
        self.scene("Кухня", txt, ch)

    def eat_borsch(self):
        s = self.s
        self.f["borsch"] = self.day()
        s["hp"] += 1
        s["drunk"] = max(0, s["drunk"] - 1)
        self.advance(20)
        self.say("🍲 Горячий борщ. Голова чуть проясняется. +1 ❤️")
        self.kitchen()

    def balcony(self):
        self.f["balcony"] = self.day()
        self.advance(15)
        if self.add("bag"):
            self.say("🛍 Ты собираешь пустые бутылки в пакет. В «Пятёрочке» за них дадут немного денег.")
        self.go()

    def sleep(self):
        s = self.s
        self.advance(self.minutes_to_morning(), sleep=True)
        s["hp"] += 2
        self.say("😴 Ты проваливаешься в сон на тахте. Наступает утро %d-го дня. +2 ❤️" % self.day())
        if not self.weekend():
            self.say("Мама на ходу: «Я на работу. Веди себя прилично!»")
        self.go("home")

    def phone(self):
        ch = [("📞 Коле", self.call_kolya)]
        if self.mom_state() == "away":
            ch.append(("📞 Маме", self.call_mom))
        ch += [("📞 Бывшему", self.call_ex), ("↩️ Назад", self.back)]
        self.scene("Телефон", "Старый кнопочный телефон. Батарейка держится на изоленте.", ch)

    def call_kolya(self):
        s = self.s
        self.advance(10)
        if s["romance"] < 2 or not chance(0.75):
            self.say("📞 Длинные гудки. Коля не берёт.")
        elif s["drunk"] >= 6:
            s["romance"] -= 1
            self.say("📞 Коля: «Тахта, ты пьяная. Не звони мне так». Гудки. −1 💘")
        elif self.f.get("kcall") != self.day() and chance(0.55 + self.pers_mod() + 0.03 * s["romance"]):
            self.f["kcall"] = self.day()
            self.f["know_park"] = True
            s["romance"] += 1
            self.say("📞 Коля неожиданно разговорчив: «Вечером гуляю с Тишей в парке, с семи до девяти. Заходи». +1 💘")
        else:
            self.say("📞 Коля: «А, привет. Слушай, неудобно, перезвоню». Не перезвонит.")
        self.go()

    def call_mom(self):
        s = self.s
        self.advance(10)
        if s["mom"] >= 2 and self.f.get("momcall") != self.day():
            self.f["momcall"] = self.day()
            s["money"] += 100
            s["mom"] -= 1
            self.say("📞 Мама вздыхает: «Возьми сотку в шкатулке. Только на еду!» +100 ₽")
        else:
            self.say("📞 Мама: «Я на работе! Не звони по пустякам». Короткие гудки.")
        self.go()

    def call_ex(self):
        s = self.s
        self.advance(15)
        if not self.f.get("ex_paid") and chance(0.3):
            self.f["ex_paid"] = True
            s["money"] += 150
            self.say("📞 Бывший размяк: «Ладно, скину тебе 150, только больше не звони». +150 ₽")
        else:
            self.say("📞 Бывший двадцать минут рассказывает, как ты испортила ему жизнь, и напоминает про долг в 500 ₽.")
        self.go()

    def mom_talk(self):
        if self.mom_state() == "asleep":
            ch = [("🔔 Разбудить", self.mom_wake), ("↩️ Не будить", self.back)]
            return self.scene("Мама", "Мама спит. Будить её — себе дороже.", ch)
        ch = [("💰 Попросить денег", self.mom_money),
              ("🤝 Попросить о помощи, поговорить по душам", self.mom_help)]
        if self.sober_path() and not self.f.get("mom_sorry"):
            ch.append(("🙏 Извиниться за всё", self.mom_sorry))
        ch += [("😤 Поругаться", self.mom_fight), ("↩️ Уйти", self.back)]
        m = self.s["mom"]
        mood = "смотрит устало, но тепло" if m >= 2 else "поджимает губы" if m <= 0 else "вздыхает"
        self.scene("Мама", "Мама %s. «Ну что тебе, Софа?»" % mood, ch)

    def mom_wake(self):
        self.s["mom"] -= 1
        self.advance(10)
        self.say("👩 «Ты на часы смотрела?!» Мама злится. −отношения с мамой")
        self.go()

    def mom_money(self):
        s = self.s
        self.advance(10)
        if self.f.get("mom_money") == self.day():
            s["mom"] -= 1
            self.say("👩 «Я тебе сегодня уже давала!» Мама обижена.")
        elif chance(0.35 + 0.15 * s["mom"] - (0.3 if s["drunk"] >= 3 else 0)):
            m = rint(5, 15) * 10
            self.f["mom_money"] = self.day()
            s["money"] += m
            self.say("👩 Мама достаёт кошелёк: «На проезд. И на хлеб». +%d ₽" % m)
        else:
            self.f["mom_money"] = self.day()
            self.say("👩 «Чтобы ты опять пропила? Нет».")
        self.go()

    def mom_help(self):
        s = self.s
        self.advance(30)
        if s["drunk"] >= 3:
            s["mom"] -= 1
            self.say("👩 «О чём с тобой говорить, когда ты в таком виде». Мама уходит к телевизору.")
        elif self.f.get("mom_heart") != self.day():
            self.f["mom_heart"] = self.day()
            s["mom"] += 1
            s["hp"] += 1
            self.say("👩 Вы долго говорите на кухне. Мама гладит тебя по голове, как в детстве, и наливает чаю. +1 ❤️")
        else:
            self.say("👩 Мама кивает: «Я всегда рядом, ты же знаешь».")
        self.go()

    def mom_sorry(self):
        self.f["mom_sorry"] = True
        self.s["mom"] += 2
        self.advance(30)
        self.say("🙏 Ты просишь прощения — за всё. Мама долго молчит, потом обнимает тебя и плачет. Но по-другому.")
        self.go()

    def mom_fight(self):
        s = self.s
        s["mom"] -= 1
        self.advance(15)
        self.say("😤 Вы орёте друг на друга на всю квартиру. Соседи стучат по батарее.")
        if s["drunk"] >= 6 and chance(0.3):
            return self.arrest("👩 Мама набирает 02: «Приезжайте, она буйная!»")
        self.go()

    # ---------------------------------------- Двор
    def b_yard(self):
        s, sl, h = self.s, self.slot(), self.hour()
        P = self.P
        alk = sl == "morning" or (sl == "day" and P("alk", 0.3)) or (sl == "evening" and P("alk", 0.5))
        bab = sl == "morning" or (sl == "day" and P("bab", 0.6))
        chi = (sl == "day" and P("chi", 0.7)) or (sl == "evening" and P("chi", 0.4))
        lif = (sl == "day" and P("lif", 0.7)) or (sl == "evening" and P("lif", 0.4))
        dro = (sl == "day" and P("dro", 0.5)) or (sl == "evening" and P("dro", 0.4))
        kol = (sl == "day" and P("kol", 0.25)) or (sl == "evening" and h < 19 and P("kol", 0.6))
        ksy = sl == "evening" and P("ksy", 0.4) and not self.f.get("ksy_out")
        elk = sl == "evening" and P("elk", 0.4)
        gop = sl == "night" and P("gop", 0.4)
        desc = {
            "morning": "Утренний двор: покосившиеся качели, лавочка у подъезда №5, лужи.",
            "day": "Двор гудит: кто-то выбивает ковёр, из-за гаражей доносится мат.",
            "evening": "Вечер. Зажигаются окна девятиэтажек, у подъезда пахнет жареной картошкой.",
            "night": "Ночь. Фонарь мигает, у качелей кто-то гогочет.",
        }[sl]
        who = []
        acts = []
        if alk:
            who.append("алкаши Толян и Косой на лавочке")
            acts.append(("🍻 Подойти к алкашам", self.alkashi))
        if bab:
            who.append("бабки у подъезда")
            acts.append(("👵 Заговорить с бабками", self.babki))
        if chi:
            who.append("Чича")
            acts.append(("😏 Подсесть к Чиче", self.chicha))
        if dro:
            who.append("Дрон")
            acts.append(("💪 Подойти к Дрону", self.dron))
        if lif:
            who.append("Лифон")
            acts.append(("🕶 Подойти к Лифону", self.lifon))
        if kol:
            who.append("<b>Коля</b> " + ("у почтовых ящиков" if sl == "day" else "с йорком Тишей"))
            acts.append(("✨ Подойти к Коле", lambda: self.kolya("yard")))
        if ksy:
            who.append("Ксюха караулит у подъезда")
            acts.append(("💅 Подойти к Ксюхе", lambda: self.ksy_scene(False)))
        if elk:
            who.append("Элка выносит мусор")
            acts.append(("🙂 Заговорить с Элкой", self.elka))
        if gop:
            who.append("гопники у качелей")
            acts.append(("😬 Подойти к гопникам", self.gop_event))
        acts.append(("🎠 Пойти к качелям", self.swings))
        acts.append(("⏳ Подождать полчаса", self.wait_yard))
        if self.f.get("code"):
            acts.append(("🔔 Позвонить в домофон Коле", self.intercom))
        if who:
            desc += "\n\nЗдесь: " + ", ".join(who) + "."
        else:
            desc += "\n\nНикого интересного."
        return LOCS["yard"], desc, acts

    def wait_yard(self):
        self.advance(30)
        self.say("⏳ Ты сидишь на лавочке и смотришь, кто пройдёт.")
        self.go()

    def swings(self):
        s = self.s
        self.advance(10)
        if s["drunk"] > 5 and chance(0.4):
            s["hp"] -= 1
            self.say("🎠 Качели делают «солнышко» вместе с тобой. Ты падаешь в песок. −1 ❤️")
        elif self.f.get("swing_beer") != self.day() and chance(0.2):
            self.f["swing_beer"] = self.day()
            if self.add("beer"):
                self.say("🎠 Под качелями — забытая бутылка пива. Целая! 🍺")
        else:
            self.say("🎠 Качели жалобно скрипят. Ты немного качаешься. Детство.")
        self.go()

    def alkashi(self):
        s = self.s
        txt = "Толян и Косой трясут пустой бутылкой. «О, Тахта! Садись»."
        ch = [("🗞 Узнать новости", self.alk_news),
              ("🙏 Попросить глоток", self.alk_sip)]
        if s["money"] >= 20:
            ch.append(("🪙 Скинуться (20 ₽)", self.alk_chip))
        if self.bottles():
            ch.append(("🍾 Угостить своей бутылкой", self.alk_share))
        if s["money"] >= 100 or self.bottles():
            txt += "\nКосой косится на твою сумку: «Слышь, а у тебя есть, да? Поделись с братвой»."
        ch += [("🤬 Нагрубить", self.alk_rude), ("↩️ Отойти", self.back)]
        self.scene("Алкаши на лавочке", txt, ch)

    def alk_news(self):
        self.advance(15)
        self.say("🗞 " + pick([
            "Толян: «Коля-то, говорят, квартиру трёшку купил. Миллионер, ёпт».",
            "Косой: «Ксюха вчера в КБ шампанское брала. Для Коли старается».",
            "Толян: «У деда Макара в гаражах первач по десятке. Чистый, как слеза»." ,
            "Косой: «Лифон опять какую-то сумку таскает. Не лезь к нему».",
            "Толян: «Иван в вытрезвителе по ночам собрания проводит. Секта, не иначе».",
        ]))
        self.go()

    def alk_sip(self):
        self.advance(10)
        if chance(0.5 + 0.05 * self.s["rep"]):
            self.drink("sip", "🍻 Толян протягивает бутылку: «Только глоток!» Тёплое пиво — как бальзам.")
        else:
            self.say("🍻 «Самим мало». Косой прячет бутылку за пазуху.")
        self.go()

    def alk_chip(self):
        self.s["money"] -= 20
        self.s["rep"] += 1
        self.advance(30)
        self.drink("beer", "🪙 Вы скидываетесь, Косой бегает за пивом. Ты своя. +репутация")
        self.go()

    def alk_share(self):
        b = self.bottles()[0]
        self.remove(b)
        self.s["rep"] += 1
        self.advance(20)
        self.drink("sip", "🍾 Ты пускаешь %s по кругу. Толян чуть не плачет: «Человек!» +репутация" % ITEMS[b])
        self.go()

    def alk_rude(self):
        self.say("🤬 «Пошли вы, синяки». Толян поднимается: «Чё сказала?!»")
        self.fight("alkash", public=True,
                   win=lambda: self._after(lambda: self.s.__setitem__("rep", self.s["rep"] + 1),
                                           "Толян сидит в луже и обиженно сопит. +репутация"))

    def babki(self):
        s = self.s
        txt = "Бабки у подъезда смолкают и смотрят на тебя оценивающе."
        if s["outfit"] == "scarf":
            txt += " «Ишь, в платочке. Прям как приличная»."
        elif s["outfit"] == "dress":
            txt += " «Вырядилась! Блестит, как ёлка»."
        ch = [("💬 Расспросить про Колю", lambda: self.bab_gossip("kolya")),
              ("💬 Посплетничать про Ксюху и Элку", lambda: self.bab_gossip("girls")),
              ("🙏 Выпросить мелочь", self.bab_coins),
              ("↩️ Отойти", self.back)]
        self.scene("Бабки у подъезда", txt, ch)

    def bab_police_risk(self):
        if self.s["drunk"] >= 6 and chance(0.35):
            self.arrest("👵 «Пьянь! Я милицию вызвала!» — бабка Зинаида машет телефоном. Через десять минут приезжает наряд.")
            return True
        return False

    def bab_gossip(self, topic):
        self.advance(20)
        if self.bab_police_risk():
            return
        if topic == "kolya":
            self.f["know_park"] = True
            line = "«Коля-то каждый вечер с семи до девяти с собачкой в парке гуляет. Собачку Тишей зовут, галеты любит»."
            if not self.f.get("code") and chance(0.3):
                self.f["code"] = True
                line += " А ещё бабка проговаривается, какой у Коли код домофона: «147, я ж слышу, как он жмёт»."
            self.say("👵 " + line)
        else:
            self.say("👵 " + pick([
                "«Ксюха на всё готова, лишь бы его окрутить. Билеты в театр купила!»",
                "«Элка добрая девка, да мать её затюкала. По вечерам в «Угле» прячется»." ,
                "«Ксюха боится, что все узнают, что её бывший её бросил прямо в ЗАГСе». (Пригодится в споре.)",
            ]))
            if chance(0.35):
                self.f["ksy_dirt"] = True
        self.go()

    def bab_coins(self):
        s = self.s
        self.advance(15)
        if self.bab_police_risk():
            return
        if self.f.get("bab_coins") == self.day():
            self.say("👵 «Совести нет! Вчера, сегодня…»")
        elif chance(0.4 + (0.3 if s["outfit"] == "scarf" else 0) - 0.05 * s["drunk"]):
            m = rint(10, 30)
            s["money"] += m
            self.f["bab_coins"] = self.day()
            self.say("👵 Бабка вздыхает и отсчитывает %d ₽ мелочью: «На хлебушек. На хлебушек, поняла?»" % m)
        else:
            self.f["bab_coins"] = self.day()
            self.say("👵 «Работать иди!»")
        self.go()

    def intercom(self):
        s = self.s
        self.advance(10)
        sl = self.slot()
        if sl == "evening" and 19 <= self.hour() < 21:
            self.say("🔔 Тишина. Коля, видимо, гуляет в парке.")
            return self.go()
        if s["romance"] >= 3 and s["drunk"] < 6 and chance(0.6):
            self.say("🔔 «Кто? …А, Тахта. Ну, спускаюсь»." )
            return self.kolya("yard")
        if s["drunk"] >= 6:
            s["romance"] -= 1
            self.say("🔔 «Тахта, ты пьяная. Иди домой». Щелчок. −1 💘")
        else:
            self.say("🔔 Из динамика: «Я занят». Щелчок.")
        self.go()

    # ---------- друзья Коли
    def chicha(self):
        txt = "Чича щерится: «О, Тахта! Анекдот хочешь? Короче, заходит алкашка в бар…»"
        ch = [("😂 Посмеяться над шутками", self.chi_laugh),
              ("💰 Купить инфу про Колю (50 ₽)", self.chi_info),
              ("😘 Пофлиртовать", self.chi_flirt),
              ("↩️ Отойти", self.back)]
        self.scene("Чича", txt, ch)

    def chi_laugh(self):
        self.advance(15)
        if self.f.get("chi_laugh") != self.day():
            self.f["chi_laugh"] = self.day()
            self.s["fr"]["chicha"] += 1
            self.say("😂 Ты ржёшь над пошлыми анекдотами. Чича доволен: «Свой человек!» (Чича +1)")
        else:
            self.say("😂 Анекдоты пошли по второму кругу.")
        self.go()

    def chi_info(self):
        if not self.pay(50):
            return self.go()
        self.advance(10)
        self.f["code"] = True
        self.f["know_park"] = True
        self.f["ksy_dirt"] = True
        self.say("💰 Чича прячет купюру: «Коля вечером в парке с йорком, с семи до девяти. Код домофона — 147. "
                 "А Ксюху бывший в ЗАГСе бросил — она бесится, когда напоминают». ")
        self.go()

    def chi_flirt(self):
        self.advance(10)
        ch = [("✋ Резко отказать", self.chi_refuse),
              ("😅 Отшутиться", self.chi_joke),
              ("👋 Влепить пощёчину", self.chi_slap)]
        self.scene("Чича", "Чича понимает флирт по-своему и начинает распускать руки.", ch)

    def chi_refuse(self):
        self.s["fr"]["chicha"] -= 1
        self.s["rep"] -= 1
        self.say("✋ «Руки убрал». Чича злится: «Да кому ты нужна». К вечеру по району ползут гадкие слухи. (Чича −1, −репутация)")
        self.go()

    def chi_joke(self):
        self.s["fr"]["chicha"] += 1
        self.say("😅 Ты выкручиваешься шуткой. Чича хохочет и отстаёт. (Чича +1)")
        self.go()

    def chi_slap(self):
        self.s["fr"]["chicha"] -= 1
        self.say("👋 Звонкая пощёчина. Чича звереет.")
        self.fight("chicha", public=False,
                   win=lambda: self._after(lambda: self.s.__setitem__("rep", self.s["rep"] + 1),
                                           "Чича держится за нос: «Бешеная!» Зато уважают. +репутация"))

    def dron(self):
        ch = [("💬 Поговорить", self.dron_talk),
              ("💪 Армрестлинг", self.arm),
              ("🤬 Оскорбить", self.dron_insult),
              ("↩️ Отойти", self.back)]
        self.scene("Дрон", "Дрон молча кивает. Бицепс размером с твою голову.", ch)

    def dron_talk(self):
        self.advance(10)
        self.say("💪 " + pick(["«Угу».", "«Ну».", "Дрон долго думает и говорит: «Коля нормальный». Всё.",
                              "«Ксюха мутная». Дрон умеет удивлять."]))
        self.go()

    def arm(self):
        ch = [("💪 Сильно жать", lambda: self.arm_res("hard")),
              ("🦊 Хитрить", lambda: self.arm_res("cheat")),
              ("🏳 Сдаться", lambda: self.arm_res("give"))]
        self.scene("Армрестлинг", "Дрон ставит локоть на стол. Его ладонь — как лопата.", ch)

    def arm_res(self, how):
        s = self.s
        self.advance(10)
        win = False
        if how == "hard":
            win = chance(0.25 + min(0.2, 0.04 * s["drunk"]))
            if not win:
                self.say("💪 Дрон кладёт твою руку без усилия. Все ржут, но необидно.")
        elif how == "cheat":
            if chance(0.3):
                s["fr"]["dron"] -= 1
                self.say("🦊 Дрон замечает, что ты подставила второй локоть. «Нечестно». (Дрон −1)")
            else:
                win = chance(0.5)
                if not win:
                    self.say("🦊 Хитрость не помогла. Дрон даже не заметил.")
        else:
            self.say("🏳 Ты сдаёшься. Дрон хлопает по плечу: «Норм».")
        if win:
            s["fr"]["dron"] += 1
            s["rep"] += 1
            self.say("🏆 Невероятно — рука Дрона касается стола! Он уважительно кивает. (Дрон +1, +репутация)")
        self.go()

    def dron_insult(self):
        self.s["fr"]["dron"] -= 1
        self.say("🤬 «Шкаф безмозглый». Дрон медленно встаёт.")
        self.fight("dron", public=False,
                   win=lambda: self._after(lambda: (self.s.__setitem__("rep", self.s["rep"] + 3),
                                                    self.s["fr"].__setitem__("dron", self.s["fr"]["dron"] + 2)),
                                           "Дрон сидит на земле и смотрит на тебя с восхищением. Легенда! (Дрон +2)"))

    def lifon(self):
        ch = [("🏢 «Помочь с арендаторами» (≈1 ч)", self.lif_rent),
              ("👜 «Отнести сумку» (≈30 мин)", self.lif_bag),
              ("↩️ Отойти", self.back)]
        self.scene("Лифон", "Лифон оглядывается и шепчет: «Есть дело. Не пыльное»." , ch)

    def lif_rent(self):
        s = self.s
        self.advance(60)
        s["fr"]["lifon"] += 1
        m = rint(100, 200)
        s["money"] += m
        self.say("🏢 Ты стоишь «на шухере», пока Лифон выбивает долг из арендаторов. Доля — %d ₽. (Лифон +1)" % m)
        if chance(0.25):
            if chance(0.5):
                return self.arrest("🚓 На выходе из подъезда вас принимает наряд.")
            return self.gop_event()
        self.go()

    def lif_bag(self):
        s = self.s
        self.advance(30)
        s["fr"]["lifon"] += 1
        if chance(0.3):
            return self.arrest("🚓 На полпути тебя останавливает патруль: «Что в сумке?» Лучше бы ты не знала.")
        self.say("👜 Сумка передана какому-то мужику у гаражей. Лифон доволен: держи бутылку. (Лифон +1)")
        self.add("vodka")
        self.go()

    # ---------------------------------------- Наливайка
    def bar_open(self):
        h = self.hour()
        return h >= 10 or h < 2

    def b_bar(self):
        s, sl = self.s, self.slot()
        P = self.P
        if not self.bar_open():
            desc = "Дверь в подвал заперта. Внутри храпит Зинаида. Открываются в 10:00."
            return LOCS["bar"], desc, [("🚪 Ломиться в дверь", self.bar_knock)]
        desc = ("Подвал с липкими столами. Хрипит телевизор, пахнет перегаром. За стойкой — буфетчица Зинаида.\n"
                "Пиво 30 ₽ · стопка водки 50 ₽ · самогон 20 ₽")
        who, acts = [], [("🍺 Подойти к стойке", self.bar_buy)]
        chi = sl in ("day", "evening") and P("chi", 0.4)
        lif = sl in ("day", "evening") and P("lif", 0.4)
        ksy = sl == "evening" and P("ksy", 0.6) and not self.f.get("ksy_out")
        elk = sl == "evening" and P("elk", 0.4)
        dro = sl == "evening" and P("dro", 0.15)
        gop = sl == "night" and P("gop", 0.5)
        if ksy:
            who.append("Ксюха с коктейлем")
            acts.append(("💅 Присесть к Ксюхе", lambda: self.ksy_scene(False)))
        if elk:
            who.append("Элка в углу")
            acts.append(("🙂 Присесть к Элке", self.elka))
        if chi:
            who.append("Чича")
            acts.append(("😏 К Чиче", self.chicha))
        if lif:
            who.append("Лифон")
            acts.append(("🕶 К Лифону", self.lifon))
        if dro:
            who.append("Дрон")
            acts.append(("💪 К Дрону", self.dron))
        if gop:
            who.append("гопники за дальним столом")
        acts += [("🃏 Сесть к мужикам за карты", self.cards),
                 ("🫳 Стащить бутылку со стойки", self.bar_steal),
                 ("💥 Устроить дебош", self.debosh)]
        desc += "\n\nЗдесь: " + (", ".join(who) if who else "пара работяг у телевизора") + "."
        if gop and chance(0.3):
            self.say("😬 Гопники за дальним столом громко обсуждают твою внешность.")
        return LOCS["bar"], desc, acts

    def bar_knock(self):
        self.advance(10)
        if chance(0.4):
            return self.arrest("🚓 Соседи вызвали полицию: «Ломится какая-то в подвал!»")
        if self.s["money"] >= 30:
            self.s["money"] -= 30
            self.drink("glass", "🚪 Зинаида в бигудях высовывается в окошко: «Тридцатка, и вали». Стакан самогона через решётку.")
        else:
            self.say("🚪 Зинаида высовывается: «Денег нет? Вали!» Окошко захлопывается.")
        self.go()

    def bar_buy(self):
        ch = [("🍺 Пиво — 30 ₽", lambda: self.buy_drink(30, "beer")),
              ("🥃 Стопка водки — 50 ₽", lambda: self.buy_drink(50, "shot")),
              ("🫙 Самогон — 20 ₽", lambda: self.buy_drink(20, "samogon")),
              ("🍺 Пиво с собой — 40 ₽", lambda: self.buy_item(40, "beer")),
              ("↩️ Назад", self.back)]
        self.scene("Стойка", "Зинаида протирает стакан грязным полотенцем: «Чего тебе?»", ch)

    def buy_drink(self, price, kind):
        if self.pay(price):
            self.advance(15)
            self.drink(kind)
        self.go()

    def buy_item(self, price, item):
        if self.s["money"] >= price:
            if self.add(item):
                self.s["money"] -= price
                self.say("🛒 Куплено: %s." % ITEMS[item])
        else:
            self.say("💸 Не хватает денег.")
        self.advance(5)
        self.go()

    def cards(self):
        ch = []
        if self.s["money"] >= 20:
            ch.append(("🃏 Ставка 20 ₽", lambda: self.cards_play(20)))
        if self.s["money"] >= 50:
            ch.append(("🃏 Ставка 50 ₽", lambda: self.cards_play(50)))
        if self.s["money"] < 20 and self.bottles():
            ch.append(("🍾 Поставить бутылку", lambda: self.cards_play(0)))
        ch += [("💬 Просто поболтать", self.cards_talk), ("↩️ Назад", self.back)]
        self.scene("Карты", "Мужики режутся в «дурака» на деньги. «Садись, если не боишься»." , ch)

    def cards_play(self, bet):
        s = self.s
        self.advance(20)
        win = chance(0.45 - 0.02 * s["drunk"])
        if bet == 0:
            b = self.bottles()[0]
            if win:
                s["money"] += 40
                self.say("🃏 Выиграла! Бутылка остаётся при тебе, плюс 40 ₽ сверху.")
            else:
                self.remove(b)
                self.say("🃏 Проиграла. %s уходит мужикам." % ITEMS[b])
        elif win:
            s["money"] += bet
            self.say("🃏 Козырный туз! +%d ₽" % bet)
        else:
            s["money"] -= bet
            self.say("🃏 Остаёшься «дурой». −%d ₽" % bet)
        self.go()

    def cards_talk(self):
        self.advance(15)
        self.f["know_park"] = True
        self.say("💬 «Миллионер ваш вечерами в парке с собачонкой гуляет. А Ксюха вокруг круги нарезает»." )
        self.go()

    def bar_steal(self):
        s = self.s
        self.advance(5)
        if chance(0.65 - 0.08 * s["drunk"]):
            s["rep"] -= 1
            item = pick(["vodka", "beer", "samogon"])
            if self.add(item):
                self.say("🫳 Пока Зинаида отвернулась, %s перекочёвывает в твою сумку. (−репутация)" % ITEMS[item])
            return self.go()
        self.say("🫳 «А ну положь!» Зинаида выскакивает из-за стойки с половником.")

        def won():
            if chance(0.5):
                return self.arrest("🚓 Ты отбилась от Зинаиды, но она успела вызвать полицию.")
            self.say("Ты вылетаешь из подвала, пока Зинаида ищет телефон.")
            self.go("yard")

        self.fight("zina", public=True, win=won)

    def debosh(self):
        self.say("💥 Ты опрокидываешь стол и орёшь на весь подвал. Через секунду дерутся все.")

        def won():
            self.s["rep"] += 2
            if chance(0.6):
                return self.arrest("🚓 Ты последней стоишь на ногах посреди разгрома. Тут и входит наряд. (+репутация)")
            self.say("🏆 Ты последней стоишь на ногах и успеваешь уйти до приезда полиции. +репутация")
            self.go("yard")

        self.fight("gang", public=True, win=won)

    # ---------------------------------------- КБ
    def b_kb(self):
        h, sl = self.hour(), self.slot()
        if h < 9 or h >= 23:
            return LOCS["kb"], "Яркая вывеска погашена. Работают с 09:00 до 23:00.", []
        desc = ("Сетевой алкомаркет: камеры, яркий свет, охранник Сергей у входа %s." %
                ("подозрительно щурится" if sl in ("morning", "day") else "лениво листает телефон"))
        acts = [("🛒 Купить", self.kb_buy),
                ("🫳 Попытаться украсть", self.kb_steal),
                ("🙏 Стрельнуть мелочь у входа", self.kb_beg)]
        who = []
        kol = (18 <= h < 21 and self.P("kol", 0.35)) or (sl == "day" and self.P("kol", 0.1))
        ksy = sl == "evening" and self.P("ksy", 0.25) and not self.f.get("ksy_out")
        if kol:
            who.append("<b>Коля</b> выбирает дорогое пиво")
            acts.append(("✨ Подойти к Коле, помочь с выбором", lambda: self.kolya("kb")))
        if ksy:
            who.append("Ксюха с бутылкой шампанского")
            acts.append(("💅 Подойти к Ксюхе", lambda: self.ksy_scene(False)))
        if self.f.get("elka_with") == self.day():
            acts.append(("🎭 Устроить скандал (Элка ворует)", self.kb_scandal))
        if who:
            desc += "\n\nЗдесь: " + ", ".join(who) + "."
        return LOCS["kb"], desc, acts

    def kb_buy(self):
        ch = [("🍺 «Жигулёвское» — 70 ₽", lambda: self.buy_item(70, "beer")),
              ("🍾 Водка — 300 ₽", lambda: self.buy_item(300, "vodka")),
              ("🥂 Шампанское — 250 ₽", lambda: self.buy_item(250, "champ")),
              ("🥃 Коньяк «Хеннесси» — 3000 ₽", lambda: self.buy_item(3000, "cognac")),
              ("🦴 Галета для собак — 20 ₽", lambda: self.buy_item(20, "galeta")),
              ("🧃 Квас (выпить сразу) — 40 ₽", lambda: self.buy_drink(40, "kvass")),
              ("↩️ Назад", self.back)]
        self.scene("Касса «КБ»", "У тебя %d ₽. Кассирша смотрит без интереса." % self.s["money"], ch)

    def kb_steal(self):
        s = self.s
        self.advance(10)
        p = (0.3 if self.slot() in ("morning", "day") else 0.42) - 0.03 * s["drunk"]
        if chance(p):
            item = pick(["beer", "vodka", "champ"])
            s["rep"] -= 1
            if self.add(item):
                self.say("🫳 %s под курткой, Сергей ничего не заметил. (−репутация)" % ITEMS[item])
            return self.go()
        self.say("🫳 Пищит рамка. Сергей перегораживает выход: «Стоять!»")

        def won():
            item = pick(["beer", "vodka"])
            self.add(item)
            self.say("Ты прорываешься на улицу с бутылкой. Сергей держится за ухо.")
            self.go("yard")

        self.fight("guard", public=True, win=won)

    def kb_beg(self):
        s = self.s
        self.advance(20)
        p = 0.6 if s["rep"] <= 0 else 0.35 if s["rep"] < 3 else 0.15
        if chance(p):
            m = rint(10, 40)
            s["money"] += m
            self.say("🙏 Сердобольная женщина сыплет мелочь: +%d ₽." % m)
        elif s["rep"] >= 3:
            self.say("🙏 «Ты ж Тахта, у тебя всё есть! Иди отсюда». Слава бежит впереди тебя.")
        else:
            self.say("🙏 Покупатели отводят глаза. Сергей кивает на дверь.")
        self.go()

    def kb_scandal(self):
        s = self.s
        self.advance(15)
        s["rep"] -= 1
        self.f["elka_with"] = None
        item = pick(["vodka", "champ", "cognac"])
        self.say("🎭 Ты устраиваешь сцену у кассы, Сергей бежит к тебе — а Элка под шумок выносит %s. "
                 "Она отдаёт добычу тебе и убегает домой. (−репутация)" % ITEMS[item])
        self.add(item)
        if chance(0.25):
            return self.arrest("🚓 Сергей успел нажать тревожную кнопку.")
        self.go()

    # ---------------------------------------- Пятёрочка
    def b_pyat(self):
        h, sl = self.hour(), self.slot()
        if h < 8 or h >= 22:
            return LOCS["pyat"], "Закрыто. Работают с 08:00 до 22:00.", []
        desc = ("Очередь, крики детей, «Уважаемые покупатели!» по громкой связи. "
                "За кассой — тётя Зина, у входа дремлет охранник.")
        acts = [("🛒 Купить", self.py_buy),
                ("🫳 Украсть", self.py_steal),
                ("🔎 Поискать просрочку", self.py_expired),
                ("💬 Поговорить с Зиной", self.py_zina)]
        if self.has("bag"):
            acts.append(("🛍 Сдать бутылки", self.py_bottles))
        if sl in ("day", "evening") and self.P("elk", 0.25):
            desc += "\n\nЗдесь: Элка затаривается мукой для пирогов."
            acts.append(("🙂 Заговорить с Элкой", self.elka))
        return LOCS["pyat"], desc, acts

    def py_buy(self):
        ch = [("🍷 Портвейн «777» — 120 ₽", lambda: self.buy_item(120, "port")),
              ("🍺 Пиво — 60 ₽", lambda: self.buy_item(60, "beer")),
              ("🥐 Булка — 35 ₽", lambda: self.buy_item(35, "bun")),
              ("🦴 Галета для собак — 25 ₽", lambda: self.buy_item(25, "galeta")),
              ("↩️ Назад", self.back)]
        self.scene("Касса «Пятёрочки»", "У тебя %d ₽. Тётя Зина зевает." % self.s["money"], ch)

    def py_steal(self):
        s = self.s
        self.advance(10)
        if chance(0.55 - 0.06 * s["drunk"]):
            item = pick(["port", "beer", "bun"])
            s["rep"] -= 1
            if self.add(item):
                self.say("🫳 %s в рукаве. Никто не заметил. (−репутация)" % ITEMS[item])
            return self.go()
        ch = [("🙌 Не сопротивляться", lambda: self.arrest("🚓 Охранник вызывает полицию. Ты сидишь в подсобке среди коробок.")),
              ("💪 Вырваться", self.py_resist)]
        self.scene("Попалась!", "Охранник хватает тебя за руку: «Попалась, голубушка!»", ch)

    def py_resist(self):
        def won():
            self.say("Ты вырываешься и убегаешь во двор.")
            self.go("yard")
        self.fight("guard5", public=True, win=won)

    def py_expired(self):
        self.advance(15)
        if self.f.get("expired") != self.day() and chance(0.5):
            self.f["expired"] = self.day()
            if self.add("sour"):
                self.say("🔎 На нижней полке за коробками — бутылка вина с истёкшим сроком. Кисловатое, но бесплатное.")
        else:
            self.say("🔎 Только просроченный кефир. Не то.")
        self.go()

    def py_zina(self):
        self.advance(15)
        self.f["know_park"] = True
        self.say("💬 Тётя Зина понижает голос: " + pick([
            "«Коля твой по вечерам в КБ за дорогим пивом ходит, а потом с собачкой в парк, с семи до девяти»." ,
            "«Ксюха за ним хвостом. Вчера шампанское брала, губы накрасила — во!»",
            "«Коля один заходит, всегда вежливый. Собачке галеты берёт»." ,
        ]))
        self.go()

    def py_bottles(self):
        self.remove("bag")
        m = rint(40, 70)
        self.s["money"] += m
        self.advance(10)
        self.say("🛍 Пункт приёма стеклотары: +%d ₽." % m)
        self.go()

    # ---------------------------------------- Гаражи
    def b_gar(self):
        s, sl = self.s, self.slot()
        P = self.P
        desc = ("Ржавые ряды гаражей, запах бензина и сигарет. В дальнем углу у деда Макара булькает аппарат. "
                "Стакан первача — 10 ₽, бутылка — 50 ₽.")
        dro = (sl == "evening" and P("dro", 0.8)) or (sl in ("day", "night") and P("dro", 0.3))
        chi = sl == "evening" and P("chi", 0.2)
        lif = P("lif", 0.3)
        gop = sl in ("evening", "night") and P("gop", 0.5)
        who = ["дед Макар"]
        acts = [("🥛 Стакан первача — 10 ₽", lambda: self.buy_drink(10, "glass")),
                ("🫙 Бутылку самогона — 50 ₽", lambda: self.buy_item(50, "samogon")),
                ("🧰 Предложить деду Макару помощь в сбыте", self.makar_help),
                ("🫳 Стащить чужой самогон", self.gar_steal)]
        if dro:
            who.append("Дрон качается на турнике")
            acts.append(("💪 Подойти к Дрону", self.dron))
        if chi:
            who.append("Чича")
            acts.append(("😏 К Чиче", self.chicha))
        if lif:
            who.append("Лифон на «деловых переговорах»")
            acts.append(("🕶 К Лифону", self.lifon))
        if gop:
            who.append("толпа гопников")
            if s["rep"] >= 2 or s["fr"]["dron"] >= 1:
                acts.append(("🥊 Вписаться в драку стенка на стенку", self.gang_fight))
            acts.append(("😠 Наехать на гопников", self.gang_fight))
        desc += "\n\nЗдесь: " + ", ".join(who) + "."
        return LOCS["gar"], desc, acts

    def makar_help(self):
        s = self.s
        self.advance(60)
        m = rint(80, 150)
        s["money"] += m
        self.say("🧰 Ты разносишь «лекарство» по проверенным квартирам. Дед Макар платит %d ₽." % m)
        if chance(0.25):
            return self.arrest("🚓 В одной из квартир дверь открывает участковый.")
        ch = [("🥛 Принять угощение", lambda: (self.drink("glass", "🥛 Макар наливает стакан: «За труды»."), self.go())),
              ("🙅 Отказаться", self.back)]
        self.scene("Дед Макар", "Дед Макар подмигивает: «Стаканчик за счёт заведения?»", ch)

    def gar_steal(self):
        s = self.s
        self.advance(10)
        if chance(0.45 - 0.04 * s["drunk"]):
            if self.add("samogon"):
                self.say("🫳 Ты тихо утаскиваешь бутыль из-под брезента.")
            return self.go()
        self.say("🫳 «Держи воровку!» — за тобой бегут внуки деда Макара.")
        self.fight("makar", public=False)

    def gang_fight(self):
        self.say("🥊 Стенка на стенку! Дрон, если он тут, встаёт рядом с тобой.")

        def won():
            self.s["rep"] += 3
            self.s["fr"]["dron"] += 1
            self.say("🏆 Гопники разбегаются. О тебе будут говорить во всех дворах. (+репутация, Дрон +1)")
            self.go()

        def lost():
            self.s["hp"] = 0
            self.say("Тебя бьют долго и со вкусом.")
            self.go()

        self.fight("gang", public=False, win=won, lose=lost)

    # ---------------------------------------- Парк
    def b_park(self):
        s, sl, h = self.s, self.slot(), self.hour()
        P = self.P
        desc = {
            "morning": "Аллеи, сухой фонтан. Бегуны и пенсионеры с газетами.",
            "day": "Мамаши с колясками, дети лезут в сухой фонтан.",
            "evening": "Вечерний парк: парочки, собачники, фонари в листве. Любимое время Коли.",
            "night": "Ночью в парке пьяные компании и бомжи. Небезопасно.",
        }[sl]
        acts, who = [], []
        if sl == "evening":
            acts.append(("⏳ Ждать Колю у фонтана", self.wait_kolya))
            if 19 <= h < 21 and P("kol", 0.9):
                who.append("<b>Коля</b> с йорком Тишей")
                acts.insert(0, ("✨ Подойти к Коле", lambda: self.kolya("park")))
            if not self.f.get("ksy_out") and P("ksy", 0.35):
                who.append("Ксюха «случайно» прогуливается")
                acts.append(("💅 Подойти к Ксюхе", lambda: self.ksy_scene(False)))
            if P("elk", 0.25):
                who.append("Элка на скамейке")
                acts.append(("🙂 Подсесть к Элке", self.elka))
        if sl == "morning" and self.weekend() and P("mom", 0.5):
            who.append("мама гуляет по аллее")
            acts.append(("👩 Подойти к маме", self.park_mom))
        if sl == "night":
            acts.append(("🌙 Искать приключений", self.park_night))
        else:
            acts.append(("🪑 Посидеть на скамейке", self.park_sit))
        if who:
            desc += "\n\nЗдесь: " + ", ".join(who) + "."
        return LOCS["park"], desc, acts

    def park_sit(self):
        self.advance(30)
        self.say("🪑 Ты сидишь на скамейке и смотришь на голубей.")
        self.go()

    def park_mom(self):
        s = self.s
        self.advance(20)
        if s["drunk"] < 3:
            s["mom"] += 1
            self.say("👩 Вы гуляете с мамой под руку. Она рассказывает про соседей и улыбается.")
        else:
            s["mom"] -= 1
            self.say("👩 Мама видит тебя и сворачивает на другую аллею.")
        self.go()

    def wait_kolya(self):
        h = self.hour()
        m = self.s["t"] % 1440
        if h < 19:
            self.advance(19 * 60 - m + rint(0, 10))
        elif h < 21:
            self.advance(10)
        else:
            self.advance(15)
            self.say("⏳ Ты ждёшь, но Коля сегодня уже ушёл домой. Он гуляет с 19 до 21.")
            return self.go()
        self.say("⏳ У фонтана появляется Коля с йорком на поводке.")
        self.kolya("park")

    def park_night(self):
        self.advance(20)
        r = random.random()
        if r < 0.4:
            return self.gop_event()
        if r < 0.7:
            item = pick(["beer", "beer", "vodka"])
            if self.add(item):
                self.say("🌙 Под скамейкой кто-то забыл: %s." % ITEMS[item])
        else:
            self.drink("sip", "🌙 Бомж у фонтана молча протягивает тебе бутылку. Ночь сближает.")
        self.go()

    # ---------------------------------------- Вытрезвитель
    def ivan_here(self):
        h = self.hour()
        return (h >= 22 or h < 7) or self.P("ivan", 0.5)

    def b_vytrez(self):
        s = self.s
        h = self.hour()
        desc = ("Казённое здание при отделении №5. Палата с железными кроватями, решётки, хлорка. "
                "На соседней койке храпит забулдыга.")
        acts = [("🛏 Проспаться", self.vyt_sleep)]
        ivan = self.ivan_here() and not self.f.get("ivan_turned")
        if ivan:
            desc += "\n\nСанитар <b>Иван</b> (50 лет, трезвенник с 10-летним стажем) моет пол."
            acts.append(("🧔 Поговорить с Иваном", self.ivan_talk))
            if self.f.get("ivan_agreed") and self.f.get("meeting_at") is None and (h >= 22 or h < 7):
                acts.append(("🕯 Пойти на собрание «12 шагов»", self.meeting))
        elif self.f.get("ivan_turned"):
            desc += "\n\nИван проходит мимо и не смотрит на тебя."
        can_leave = not self.f.get("must_stay") or (s["drunk"] <= 2 and 7 <= h < 21)
        if can_leave:
            acts.append(("🚪 Выписаться и уйти", self.vyt_leave))
        else:
            desc += "\n\n<i>Отпустят, когда протрезвеешь (опьянение ≤2) и наступит день.</i>"
            acts.append(("🏃 Попытаться сбежать", self.vyt_escape))
        acts.append(("📞 Попросить позвонить Коле", self.vyt_call_kolya))
        acts.append(("📞 Попросить позвонить маме", self.vyt_call_mom))
        return LOCS["vytrez"], desc, acts

    def vyt_sleep(self):
        s = self.s
        self.advance(240, sleep=True)
        s["drunk"] = 0
        s["hp"] += 2
        self.say("🛏 Ты проспалась на железной койке. Голова ясная. Опьянение 0, +2 ❤️")
        self.go()

    def vyt_leave(self):
        self.f["must_stay"] = False
        self.advance(15)
        self.say("🚪 Дежурный выдаёт шнурки и паспорт: «Свободна. Не возвращайся». Ты выходишь во двор.")
        self.s["loc"] = "yard"
        self.go("yard")

    def vyt_escape(self):
        s = self.s
        self.advance(15)
        if chance(0.45 - 0.03 * s["drunk"]):
            self.f["escaped"] = True
            self.f["must_stay"] = False
            self.say("🏃 Ты выскальзываешь через окно в туалете и бежишь дворами домой.")
            return self.go("yard")
        self.say("🏃 Дежурный ловит тебя за шиворот у самой двери.")
        if s["money"] >= 500:
            s["money"] -= 500
            self.say("Штраф за попытку побега: −500 ₽.")
            return self.go()
        return self.arrest("Денег на штраф нет — оформляют привод.")

    def vyt_call_kolya(self):
        s = self.s
        self.advance(15)
        if s["romance"] > 5:
            self.f["must_stay"] = False
            self.say("📞 Через полчаса приезжает Коля, о чём-то тихо говорит с дежурным и забирает тебя домой. "
                     "«Тахта, ну ты даёшь». В голосе — забота.")
            self.advance(30)
            return self.go("home")
        self.say("📞 Коля не берёт трубку.")
        self.go()

    def vyt_call_mom(self):
        s = self.s
        self.advance(15)
        if s["mom"] >= 2:
            s["mom"] -= 1
            self.f["must_stay"] = False
            self.say("📞 Мама приезжает на такси — в халате и с лицом мученицы. Забирает домой.")
            self.advance(30)
            return self.go("home")
        self.say("📞 Мама: «Сиди там, может, ума наберёшься». Гудки.")
        self.go()

    def ivan_talk(self):
        s = self.s
        self.advance(15)
        if s["drunk"] >= 3:
            self.say("🧔 Иван качает головой: «Проспись сначала. Потом поговорим»." )
            return self.go()
        if self.f.get("meeting_at") is not None:
            left = max(0, self.f["meeting_at"] + 1440 - s["t"])
            self.say("🧔 «Держишься? Ещё %d ч. Без крепкого и без драк. Я в тебя верю»." % (left // 60 + 1))
            return self.go()
        if self.f.get("ivan_agreed"):
            self.say("🧔 «Собрание по ночам, в подсобке. Приходи после десяти»." )
            return self.go()
        ch = [("🤝 Согласиться прийти", self.ivan_yes), ("🙅 Отказаться", self.ivan_no)]
        self.scene("Иван", "Иван садится на край койки: «Я десять лет назад лежал вот тут же. "
                   "По ночам у нас собрание — «12 шагов». Никто не будет учить жизни. Просто приходи»." , ch)

    def ivan_yes(self):
        self.f["ivan_agreed"] = True
        self.say("🤝 «Вот и хорошо. После десяти вечера, в подсобке»." )
        self.go()

    def ivan_no(self):
        self.say("🙅 Иван пожимает плечами: «Дверь открыта»." )
        self.go()

    def meeting(self):
        self.advance(30)
        txt = ("Подсобка. Кружок стульев, электрический чайник, восемь человек с серыми лицами. "
               "Иван говорит: «Расскажи о себе. Сколько сможешь». Все смотрят на тебя.")
        ch = [("😔 Признать своё бессилие перед бутылкой", lambda: self.meeting_choice("admit")),
              ("🙏 Попросить прощения у близких", lambda: self.meeting_choice("sorry")),
              ("🤲 Пообещать помогать другим", lambda: self.meeting_choice("help")),
              ("🚪 Встать и уйти", lambda: self.meeting_choice("leave"))]
        self.scene("Собрание «12 шагов»", txt, ch)

    def meeting_choice(self, c):
        s = self.s
        if c == "leave":
            self.say("🚪 Ты выходишь. Иван не останавливает.")
            return self.go()
        self.f["meeting_at"] = s["t"]
        if c == "admit":
            s["thirst"] = max(0, s["thirst"] - 2)
            self.say("😔 «Меня зовут София. Я алкоголичка». Голос дрожит. Кто-то хлопает. Становится легче дышать.")
        elif c == "sorry":
            s["mom"] += 2
            self.say("🙏 Ты звонишь маме из подсобки и просишь прощения. Мама долго молчит в трубку, потом плачет.")
        else:
            s["rep"] += 1
            self.say("🤲 Ты обещаешь помогать тем, кто придёт после тебя. Иван кивает.")
        self.say("🧔 Иван: «Теперь сутки. Без крепкого алкоголя и без драк. Не сбегай отсюда. "
                 "Справишься — я стану твоим наставником».\n<i>Жажда теперь растёт вдвое медленнее.</i>")
        self.go()

    # ---------------------------------------- Участок
    def b_police(self):
        s = self.s
        fine = self.f.get("fine", 400)
        desc = ("Участок №5. Дежурный печатает протокол двумя пальцами.\n"
                "«Ну что, гражданка, будем оформлять?»")
        acts = []
        if s["money"] >= fine:
            acts.append(("💸 Заплатить штраф — %d ₽" % fine, self.pol_fine))
        if s["money"] >= 1000:
            acts.append(("🤫 Дать взятку — 1000 ₽", self.pol_bribe))
        acts += [("🧹 Отработать уборкой (2 ч)", self.pol_work),
                 ("📞 Позвонить Коле", self.pol_kolya),
                 ("🔒 Провести ночь в камере", self.pol_cell),
                 ("👊 Сопротивляться", self.pol_resist)]
        return LOCS["police"], desc, acts

    def release(self, record=True, to="yard"):
        if record:
            self.s["arrests"].append(self.s["t"])
        self.s["loc"] = to
        self.go(to)

    def pol_fine(self):
        self.s["money"] -= self.f.get("fine", 400)
        self.advance(30)
        self.say("💸 Штраф оплачен, привод записан. Тебя отпускают.")
        self.release()

    def pol_bribe(self):
        self.s["money"] -= 1000
        self.advance(15)
        self.say("🤫 Купюра исчезает в ящике стола. Протокол — в мусорке. Никаких записей.")
        self.release(record=False)

    def pol_work(self):
        self.advance(120)
        self.say("🧹 Два часа ты метёшь территорию у отделения. Привод записан, но без штрафа.")
        self.release()

    def pol_kolya(self):
        s = self.s
        self.advance(20)
        if s["romance"] > 5:
            self.say("📞 Коля приезжает, жмёт руку дежурному — и всё «порешано». «Поехали, горе моё». Без записи.")
            self.advance(30)
            return self.release(record=False, to="home")
        self.say("📞 Коля не берёт трубку.")
        self.go()

    def pol_cell(self):
        self.advance(self.minutes_to_morning(), sleep=True)
        self.s["arrests"].append(self.s["t"])
        self.f["must_stay"] = False
        self.s["drunk"] = 0
        self.say("🔒 Ночь на нарах, утро в вытрезвителе. Привод записан. Утром тебя отпускают.")
        self.go("vytrez")

    def pol_resist(self):
        self.say("👊 Ты бросаешься на сержанта. Плохая идея.")

        def won():
            self.s["rep"] += 2
            self.s["arrests"].append(self.s["t"])
            self.say("🏃 Невероятно, но ты вырываешься и убегаешь! Привод всё равно записан. (+репутация)")
            self.go("yard")

        def lost():
            self.s["arrests"].append(self.s["t"])
            self.s["hp"] -= 1
            self.say("Тебя скручивают. Дополнительный привод за сопротивление.")
            self.pol_cell()

        self.fight("cop", public=False, win=won, lose=lost, surr=lost)

    def arrest(self, why):
        self.s["fight"] = None
        self.s["meet"] = None
        self.f["fine"] = rint(3, 5) * 100
        self.s["loc"] = "police"
        self.say(why)
        self.advance(20)
        self.go("police")

    # ================================================================= КОЛЯ И КОНКУРЕНТКИ
    def kolya(self, where):
        s = self.s
        m = s.get("meet")
        if not m or m.get("w") != where:
            ksy = (where in ("park", "yard") and self.slot() == "evening" and not self.f.get("ksy_out") and chance(0.35))
            s["meet"] = m = dict(w=where, talk=False, bench=False, help=False, loan=False, ksy=ksy, ksy_done=False)
            if self.f.get("elka_with") == self.day():
                m["elka"] = True
        self.kolya_scene()

    def kolya_scene(self):
        s = self.s
        m = s["meet"]
        if m is None:
            return self.go()
        where = m["w"]
        o = s["outfit"]
        txt = {"park": "Коля в дорогой куртке, на поводке — йорк Тиша.",
               "yard": "Коля у подъезда. Йорк Тиша обнюхивает твои ботинки.",
               "kb": "Коля задумчиво смотрит на полку с крафтовым пивом."}[where]
        txt += "\n" + {"scarf": "Коля приподнимает бровь: «Тахта, ты сегодня прям как в церковь собралась. Тебе идёт».",
                       "dress": "Коля присвистывает. Тиша лает на блёстки.",
                       "casual": "Коля кивает: «Привет, соседка»."}[o]
        if s["drunk"] >= 6:
            txt += "\nКоля морщится от запаха."
        if m.get("elka"):
            txt += "\nЭлка рядом с тобой и нервно хихикает."
        txt += "\n\n💘 Роман: %d/10" % s["romance"]
        ch = []
        if not m["talk"]:
            ch.append(("💬 Заговорить", self.k_talk))
        if self.has("galeta") and self.f.get("york") != self.day() and where != "kb":
            ch.append(("🦴 Покормить йорка галетой", self.k_feed))
        if where == "kb" and not m["help"]:
            ch.append(("🛒 Помочь выбрать пиво", self.k_help))
        if where == "park" and not m["bench"] and s["romance"] >= 3:
            ch.append(("🌳 Присесть рядом на скамейку, поговорить о жизни", self.k_bench))
        if s["romance"] >= 4 and not m["loan"] and self.f.get("loan") != self.day():
            ch.append(("💸 Попросить в долг", self.k_loan))
        ch.append(("👋 Попрощаться", self.k_bye))
        self.scene("✨ Коля", txt, ch)

    def k_after(self):
        """После действия: может вмешаться Ксюха."""
        m = self.s["meet"]
        if m and m.get("ksy") and not m.get("ksy_done") and not self.f.get("ksy_out"):
            m["ksy_done"] = True
            return self.ksy_scene(True)
        self.kolya_scene()

    def k_talk(self):
        s = self.s
        m = s["meet"]
        m["talk"] = True
        self.advance(15)
        if s["drunk"] >= 6:
            s["romance"] -= 1
            self.say("💬 Ты несёшь что-то бессвязное. Коля: «Тахта, ты опять?» −1 💘")
            return self.k_after()
        p = 0.5 + self.outfit_k() + self.pers_mod() + 0.02 * s["romance"]
        if m.get("elka"):
            if chance(0.5):
                p += 0.15
                self.say("Элка удачно вставляет: «Софа у нас добрая, собак любит!»")
            else:
                p -= 0.15
                self.say("Элка невпопад рассказывает про свои пироги. Неловко.")
        if chance(p):
            s["romance"] += 1
            self.say("💬 " + pick(["Вы болтаете про район, Коля смеётся твоей шутке.",
                                   "Коля рассказывает про бизнес, ты внимательно слушаешь.",
                                   "Вы вспоминаете школу — оказывается, учились у одной химички."]) + " +1 💘")
        else:
            self.say("💬 Разговор не клеится. Коля поглядывает на часы.")
        self.k_after()

    def k_feed(self):
        s = self.s
        self.remove("galeta")
        self.f["york"] = self.day()
        s["romance"] += 2
        self.advance(10)
        self.say("🦴 Тиша хрустит галетой и лижет тебе руку. Коля тает: «О, ты любишь собак? Молодец, Тахта». +2 💘")
        self.k_after()

    def k_help(self):
        s = self.s
        s["meet"]["help"] = True
        self.advance(10)
        if chance(0.6 + self.pers_mod()):
            s["romance"] += 1
            self.say("🛒 Ты со знанием дела советуешь бельгийское. Коля впечатлён: «А ты шаришь!» +1 💘")
        else:
            self.say("🛒 Ты советуешь «Жигулёвское». Коля вежливо улыбается и берёт другое.")
        self.k_after()

    def k_bench(self):
        s = self.s
        s["meet"]["bench"] = True
        self.advance(30)
        p = 0.3 + 0.06 * s["romance"] + self.outfit_k() + self.pers_mod()
        if chance(p):
            s["romance"] += 2
            self.say("🌳 Вы сидите на скамейке, Тиша дремлет у Коли на коленях. Коля говорит, что устал от "
                     "фальшивых людей, а с тобой просто. +2 💘")
        else:
            s["romance"] -= 1
            self.say("🌳 Ты слишком торопишься с откровениями. Коля отодвигается: «Мне пора». −1 💘")
        self.k_after()

    def k_loan(self):
        s = self.s
        s["meet"]["loan"] = True
        self.f["loan"] = self.day()
        m = rint(10, 30) * 10
        s["money"] += m
        s["romance"] -= 1
        self.advance(5)
        self.say("💸 Коля молча достаёт %d ₽. Взгляд у него становится чуть холоднее. −1 💘" % m)
        self.k_after()

    def k_bye(self):
        self.s["meet"] = None
        self.say("👋 Коля уходит. Тиша оглядывается на тебя.")
        self.go()

    def ksy_scene(self, kolya_here):
        self.f["ksy_k"] = kolya_here
        txt = ("Ксюха в боевом макияже: «О, Тахта выползла. Коля, ты с ней осторожно — заразно»."
               if kolya_here else "Ксюха смеряет тебя взглядом: «Чего припёрлась? Коля не для таких, как ты»." )
        ch = [("🗣 Ответить достойно", self.ksy_verbal),
              ("👊 Вцепиться ей в волосы", self.ksy_fight),
              ("🙄 Не обращать внимания", self.ksy_ignore)]
        self.scene("💅 Ксюха", txt, ch)

    def ksy_return(self):
        if self.f.get("ksy_k") and self.s.get("meet"):
            return self.kolya_scene()
        self.go()

    def ksy_verbal(self):
        s = self.s
        kh = self.f.get("ksy_k")
        self.advance(10)
        p = 0.45 + self.pers_mod() + (0.25 if self.f.get("elka_help") else 0) + (0.2 if self.f.get("ksy_dirt") else 0)
        if chance(p):
            self.f["ksy_shame"] = self.f.get("ksy_shame", 0) + 1
            s["rep"] += 1
            line = "🗣 " + ("Ты небрежно напоминаешь про ЗАГС. Ксюха краснеет до ушей." if self.f.get("ksy_dirt")
                           else "Ты отвечаешь так метко, что вокруг смеются. Ксюха краснеет.")
            if self.f.get("elka_help"):
                line += " Элка «случайно» опрокидывает на Ксюху стакан с томатным соком."
            if kh:
                s["romance"] += 1
                line += " Коля прячет улыбку. +1 💘"
            self.say(line + " (+репутация)")
            if self.f["ksy_shame"] >= 2:
                self.f["ksy_out"] = True
                self.say("💅 Ксюха убегает в слезах. Говорят, она уезжает к тётке в Тверь. <b>Конкурентка опозорена.</b>")
        else:
            s["rep"] -= 1
            line = "🗣 Ксюха оказывается острее на язык. Ты не находишь слов. (−репутация)"
            if kh:
                s["romance"] -= 1
                line += " −1 💘"
            self.say(line)
        self.ksy_return()

    def ksy_fight(self):
        kh = self.f.get("ksy_k")
        self.say("👊 Ты бросаешься на Ксюху.")

        def won():
            s = self.s
            self.f["ksy_out"] = True
            s["rep"] += 2
            s["romance"] += 1
            self.say("🏆 Ксюха сидит на асфальте с размазанной тушью. Через час об этом знает весь район, и Коля тоже: "
                     "«Ну ты даёшь, Тахта». <b>Конкурентка опозорена.</b> (+репутация, +1 💘)")
            if self.s["loc"] in ("bar", "yard", "kb") and chance(0.3):
                return self.arrest("🚓 Но кто-то всё-таки вызвал полицию.")
            self.ksy_return()

        def lost():
            s = self.s
            s["rep"] -= 1
            if kh:
                s["romance"] -= 1
            self.say("Ксюха победно поправляет причёску. (−репутация)")
            if chance(0.3):
                return self.arrest("🚓 Приехала полиция разнимать.")
            self.ksy_return()

        self.fight("ksy", public=True, win=won, lose=lost)

    def ksy_ignore(self):
        if self.f.get("ksy_k"):
            self.s["romance"] -= 1
            self.say("🙄 Ты молчишь, а Ксюха уводит Колю разговором про театр. −1 💘")
        else:
            self.say("🙄 Ты проходишь мимо. Ксюха фыркает в спину.")
        self.ksy_return()

    def elka(self):
        ch = [("🤗 Утешить, пожалеть", self.el_comfort),
              ("🍺 Подпоить (30 ₽ или своя бутылка)", self.el_drink)]
        if self.f.get("elka_ok"):
            ch.append(("🤝 Позвать Элку с собой", self.el_take))
        ch += [("👊 Наехать на Элку", self.el_fight), ("↩️ Отойти", self.back)]
        txt = "Элка теребит рукав: «Мама опять орала… А ты тоже по Коле сохнешь, да?»"
        if self.f.get("elka_ok"):
            txt = "Элка тебе рада: «Софа! Посиди со мной»."
        self.scene("🙂 Элка", txt, ch)

    def el_comfort(self):
        self.advance(20)
        self.f["elka_ok"] = True
        self.say("🤗 Ты слушаешь про маму Элки и гладишь её по плечу. Элка хлюпает носом: «Ты хорошая. "
                 "Забирай своего Колю, мне он всё равно не по зубам». <b>Элка больше не соперница.</b>")
        self.go()

    def el_drink(self):
        s = self.s
        b = self.bottles()
        if b:
            self.remove(b[0])
        elif not self.pay(30):
            return self.go()
        self.advance(30)
        self.f["elka_ok"] = True
        self.f["elka_help"] = True
        self.drink("beer", "🍺 Вы выпиваете с Элкой. Она хихикает и шепчет: «Ксюха — гадюка. Я тебе помогу, вот увидишь»." )
        self.go()

    def el_take(self):
        self.f["elka_with"] = self.day()
        self.say("🤝 Элка увязывается за тобой на весь день. Может пригодиться в «КБ»… или помешать с Колей.")
        self.go()

    def el_fight(self):
        self.say("👊 «Слышь, отстань от Коли!» Элка испуганно поднимает кулачки.")

        def won():
            self.f["elka_ok"] = True
            self.s["rep"] -= 1
            self.say("Элка убегает в слезах. Больше она к Коле не подойдёт. Но бить Элку — так себе слава. (−репутация)")
            self.go()

        self.fight("elka", public=True, win=won)

    # ================================================================= Гопники
    def gop_event(self):
        s = self.s
        txt = "Из темноты выходят двое в спортивках: «Девушка, а есть мелочь? А если найдём?»"
        ch = []
        if s["money"] >= 50:
            ch.append(("💸 Отдать 50 ₽", self.gop_pay))
        if self.has("lighter"):
            ch.append(("🔥 Дать прикурить", self.gop_light))
        ch += [("👊 Драться", self.gop_fight), ("🏃 Убежать", self.gop_run)]
        self.scene("😬 Гопники", txt, ch)

    def gop_pay(self):
        self.s["money"] -= 50
        self.say("💸 Гопники забирают полтинник и теряют к тебе интерес.")
        self.go()

    def gop_light(self):
        self.say("🔥 Ты чиркаешь зажигалкой. «О, нормальная». Тебя хлопают по плечу и отпускают.")
        self.go()

    def gop_run(self):
        if chance(0.55 - 0.04 * self.s["drunk"]):
            self.advance(5)
            self.say("🏃 Ты ныряешь в подъезд и пережидаешь.")
            return self.go()
        self.say("🏃 Тебя догоняют за углом.")
        self.gop_fight()

    def gop_fight(self):
        def won():
            self.s["rep"] += 2
            self.say("🏆 Гопники ретируются. «Психованная!» (+репутация)")
            self.go()

        def lost():
            self.s["money"] = 0
            self.say("Гопники выворачивают твои карманы до копейки.")
            self.go()

        self.fight("gop", public=False, win=won, lose=lost, surr=lost)

    # ================================================================= ДРАКИ
    def fight(self, key, win=None, lose=None, surr=None, public=False, run_to="yard"):
        e = ENEMIES[key]
        self.s["fight"] = dict(k=key, hp=e["hp"], max=e["hp"], stun=0, public=public, run_to=run_to)
        self.fo = dict(win=win, lose=lose, surr=surr)
        self.f_scene()

    def dmg_mod(self):
        d = self.s["drunk"]
        return 2 if d >= 7 else 1 if d >= 4 else 0

    def def_mod(self):
        d = self.s["drunk"]
        return 0.2 if d >= 7 else 0.1 if d >= 4 else 0

    def f_scene(self):
        F = self.s["fight"]
        e = ENEMIES[F["k"]]
        txt = "⚔️ <b>%s</b> %s %d/%d\n🧍 Ты: ❤️ %d/10 · 🥴 %d" % (e["n"], bar(F["hp"], F["max"]), max(0, F["hp"]), F["max"],
                                                               self.s["hp"], self.s["drunk"])
        ch = [("👊 Ударить в лицо", lambda: self.f_act("face")),
              ("🦵 С ноги", lambda: self.f_act("kick"))]
        if self.bottles():
            ch.append(("🍾 Бутылкой", lambda: self.f_act("item")))
        ch += [("🌀 Уклоняться", lambda: self.f_act("dodge")),
               ("🛡 Блокировать", lambda: self.f_act("block")),
               ("🤫 Ударить исподтишка", lambda: self.f_act("sneak")),
               ("🏖 Кинуть песком в глаза", lambda: self.f_act("sand")),
               ("🏃 Убежать", lambda: self.f_act("run")),
               ("🏳 Сдаться / извиниться", lambda: self.f_act("surr"))]
        self.scene("Драка!", txt, ch)

    def f_act(self, a):
        s = self.s
        F = s["fight"]
        e = ENEMIES[F["k"]]
        if s["drunk"] >= 10:
            return self.f_end("lose", "Ноги не держат. Ты падаешь, бой проигран.")
        if a in ("face", "kick", "item", "sneak"):
            if s["drunk"] >= 7 and chance(0.2):
                self.say("Ты замахиваешься, теряешь равновесие и падаешь.")
                return self.e_turn(1.0)
            p, dmg = {"face": (0.7, rint(1, 2)), "kick": (0.55, rint(2, 3)),
                      "item": (0.75, rint(3, 4)), "sneak": (0.5, 3)}[a]
            if a == "item":
                b = self.bottles()[0]
                self.remove(b)
            dmg += self.dmg_mod()
            mult = 1.0
            if chance(p):
                F["hp"] -= dmg
                self.say({"face": "👊 Хук в челюсть!", "kick": "🦵 Пинок с разворота!",
                          "item": "🍾 Бутылка разлетается об голову!", "sneak": "🤫 Удар исподтишка!"}[a]
                         + " %s −%d" % (e["n"], dmg))
            else:
                self.say("Мимо!")
                if a == "sneak":
                    mult = 1.3
            if F["hp"] <= 0:
                return self.f_end("win")
            return self.e_turn(mult)
        if a == "dodge":
            self.say("🌀 Ты уворачиваешься.")
            return self.e_turn(0.4)
        if a == "block":
            self.say("🛡 Ты закрываешься руками.")
            return self.e_turn(1.0, block=True)
        if a == "sand":
            if chance(0.7 - 0.04 * s["drunk"]):
                F["stun"] = 1
                self.say("🏖 Горсть песка прямо в глаза!")
            else:
                self.say("🏖 Песок улетает мимо.")
            return self.e_turn(1.0)
        if a == "run":
            if chance(0.5 - 0.04 * s["drunk"]):
                return self.f_end("run")
            self.say("🏃 Убежать не вышло.")
            return self.e_turn(1.2)
        return self.f_end("surr")

    def e_turn(self, mult, block=False):
        s = self.s
        F = s["fight"]
        e = ENEMIES[F["k"]]
        self.advance(2)
        if e.get("flee") and F["hp"] <= 2 and chance(0.5):
            return self.f_end("win", "%s решает, что здоровье дороже, и даёт дёру." % e["n"])
        if F["stun"] > 0:
            F["stun"] -= 1
            self.say("%s протирает глаза и не может ударить." % e["n"])
            return self.f_scene()
        p = (0.4 + e["str"] * 0.05 + self.def_mod()) * mult
        if chance(p):
            d = 1 + (1 if e["str"] >= 4 and chance(0.4) else 0)
            extra = ""
            if e.get("item") and chance(0.3):
                d += 1
                extra = " (подручным предметом!)"
            if e.get("dirty") and chance(0.25):
                d += 1
                extra = " (грязный приём!)"
            if block:
                d = max(0, d - 1)
            s["hp"] -= d
            self.say("%s %s%s. −%d ❤️" % (e["n"], pick(e["hits"]), extra, d))
        else:
            self.say("%s промахивается." % e["n"])
        if s["hp"] <= 0:
            return self.f_end("lose")
        self.f_scene()

    def f_end(self, res, msg=None):
        s = self.s
        F = s["fight"]
        e = ENEMIES[F["k"]]
        s["fight"] = None
        self.f["last_fight"] = s["t"]
        if msg:
            self.say(msg)
        if self.sober_path():
            self.f["ivan_turned"] = True
            self.say("<i>Драка. Иван узнает об этом и больше не будет тебя ждать.</i>")
        cb = self.fo.get(res)
        self.fo = {}
        if res == "win":
            self.say("🏆 Победа над противником: %s!" % e["n"])
            return cb() if cb else self.go()
        if res == "run":
            self.say("🏃 Ты удираешь со всех ног.")
            s["loc"] = F["run_to"]
            return self.go(F["run_to"])
        if res == "surr":
            self.say("🏳 Ты поднимаешь руки: «Всё, всё, извини!»")
            if cb:
                return cb()
            if F["k"] in ("guard", "guard5", "cop", "zina"):
                return self.arrest("🚓 Тебя сдают полиции.")
            if s["money"] > 0:
                lost = rint(0, s["money"] // 3)
                s["money"] -= lost
                if lost:
                    self.say("Пришлось откупиться: −%d ₽." % lost)
            return self.go()
        # поражение
        self.say("💀 Ты проиграла драку.")
        if s["money"] > 0:
            lost = rint(0, s["money"] // 2)
            if lost:
                s["money"] -= lost
                self.say("Пока ты лежала, из кармана пропало %d ₽." % lost)
        if s["inv"] and chance(0.3):
            it = pick(s["inv"])
            self.remove(it)
            self.say("Пропало: %s." % ITEMS[it])
        if cb:
            return cb()
        if F["public"] and s["hp"] > 0 and chance(0.6):
            return self.arrest("🚓 На шум приезжает полиция.")
        self.go()

    def _after(self, effect, msg):
        effect()
        self.say(msg)
        self.go()

    # ================================================================= Сумка и подсказки
    def inventory(self):
        s = self.s
        ch = []
        for idx, it in enumerate(s["inv"]):
            if it in BOTTLES:
                ch.append(("Выпить: %s" % ITEMS[it], lambda it=it: self.drink_item(it)))
            elif it == "bun":
                ch.append(("Съесть: %s" % ITEMS[it], self.eat_bun))
            elif it == "phone":
                ch.append(("Позвонить: %s" % ITEMS[it], self.phone))
        if s["inv"]:
            ch.append(("🗑 Выбросить вещь…", self.drop_menu))
        ch.append(("↩️ Закрыть сумку", self.back))
        lst = "\n".join("• " + ITEMS[i] for i in s["inv"]) or "Пусто."
        self.scene("🎒 Сумка (%d/5)" % len(s["inv"]), lst + "\n\n👗 Наряд: %s" % OUTFITS[s["outfit"]], ch)

    def drop_menu(self):
        ch = [("Выбросить: %s" % ITEMS[it], lambda it=it: self.drop(it)) for it in self.s["inv"]]
        ch.append(("↩️ Назад", self.inventory))
        self.scene("Выбросить", "Что выбросить?", ch)

    def drop(self, it):
        self.remove(it)
        self.say("🗑 Выброшено: %s." % ITEMS[it])
        self.inventory()

    def drink_item(self, it, back=None):
        self.remove(it)
        self.advance(5)
        self.drink(it, "Ты пьёшь: %s." % ITEMS[it])
        if back and not self.s["over"]:
            return back()
        self.go()

    def eat_bun(self):
        self.remove("bun")
        self.s["hp"] += 1
        self.s["drunk"] = max(0, self.s["drunk"] - 1)
        self.advance(10)
        self.say("🥐 Булка с маком. +1 ❤️, чуть трезвее.")
        self.go()

    def help(self):
        txt = (
            "<b>Как играть.</b> Ходи по району, выбирай действия. Каждое действие занимает 10–30 минут.\n"
            "• <b>Жажда</b> растёт со временем. На 10 — обморок и вытрезвитель.\n"
            "• <b>Опьянение</b> даёт силу в драке, но мешает в разговорах. На 10 — отключишься.\n"
            "• <b>Здоровье</b> на нуле — больница или хуже.\n"
            "• Если некому помочь (нет денег, Коля и мама отвернулись) — конец.\n\n"
            "<b>Три финала:</b>\n"
            "👑 <b>Королева района</b> — роман с Колей ≥8, Ксюха опозорена, Элка не мешает, "
            "друзья Коли не враги, за последние сутки без приводов.\n"
            "🕊 <b>Просветление</b> — найди Ивана в вытрезвителе, сходи на ночное собрание, "
            "потом сутки без крепкого и без драк, не сбегая.\n"
            "⬛ <b>На дне</b> — три привода и потеря всех связей… лучше не надо.\n\n"
            "<b>Советы:</b> бабки и Зина знают, где бывает Коля. Йорк обожает галеты. "
            "Платок — Коле нравятся скромницы."
        )
        self.scene("📜 Подсказки", txt, [("↩️ Назад", self.back)])

    # ================================================================= ИИ-ДИАЛОГИ
    def active_npc(self):
        """Определяет, с каким персонажем сейчас идёт сцена."""
        if self.s.get("over") or self.s.get("fight"):
            return None
        if not self.sc:
            self.refresh()
        t = self.sc["title"]
        mapping = {
            "✨ Коля": ("kolya", "Коля-Миллионер", "35 лет, обеспеченный сосед в дорогой куртке, гуляет с йорком Тишей. Вежливый, немного сноб, устал от фальши. Ненавидит когда Тахта пьяная (опьянение >= 6), нравятся скромные (в платке) и когда кормят его собаку."),
            "Мама": ("mom", "Мама Софии", "Уставшая советская женщина, работает, тянет квартиру. Переживает за 32-летнюю дочь-алкоголичку Софию (Тахту), ворчит, стыдит за пьянство, но в глубине души любит."),
            "💅 Ксюха": ("ksy", "Ксюха", "Яркая, стервозная конкурентка за сердце Коли. Высокомерная, язвительная. Её главная тайна и боль: бывший бросил её прямо в ЗАГСе."),
            "🙂 Элка": ("elka", "Элка", "Тихая, затюканная матерью соседка, печёт пироги, тайно вздыхает по Коле, но легко уступает, если к ней отнестись по-доброму или выпить с ней."),
            "Чича": ("chicha", "Чича", "Дворовый кент Коли, любитель пошлых анекдотов, сплетен и халявы. За полтинник готов слить любую инфу."),
            "Дрон": ("dron", "Дрон", "Огромный молчаливый качок, друг Коли. Говорит короткими фразами («Угу», «Норм»), уважает только силу и дерзость."),
            "Лифон": ("lifon", "Лифон", "Мутный темщик со двора, постоянно крутит мелкие полукриминальные схемы."),
            "Алкаши на лавочке": ("alk", "Толян и Косой", "Дворовые алкаши на лавочке у подъезда. Душевные, вечно ищут мелочь на опохмел, знают все слухи района."),
            "Бабки у подъезда": ("bab", "Бабки у подъезда", "Бдительные старушки на лавочке. Осуждают за короткие платья и пьянство, хвалят за бабушкин платок, знают всё про всех. Если сильно пьяная — могут вызвать полицию."),
            "Иван": ("ivan", "Санитар Иван", "50 лет, бывший алкоголик, 10 лет в завязке. Работает в вытрезвителе, ведёт ночные собрания «12 шагов». Спокойный, мудрый."),
            "Стойка": ("zina", "Буфетчица Зинаида", "Грубая, прожжённая буфетчица в подвальной наливайке «Угол». В долг не наливает, за буйство бьёт половником."),
            "🚔 Участок №5": ("cop", "Дежурный сержант", "Уставший сержант полиции в участке №5. Оформляет протокол, циничный, не прочь взять взятку, если предложат аккуратно."),
        }
        if t in mapping:
            return mapping[t]
        if self.s["loc"] == "home" and self.mom_state() == "awake":
            return mapping["Мама"]
        return None

    def apply_ai_result(self, npc_id, data):
        """Применяет изменения статов от ИИ к игре."""
        s = self.s
        reply = str(data.get("reply", "...")).strip()
        self.say(f"💬 <b>Ответ:</b> {reply}")
        self.advance(5)

        effects = []
        rom = clamp(int(data.get("romance", 0) or 0), -2, 2)
        if rom and npc_id in ("kolya", "ksy", "elka"):
            s["romance"] = clamp(s["romance"] + rom, 0, 10)
            effects.append(f"{'+' if rom > 0 else ''}{rom} 💘")

        rep = clamp(int(data.get("rep", 0) or 0), -2, 2)
        if rep:
            s["rep"] = clamp(s["rep"] + rep, -10, 10)
            effects.append(f"{'+' if rep > 0 else ''}{rep} 😎")

        mom_d = clamp(int(data.get("mom", 0) or 0), -2, 2)
        if mom_d and npc_id == "mom":
            s["mom"] = clamp(s["mom"] + mom_d, -3, 3)
            effects.append("отношения с мамой " + ("улучшились" if mom_d > 0 else "ухудшились"))

        money = clamp(int(data.get("money", 0) or 0), -100, 150)
        if money > 0 and self.f.get(f"ai_m_{npc_id}") != self.day():
            self.f[f"ai_m_{npc_id}"] = self.day()
            s["money"] += money
            effects.append(f"+{money} ₽")
        elif money < 0 and s["money"] > 0:
            lost = min(s["money"], abs(money))
            s["money"] -= lost
            effects.append(f"−{lost} ₽")

        if data.get("give_drink") and self.f.get(f"ai_dr_{npc_id}") != self.day():
            self.f[f"ai_dr_{npc_id}"] = self.day()
            self.drink("sip", "🍻 Тебя угостили выпивкой.")

        if effects:
            self.say("<i>(" + ", ".join(effects) + ")</i>")

        action = data.get("action", "none")
        if action == "arrest" and self.s["loc"] != "police":
            return self.arrest("🚓 После твоих слов терпение лопнуло — вызвали наряд полиции!")
        if action == "fight" and npc_id in ENEMIES:
            return self.fight(npc_id, public=True)

        if npc_id == "kolya" and s.get("meet"):
            self.kolya_scene()
        elif npc_id == "ksy":
            self.ksy_scene(bool(self.f.get("ksy_k")))
        elif npc_id in ("mom", "elka", "chicha", "dron", "lifon", "ivan"):
            getattr(self, npc_id if npc_id != "mom" else "mom_talk")()
        elif npc_id == "alk":
            self.alkashi()
        elif npc_id == "bab":
            self.babki()
        elif npc_id == "zina":
            self.bar_buy()
        else:
            self.go()
        self.post()
        s["turn"] += 1
