"""Banner: planeta ASCII girando + nome. Gera GIF em loop perfeito."""
import math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
W, H = 900, 420
FRAMES = 72                       # 5°/quadro → volta completa e loop sem emenda
MS = 70
F = "/usr/share/fonts/truetype/dejavu/"
mono = ImageFont.truetype(F + "DejaVuSansMono.ttf", 11)
monob = ImageFont.truetype(F + "DejaVuSansMono-Bold.ttf", 11)
name_font = ImageFont.truetype(F + "DejaVuSansCondensed-Bold.ttf", 52)
small = ImageFont.truetype(F + "DejaVuSansMono.ttf", 14)
smallb = ImageFont.truetype(F + "DejaVuSansMono-Bold.ttf", 15)

BG = (6, 19, 27)
CW = mono.getlength("M")          # largura de um caractere
CH = 12                           # altura da linha
R = 168                           # raio do planeta em px
CX, CY = 670, 212                 # centro do planeta

rng = np.random.default_rng(7)
# continentes: soma de ondas 3D aleatórias (sem emenda na esfera)
K = rng.normal(0, 1, (14, 3)); K /= np.linalg.norm(K, axis=1, keepdims=True)
freq = rng.uniform(2.0, 5.0, 14); amp = 1 / freq; phase = rng.uniform(0, 2 * np.pi, 14)
def field(p):  # p: (..., 3)
    return sum(amp[i] * np.sin(freq[i] * (p @ K[i]) + phase[i]) for i in range(len(K)))
# calibra o limiar para ~38% de terra
samp = rng.normal(0, 1, (20000, 3)); samp /= np.linalg.norm(samp, axis=1, keepdims=True)
LAND_T = np.quantile(field(samp), 0.56)

# nós de rede: pontos sobre a terra
cand = rng.normal(0, 1, (4000, 3)); cand /= np.linalg.norm(cand, axis=1, keepdims=True)
cand = cand[field(cand) > LAND_T + 0.05]
NODES = cand[rng.choice(len(cand), 9, replace=False)]
NODE_PHASE = rng.integers(0, FRAMES, len(NODES))

TILT = math.radians(18)
LIGHT = np.array([-0.55, -0.45, 0.70]); LIGHT /= np.linalg.norm(LIGHT)
RAMP = " .:-=+*#%@"
LAND_RAMP = "=+*#%@@"
SEA_RAMP = " .,:;~~"

# grade de caracteres que cobre o planeta (+ atmosfera)
cols = int(2 * (R + 14) / CW) + 1; rows = int(2 * (R + 14) / CH) + 1
gx = (np.arange(cols) - cols / 2 + 0.5) * CW / R
gy = (np.arange(rows) - rows / 2 + 0.5) * CH / R
X, Y = np.meshgrid(gx, gy)
D2 = X ** 2 + Y ** 2
INSIDE = D2 <= 1.0
Z = np.sqrt(np.clip(1 - D2, 0, 1))
N = np.stack([X, Y, Z], -1)                       # normal = ponto na esfera (tela)
SHADE = np.clip(N @ LIGHT, 0, 1)

def to_body(p, theta):
    """tela → coordenadas do planeta: desfaz inclinação e rotação."""
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    # desfaz inclinação (em torno de x)
    y1 = y * math.cos(TILT) + z * math.sin(TILT); z1 = -y * math.sin(TILT) + z * math.cos(TILT)
    # desfaz rotação (em torno de y)
    x2 = x * math.cos(theta) - z1 * math.sin(theta); z2 = x * math.sin(theta) + z1 * math.cos(theta)
    return np.stack([x2, y1, z2], -1)

def to_screen(q, theta):
    x, y, z = q[..., 0], q[..., 1], q[..., 2]
    x1 = x * math.cos(theta) + z * math.sin(theta); z1 = -x * math.sin(theta) + z * math.cos(theta)
    y2 = y * math.cos(TILT) - z1 * math.sin(TILT); z2 = y * math.sin(TILT) + z1 * math.cos(TILT)
    return np.stack([x1, y2, z2], -1)

def lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

