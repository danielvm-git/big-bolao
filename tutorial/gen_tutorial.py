"""Gera o carrossel de tutorial do Big Bolão (slides quadrados 1080x1080).

Pillow puro, sem dependência de fontes coloridas/emoji. Renderiza em 2x e
reduz com LANCZOS pra antialiasing. Paleta = web/src/style.css.

    python tutorial/gen_tutorial.py
Saída: tutorial/slides/NN-*.png  + tutorial/_contact_sheet.png
"""
from __future__ import annotations

import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SS = 2
W = H = 1080
OUT = os.path.join(os.path.dirname(__file__), "slides")
os.makedirs(OUT, exist_ok=True)

# ---- paleta (style.css) ----
BG_DEEP = "#030B16"
BG_SURFACE = "#060E1C"
BG_CARD = "#0F1D2E"
BG_CARD2 = "#162437"
BG_LIGHT = "#122236"
TXT = "#EBF0F5"
TXT2 = "#7A8FA0"
TXT3 = "#94A3B8"
GREEN = "#00DC82"
GOLD = "#F7C948"
BLUE = "#60A5FA"
ORANGE = "#FB923C"
RED = "#F87171"
TG = "#229ED9"  # telegram blue

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
F_REG = os.path.join(FONT_DIR, "DejaVuSans.ttf")
F_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
F_LIGHT = os.path.join(FONT_DIR, "DejaVuSans-ExtraLight.ttf")

_font_cache: dict = {}


def font(size: int, kind: str = "reg") -> ImageFont.FreeTypeFont:
    key = (size, kind)
    if key not in _font_cache:
        path = {"reg": F_REG, "bold": F_BOLD, "light": F_LIGHT}[kind]
        _font_cache[key] = ImageFont.truetype(path, int(size * SS))
    return _font_cache[key]


def _s(v):  # scale scalar
    return int(round(v * SS))


def _b(box):  # scale 4-box
    return [int(round(c * SS)) for c in box]