LAND_DARK, LAND_LIT = (10, 95, 70), (167, 243, 208)
SEA_DARK, SEA_LIT = (10, 55, 85), (56, 189, 248)

def static_layer():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    for x in range(0, W, 30): d.line([(x, 0), (x, H)], fill=(12, 34, 46))
    for y in range(0, H, 30): d.line([(0, y), (W, y)], fill=(12, 34, 46))
    d.rectangle([12, 12, W - 13, H - 13], outline=(16, 92, 74))
    d.text((34, 40), "luis@l0-noc:~$ ./planeta.sh", font=small, fill=(100, 116, 139))
    d.text((34, 92), "LUIS O.", font=name_font, fill=(248, 250, 252))
    d.text((34, 150), "FLORENCIO", font=name_font, fill=(248, 250, 252))
    w = d.textlength("FLORENCIO", font=name_font)
    d.text((34 + w + 2, 150), ".", font=name_font, fill=(16, 185, 129))
    d.text((36, 232), "> ANALISTA DE INFRAESTRUTURA DE TI", font=smallb, fill=(110, 231, 183))
    d.text((36, 262), "Linux · Windows Server · AD · Redes", font=small, fill=(203, 213, 225))
    d.text((36, 284), "Automação · IA local", font=small, fill=(203, 213, 225))
    d.text((36, 350), "lteodoro780.github.io", font=small, fill=(148, 163, 184))
    return im

BASE = static_layer()
frames = []
for f in range(FRAMES):
    theta = 2 * math.pi * f / FRAMES
    im = BASE.copy(); d = ImageDraw.Draw(im)
    P = to_body(N, theta)
    land = field(P) > LAND_T
    for r in range(rows):
        for c in range(cols):
            px = CX + (c - cols / 2 + 0.5) * CW - CW / 2
            py = CY + (r - rows / 2 + 0.5) * CH - CH / 2
            if INSIDE[r, c]:
                s = SHADE[r, c]
                g = s ** 0.75
                if land[r, c]:
                    ch = LAND_RAMP[min(len(LAND_RAMP) - 1, int(g * len(LAND_RAMP)))]
                    col = lerp(LAND_DARK, LAND_LIT, g)
                else:
                    ch = SEA_RAMP[min(len(SEA_RAMP) - 1, int(g * len(SEA_RAMP)))]
                    col = lerp(SEA_DARK, SEA_LIT, 0.15 + 0.7 * g)
                if s < 0.04:            # lado noturno: quase apagado
                    ch = "." if land[r, c] else " "
                    col = (12, 52, 48)
                d.text((px, py), ch, font=mono, fill=col)
            elif D2[r, c] <= (1 + 9 / R) ** 2:     # atmosfera fina
                d.text((px, py), "·", font=mono, fill=(14, 116, 144))
    # nós de rede (só no lado visível e iluminado)
    S = to_screen(NODES, theta)
    for i, (x, y, z) in enumerate(S):
        if z <= 0.08: continue
        sx, sy = CX + x * R, CY + y * R
        lit = float(np.clip(np.array([x, y, z]) @ LIGHT, 0, 1))
        on = ((f + NODE_PHASE[i]) % 24) < 14
        col = (245, 158, 11) if on else (120, 80, 10)
        if lit < 0.05: col = (90, 60, 10)
        d.text((sx - CW / 2, sy - CH / 2), "@", font=monob, fill=col)
        if on and lit >= 0.05:
            d.ellipse([sx - 7, sy - 7, sx + 7, sy + 7], outline=(245, 158, 11))
    frames.append(im)

# paleta única para todos os quadros (sem tremulação de cor)
pal_src = Image.new("RGB", (W, H * 3))
for k, idx in enumerate([0, FRAMES // 3, 2 * FRAMES // 3]): pal_src.paste(frames[idx], (0, k * H))
pal = pal_src.quantize(colors=96, method=Image.Quantize.MEDIANCUT)
q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
q[0].save(f"{OUT}/banner-luis.gif", save_all=True, append_images=q[1:], duration=MS, loop=0, optimize=True, disposal=1)
frames[0].save(f"{OUT}/quadro-00.png"); frames[FRAMES // 4].save(f"{OUT}/quadro-18.png")
print("ok", len(frames))