class Slide:
    def __init__(self):
        self.img = Image.new("RGB", (W * SS, H * SS), BG_DEEP)
        self.d = ImageDraw.Draw(self.img, "RGBA")
        self._background()

    # ---------- background ----------
    def _background(self):
        glow = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse(_b([-180, -260, 620, 360]), fill=(247, 201, 72, 55))   # gold TL
        gd.ellipse(_b([560, 720, 1300, 1400]), fill=(0, 220, 130, 50))    # green BR
        gd.ellipse(_b([700, -200, 1300, 380]), fill=(34, 158, 217, 38))   # blue TR
        glow = glow.filter(ImageFilter.GaussianBlur(_s(120)))
        self.img.paste(Image.alpha_composite(
            self.img.convert("RGBA"), glow).convert("RGB"), (0, 0))
        self.d = ImageDraw.Draw(self.img, "RGBA")
        # fine top hairline
        self.d.rectangle(_b([0, 0, W, 6]), fill=GOLD)

    # ---------- primitives ----------
    def rrect(self, box, r, fill=None, outline=None, width=1):
        self.d.rounded_rectangle(_b(box), radius=_s(r), fill=fill,
                                 outline=outline, width=max(1, _s(width)))

    def ellipse(self, box, fill=None, outline=None, width=1):
        self.d.ellipse(_b(box), fill=fill, outline=outline,
                       width=max(1, _s(width)))

    def line(self, xy, fill, width=1):
        self.d.line([_s(c) for c in xy], fill=fill, width=max(1, _s(width)))

    def tlen(self, s, f):
        return self.d.textlength(s, font=f) / SS

    def text(self, xy, s, f, fill, anchor="la"):
        self.d.text((_s(xy[0]), _s(xy[1])), s, font=f, fill=fill, anchor=anchor)

    def wrap(self, s, f, max_w):
        out, line = [], ""
        for w in s.split():
            t = (line + " " + w).strip()
            if self.tlen(t, f) <= max_w or not line:
                line = t
            else:
                out.append(line)
                line = w
        if line:
            out.append(line)
        return out

    def paragraph(self, xy, s, f, fill, max_w, lh, anchor="la"):
        x, y = xy
        for ln in self.wrap(s, f, max_w):
            self.text((x, y), ln, f, fill, anchor=anchor)
            y += lh
        return y

    # ---------- components ----------
    def tag(self, x, y, label, color=GOLD):
        f = font(20, "bold")
        tw = self.tlen(label, f)
        pad = 22
        self.rrect([x, y, x + tw + pad * 2, y + 46], 23,
                   fill=(255, 255, 255, 8), outline=color, width=2)
        self.ellipse([x + pad - 2, y + 19, x + pad + 6, y + 27], fill=color)
        self.text((x + pad + 16, y + 23), label, f, color, anchor="lm")
        return x + tw + pad * 2

    def step_badge(self, cx, cy, n, color=GOLD):
        self.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=color)
        self.text((cx, cy + 1), str(n), font(34, "bold"), BG_DEEP, anchor="mm")

    def dots(self, active, total, cy=1028):
        gap = 30
        x0 = W / 2 - (total - 1) * gap / 2
        for i in range(total):
            c = GOLD if i == active else (255, 255, 255, 45)
            r = 7 if i == active else 5
            self.ellipse([x0 + i * gap - r, cy - r, x0 + i * gap + r, cy + r], fill=c)

    def country(self, cx, cy, code, color, r=30):
        self.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        self.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 40), width=2)
        self.text((cx, cy + 1), code, font(int(r * 0.62), "bold"), "#FFFFFF", anchor="mm")

    def phone_top(self, box):
        # subtle status bar inside a screen card
        x0, y0, x1, y1 = box
        self.text((x0 + 26, y0 + 26), "9:41", font(17, "bold"), TXT3, anchor="lm")
        for i, w in enumerate([6, 9, 12, 15]):
            bx = x1 - 150 + i * 16
            self.rrect([bx, y0 + 20 - w / 2 + 6, bx + 9, y0 + 32], 3, fill=TXT3)
        self.rrect([x1 - 78, y0 + 16, x1 - 30, y0 + 36], 6, fill=TXT3)

    def screen_card(self, box, top=True):
        self.rrect(box, 34, fill=BG_SURFACE, outline=(255, 255, 255, 28), width=2)
        self.rrect([box[0] + 4, box[1] + 4, box[2] - 4, box[3] - 4], 30,
                   outline=(255, 255, 255, 10), width=2)
        if top:
            self.phone_top(box)
        return [box[0] + 30, box[1] + 64, box[2] - 30, box[3] - 24]

    def save(self, name):
        self.img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, name))


# helper: bot chat bubble
def bubble(s: Slide, x, y, w, text, *, out=False, font_size=21, sub=None):
    f = font(font_size, "reg")
    lines = s.wrap(text, f, w - 56)
    lh = font_size + 12
    h = 30 + len(lines) * lh + (26 if sub else 0)
    fill = TG if out else BG_CARD2
    s.rrect([x, y, x + w, y + h], 20, fill=fill)
    yy = y + 22
    for ln in lines:
        s.text((x + 28, yy), ln, f, "#FFFFFF" if out else TXT, anchor="lm")
        yy += lh
    if sub:
        s.text((x + 28, yy + 2), sub, font(15, "reg"),
               (255, 255, 255, 160) if out else TXT2, anchor="lm")
    return y + h


def header(s: Slide, tag_label, tag_color, n, title, caption, total=12, idx=0):
    s.tag(80, 92, tag_label, tag_color)
    s.step_badge(966, 116, n, tag_color)
    y = s.paragraph((80, 170), title, font(50, "bold"), TXT, 840, 60)
    s.paragraph((80, y + 14), caption, font(25, "reg"), TXT3, 880, 38)
    s.dots(idx, total)
    s.text((80, 1022), "BIG BOLÃO", font(16, "bold"), TXT2, anchor="lm")
    s.text((W - 80, 1022), "Copa 2026", font(16, "reg"), TXT2, anchor="rm")


# ==========================================================================
# SLIDES
# ==========================================================================
def trophy(s: Slide, cx, cy, scale=1.0, color=GOLD):
    def P(pts):
        return [(_s(cx + dx * scale), _s(cy + dy * scale)) for dx, dy in pts]
    # cup
    s.d.polygon(P([(-46, -60), (46, -60), (38, 6), (-38, 6)]), fill=color)
    # handles
    s.d.arc(_b([cx - 78 * scale, cy - 58 * scale, cx - 30 * scale, cy + 4 * scale]),
            70, 290, fill=color, width=_s(10 * scale))
    s.d.arc(_b([cx + 30 * scale, cy - 58 * scale, cx + 78 * scale, cy + 4 * scale]),
            250, 110, fill=color, width=_s(10 * scale))
    # stem + base
    s.rrect([cx - 10 * scale, cy + 6 * scale, cx + 10 * scale, cy + 40 * scale], 4 * scale, fill=color)
    s.rrect([cx - 40 * scale, cy + 40 * scale, cx + 40 * scale, cy + 56 * scale], 6 * scale, fill=color)
    s.text((cx, cy - 26 * scale), "★", font(int(34 * scale), "bold"), BG_DEEP, anchor="mm")


def s01():
    s = Slide()
    trophy(s, W / 2, 300, scale=2.2)
    s.text((W / 2, 470), "BIG BOLÃO", font(78, "bold"), TXT, anchor="mm")
    s.text((W / 2, 548), "Copa do Mundo 2026", font(34, "reg"), GOLD, anchor="mm")
    s.rrect([260, 612, W - 260, 700], 44, fill=(255, 255, 255, 8),
            outline=(247, 201, 72, 90), width=2)
    s.text((W / 2, 656), "Guia rápido pra participar", font(28, "bold"), TXT, anchor="mm")
    s.paragraph((150, 760),
                "Palpite no privado do bot. Acompanhe o ranking no site. "
                "Em 2 minutos você está jogando.",
                font(26, "reg"), TXT3, 780, 40, anchor="la")
    # center that paragraph
    s.text((W / 2, 905), "arraste para o lado  →", font(24, "bold"), GREEN, anchor="mm")
    s.dots(0, 12)
    s.text((W / 2, 1022), "@BigBolão", font(16, "bold"), TXT2, anchor="mm")
    s.save("01-capa.png")


def s02():
    s = Slide()
    header(s, "BOT DO TELEGRAM", TG, 1,
           "Abra o bot e toque /start",
           "No privado do bot. Ele te cadastra e mostra a ajuda. "
           "Seus palpites ficam só seus — ninguém no grupo vê.", idx=1)
    box = [180, 470, 900, 952]
    inner = s.screen_card(box)
    # chat header
    s.ellipse([inner[0], inner[1], inner[0] + 56, inner[1] + 56], fill=TG)
    s.text((inner[0] + 28, inner[1] + 28), "B", font(26, "bold"), "#FFFFFF", anchor="mm")
    s.text((inner[0] + 72, inner[1] + 18), "Big Bolão Bot", font(22, "bold"), TXT, anchor="lm")
    s.text((inner[0] + 72, inner[1] + 44), "bot", font(16, "reg"), GREEN, anchor="lm")
    s.line([inner[0], inner[1] + 74, inner[2], inner[1] + 74], (255, 255, 255, 22), 2)
    y = inner[1] + 96
    bubble(s, inner[2] - 200, y, 200, "/start", out=True, sub="você")
    y += 16
    bubble(s, inner[0], y + 70, 480,
           "Bem-vindo ao Big Bolão! Eu registro seus palpites de placar exato. "
           "Use /jogos pra começar.")
    s.save("02-start.png")


def s03():
    s = Slide()
    header(s, "BOT DO TELEGRAM", TG, 2,
           "Já jogou? Mande /sou Nome",
           "Quem participou da Rodada 1 herda os pontos. Digite /sou e seu nome "
           "exatamente como está na planilha.", idx=2)
    box = [180, 470, 900, 952]
    inner = s.screen_card(box)
    y = inner[1] + 16
    bubble(s, inner[2] - 270, y, 270, "/sou Mari Gallo", out=True, sub="você")
    y += 20
    y = bubble(s, inner[0], y + 84, 500,
               "Pronto, Mari Gallo! Você herdou seus palpites da Rodada 1.")
    y += 18
    s.rrect([inner[0], y, inner[0] + 360, y + 78], 18, fill=BG_CARD,
            outline=(0, 220, 130, 60), width=2)
    s.text((inner[0] + 24, y + 39), "9 pts herdados", font(22, "bold"), GREEN, anchor="lm")
    s.text((inner[0] + 250, y + 39), "5º lugar", font(20, "reg"), TXT3, anchor="lm")
    s.save("03-sou.png")


def s04():
    s = Slide()
    header(s, "BOT DO TELEGRAM", TG, 3,
           "Toque /jogos e palpite",
           "Escolha os gols do mandante e depois do visitante nos botões. "
           "Simples assim.", idx=3)
    box = [180, 462, 900, 958]
    inner = s.screen_card(box)
    y = inner[1] + 10
    bubble(s, inner[2] - 170, y, 170, "/jogos", out=True, sub="você")
    y += 96
    # game card inside bot
    s.rrect([inner[0], y, inner[2], y + 150], 20, fill=BG_CARD)
    s.country(inner[0] + 70, y + 56, "BRA", "#009C3B")
    s.country(inner[2] - 70, y + 56, "HAI", "#00209F")
    s.text((W / 2, y + 50), "×", font(30, "bold"), TXT2, anchor="mm")
    s.text((W / 2, y + 104), "Brasil  ×  Haiti", font(20, "bold"), TXT, anchor="mm")
    s.text((W / 2, y + 132), "hoje 21:30", font(16, "reg"), TXT3, anchor="mm")
    y += 168
    s.text((inner[0] + 4, y), "Gols do Brasil:", font(18, "reg"), TXT3, anchor="lm")
    y += 30
    for i, n in enumerate([0, 1, 2, 3, 4]):
        bx = inner[0] + i * 96
        sel = n == 2
        s.rrect([bx, y, bx + 80, y + 64], 14,
                fill=GREEN if sel else BG_CARD2)
        s.text((bx + 40, y + 32), str(n),
               font(24, "bold"), BG_DEEP if sel else TXT, anchor="mm")
    s.text((inner[2], y + 32), "›", font(40, "bold"), TXT2, anchor="rm")
    s.save("04-jogos.png")


def s05():
    s = Slide()
    header(s, "BOT DO TELEGRAM", TG, 4,
           "Edite até o apito",
           "Mudou de ideia? Use /meus pra ver e alterar seus palpites a "
           "qualquer hora, até o jogo começar.", idx=4)
    box = [180, 470, 900, 952]
    inner = s.screen_card(box)
    y = inner[1] + 10
    bubble(s, inner[2] - 160, y, 160, "/meus", out=True, sub="você")
    y += 92
    rows = [("Brasil × Haiti", "2 × 0", "aberto", GREEN),
            ("Espanha × Ar. Saudita", "1 × 0", "aberto", GREEN),
            ("EUA × Austrália", "2 × 1", "começou", ORANGE)]
    for name, guess, st, col in rows:
        s.rrect([inner[0], y, inner[2], y + 86], 18, fill=BG_CARD)
        s.text((inner[0] + 24, y + 32), name, font(20, "bold"), TXT, anchor="lm")
        s.text((inner[0] + 24, y + 60), "seu palpite", font(15, "reg"), TXT2, anchor="lm")
        s.text((inner[2] - 150, y + 43), guess, font(26, "bold"), GOLD, anchor="mm")
        s.rrect([inner[2] - 96, y + 28, inner[2] - 18, y + 58], 15,
                fill=(0, 0, 0, 0), outline=col, width=2)
        s.text((inner[2] - 57, y + 43), st, font(13, "bold"), col, anchor="mm")
        y += 100
    s.save("05-meus.png")


def s06():
    s = Slide()
    header(s, "PONTUAÇÃO", GOLD, 5,
           "Como você pontua",
           "Cravou o placar exato vale 3. Só o vencedor (ou empate) vale 1. "
           "Errou, zero.", idx=5)
    cards = [("3", "PLACAR EXATO", "palpite 2×0  ·  deu 2×0", GREEN),
             ("1", "VENCEDOR / EMPATE", "palpite 1×0  ·  deu 3×1", BLUE),
             ("0", "ERROU", "palpite 0×2  ·  deu 1×1", RED)]
    y = 506
    for pts, title, ex, col in cards:
        s.rrect([110, y, W - 110, y + 138], 26, fill=BG_CARD,
                outline=(255, 255, 255, 18), width=2)
        s.ellipse([146, y + 28, 146 + 82, y + 28 + 82], fill=col)
        s.text((146 + 41, y + 69), pts, font(46, "bold"), BG_DEEP, anchor="mm")
        s.text((280, y + 48), title, font(28, "bold"), TXT, anchor="lm")
        s.text((280, y + 92), ex, font(21, "reg"), TXT3, anchor="lm")
        s.text((W - 150, y + 69), "pts", font(22, "reg"), col, anchor="mm")
        y += 158
    s.save("06-pontuacao.png")


def s07():
    s = Slide()
    header(s, "SITE", GREEN, 6,
           "Entre pelo link mágico",
           "O bot te manda um link. Toque nele e o site já abre logado — "
           "sem senha, sem cadastro.", idx=6)
    box = [240, 480, 840, 946]
    inner = s.screen_card(box, top=True)
    cx = (inner[0] + inner[2]) / 2
    trophy(s, cx, inner[1] + 120, scale=1.2)
    s.text((cx, inner[1] + 220), "Big Bolão", font(34, "bold"), TXT, anchor="mm")
    s.text((cx, inner[1] + 262), "Copa 2026", font(20, "reg"), GOLD, anchor="mm")
    by = inner[1] + 330
    s.rrect([inner[0] + 30, by, inner[2] - 30, by + 76], 20, fill=TG)
    s.text((cx, by + 38), "Entrar com o Telegram", font(23, "bold"), "#FFFFFF", anchor="mm")
    s.text((cx, by + 122), "toque no link que o bot enviou",
           font(18, "reg"), TXT3, anchor="mm")
    s.save("07-login.png")


def s08():
    s = Slide()
    header(s, "SITE", GREEN, 7,
           "Home: seu resumo",
           "Sua posição, seus pontos e o próximo jogo logo na entrada.", idx=7)
    box = [240, 430, 840, 958]
    inner = s.screen_card(box)
    cx = (inner[0] + inner[2]) / 2
    s.text((inner[0], inner[1] + 8), "Olá, Mari Gallo 👋".replace(" 👋", ""),
           font(24, "bold"), TXT, anchor="lm")
    y = inner[1] + 50
    s.rrect([inner[0], y, inner[2], y + 130], 22, fill=BG_CARD,
            outline=(247, 201, 72, 50), width=2)
    for i, (val, lab, col) in enumerate([("5º", "posição", GOLD),
                                         ("9", "pontos", GREEN),
                                         ("1", "exatos", BLUE)]):
        bx = inner[0] + 40 + i * ((inner[2] - inner[0] - 80) / 2)
        s.text((bx, y + 52), val, font(40, "bold"), col, anchor="mm")
        s.text((bx, y + 96), lab, font(17, "reg"), TXT3, anchor="mm")
    y += 152
    s.text((inner[0], y), "PRÓXIMO JOGO", font(15, "bold"), TXT2, anchor="lm")
    y += 28
    s.rrect([inner[0], y, inner[2], y + 120], 20, fill=BG_CARD)
    s.country(inner[0] + 70, y + 60, "BRA", "#009C3B", r=28)
    s.country(inner[2] - 70, y + 60, "HAI", "#00209F", r=28)
    s.text((cx, y + 46), "×", font(28, "bold"), TXT2, anchor="mm")
    s.text((cx, y + 92), "hoje · 21:30", font(18, "reg"), TXT3, anchor="mm")
    y += 140
    s.rrect([inner[0], y, inner[2], y + 70], 18, fill=(0, 220, 130, 28),
            outline=(0, 220, 130, 80), width=2)
    s.text((cx, y + 35), "Palpitar agora →", font(22, "bold"), GREEN, anchor="mm")
    s.save("08-home.png")


def s09():
    s = Slide()
    header(s, "SITE", GREEN, 8,
           "Jogos: filtre e palpite",
           "Veja abertos, seus palpites ou finalizados. Toque num jogo aberto "
           "pra cravar o placar.", idx=8)
    box = [240, 462, 840, 958]
    inner = s.screen_card(box)
    cx = (inner[0] + inner[2]) / 2
    chips = [("Abertos", True), ("Meus", False), ("Final.", False)]
    x = inner[0]
    for lab, on in chips:
        f = font(18, "bold")
        w = s.tlen(lab, f) + 44
        s.rrect([x, inner[1], x + w, inner[1] + 50], 25,
                fill=GREEN if on else BG_CARD2)
        s.text((x + w / 2, inner[1] + 25), lab, f, BG_DEEP if on else TXT3, anchor="mm")
        x += w + 16
    y = inner[1] + 74
    games = [("BRA", "#009C3B", "HAI", "#00209F", "hoje 21:30", "aberto", GREEN),
             ("ESP", "#C60B1E", "ARA", "#006C35", "amanhã 13:00", "aberto", GREEN),
             ("FRA", "#0055A4", "IRQ", "#007A3D", "amanhã 18:00", "aberto", GREEN)]
    for a, ca, bcode, cb, when, st, col in games:
        s.rrect([inner[0], y, inner[2], y + 116], 20, fill=BG_CARD)
        s.country(inner[0] + 58, y + 46, a, ca, r=26)
        s.country(inner[0] + 130, y + 46, bcode, cb, r=26)
        s.text((inner[0] + 180, y + 40), "Jogo aberto", font(19, "bold"), TXT, anchor="lm")
        s.text((inner[0] + 180, y + 70), when, font(16, "reg"), TXT3, anchor="lm")
        s.rrect([inner[2] - 140, y + 30, inner[2] - 24, y + 86], 16,
                fill=(0, 220, 130, 28), outline=col, width=2)
        s.text((inner[2] - 82, y + 58), "palpitar", font(15, "bold"), col, anchor="mm")
        y += 132
    s.save("09-jogos-site.png")


def s10():
    s = Slide()
    header(s, "SITE", GREEN, 9,
           "Ranking: o pódio",
           "Classificação geral, recalculada a cada resultado. Você aparece "
           "destacado na lista.", idx=9)
    box = [240, 452, 840, 958]
    inner = s.screen_card(box)
    cx = (inner[0] + inner[2]) / 2
    # podium
    pod = [("Pajé", "12", 150, "#C0C0C0"), ("Ricardo", "15", 200, GOLD),
           ("Big", "11", 120, "#CD7F32")]
    base = inner[1] + 250
    bw = 150
    xs = [cx - bw - 16, cx, cx + bw + 16]
    order = [0, 1, 2]
    for i in order:
        name, pts, hgt, col = pod[i]
        x = xs[i]
        s.country(x, base - hgt - 40, name[:3].upper(), col, r=34)
        s.rrect([x - bw / 2, base - hgt, x + bw / 2, base], 14, fill=BG_CARD,
                outline=(255, 255, 255, 22), width=2)
        place = {0: "2º", 1: "1º", 2: "3º"}[i]
        s.text((x, base - hgt + 34), place, font(26, "bold"), col, anchor="mm")
        s.text((x, base - hgt + 74), pts + " pts", font(20, "bold"), TXT, anchor="mm")
        s.text((x, base - hgt - 4 + 4 - 0), "", font(14), TXT)
        s.text((x, base + 22), name, font(18, "reg"), TXT3, anchor="mm")
    # your row
    yy = base + 70
    s.rrect([inner[0], yy, inner[2], yy + 70], 18, fill=(0, 220, 130, 22),
            outline=(0, 220, 130, 80), width=2)
    s.text((inner[0] + 28, yy + 35), "5º", font(22, "bold"), GOLD, anchor="lm")
    s.text((inner[0] + 92, yy + 35), "Mari Gallo (você)", font(20, "bold"), TXT, anchor="lm")
    s.text((inner[2] - 28, yy + 35), "9 pts", font(22, "bold"), GREEN, anchor="rm")
    s.save("10-ranking.png")


def s11():
    s = Slide()
    header(s, "SITE", GREEN, 10,
           "Meus Palpites",
           "Tudo num lugar só, agrupado por status: abertos pra editar, "
           "aguardando resultado e finalizados.", idx=10)
    box = [240, 470, 840, 952]
    inner = s.screen_card(box)
    groups = [("ABERTOS PRA EDITAR", GREEN, [("Brasil × Haiti", "2 × 0")]),
              ("AGUARDANDO RESULTADO", ORANGE, [("EUA × Austrália", "2 × 1")]),
              ("FINALIZADOS", TXT2, [("Espanha × Cabo Verde", "+1"),
                                     ("Brasil × Marrocos", "+3")])]
    y = inner[1] + 6
    for title, col, rows in groups:
        s.text((inner[0], y), title, font(15, "bold"), col, anchor="lm")
        y += 30
        for name, val in rows:
            s.rrect([inner[0], y, inner[2], y + 64], 16, fill=BG_CARD)
            s.text((inner[0] + 22, y + 32), name, font(19, "bold"), TXT, anchor="lm")
            vcol = GREEN if val.startswith("+3") else (BLUE if val.startswith("+1") else GOLD)
            s.text((inner[2] - 22, y + 32), val, font(22, "bold"), vcol, anchor="rm")
            y += 76
        y += 12
    s.save("11-meus-palpites.png")


def s12():
    s = Slide()
    trophy(s, W / 2, 250, scale=1.7)
    s.text((W / 2, 392), "Bora palpitar!", font(60, "bold"), TXT, anchor="mm")
    s.paragraph((140, 470),
                "", font(24), TXT3, 800, 36)
    s.text((W / 2, 470), "Você já sabe tudo que precisa.", font(26, "reg"), TXT3, anchor="mm")
    # two recap cards
    cards = [("BOT DO TELEGRAM", TG, "Palpite no privado", "/start · /sou · /jogos"),
             ("SITE", GREEN, "Acompanhe o ranking", "login mágico · pódio")]
    y = 556
    for tagl, col, t, sub in cards:
        s.rrect([130, y, W - 130, y + 132], 24, fill=BG_CARD,
                outline=(255, 255, 255, 18), width=2)
        s.text((170, y + 38), tagl, font(17, "bold"), col, anchor="lm")
        s.text((170, y + 76), t, font(26, "bold"), TXT, anchor="lm")
        s.text((170, y + 110), sub, font(18, "reg"), TXT3, anchor="lm")
        s.ellipse([W - 200, y + 44, W - 156, y + 88], fill=col)
        s.text((W - 178, y + 67), "✓", font(26, "bold"), BG_DEEP, anchor="mm")
        y += 150
    s.rrect([200, 880, W - 200, 956], 38, fill=(0, 220, 130, 26),
            outline=(0, 220, 130, 90), width=2)
    s.text((W / 2, 918), "Dúvidas? Chama no grupo 🏆".replace(" 🏆", ""),
           font(24, "bold"), GREEN, anchor="mm")
    s.dots(11, 12)
    s.text((W / 2, 1022), "@BigBolão", font(16, "bold"), TXT2, anchor="mm")
    s.save("12-cta.png")


def contact_sheet():
    files = sorted(f for f in os.listdir(OUT) if f.endswith(".png"))
    cols, thumb, gap = 4, 250, 16
    rows = math.ceil(len(files) / cols)
    cw = cols * thumb + (cols + 1) * gap
    ch = rows * thumb + (rows + 1) * gap
    sheet = Image.new("RGB", (cw, ch), "#02060D")
    for i, fn in enumerate(files):
        im = Image.open(os.path.join(OUT, fn)).resize((thumb, thumb), Image.LANCZOS)
        r, c = divmod(i, cols)
        sheet.paste(im, (gap + c * (thumb + gap), gap + r * (thumb + gap)))
    sheet.save(os.path.join(os.path.dirname(__file__), "_contact_sheet.png"))


if __name__ == "__main__":
    for fn in (s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12):
        fn()
        print("ok", fn.__name__)
    contact_sheet()
    print("done ->", OUT)
