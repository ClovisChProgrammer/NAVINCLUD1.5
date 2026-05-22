import os
import random
from PIL import Image, ImageDraw, ImageFont

# Paletas de cores baseadas em eixos de confusão reais (CIE Lab)
# As cores de Achroma agora têm contraste cromático real, mas brilho idêntico.
COLOR_PALETTES = {
    "control": {"bg": (70, 80, 70), "num": (255, 50, 50)},    # Super visível
    # Nopia (defeitos completos)
    "protanopia": {"bg": (145, 145, 120), "num": (120, 120, 80)}, # Eixo Vermelho
    "deuteranopia": {"bg": (140, 160, 140), "num": (160, 140, 120)}, # Eixo Verde
    "tritanopia": {"bg": (70, 130, 180), "num": (70, 150, 120)},  # Eixo Azul
    "achromatopsia": {"bg": (130, 130, 130), "num": (100, 150, 100)}, # Verde vs Cinza (Mesma Luminância)
    # Malia (defeitos parciais, delta de cor reduzido)
    "protanomaly": {"bg": (150, 150, 130), "num": (130, 130, 100)},
    "deuteranomaly": {"bg": (150, 165, 150), "num": (165, 150, 130)},
    "tritanomaly": {"bg": (70, 135, 175), "num": (70, 145, 135)},
    "achromatomaly": {"bg": (135, 135, 135), "num": (110, 145, 110)},
}

PLATES_DATA = [
    # 2 placas de controle
    (1, 12, "control"), (2, 73, "control"),
    # Protan (2 protanopia, 2 protanomaly)
    (3, 29, "protanopia"), (4, 45, "protanopia"),
    (5, 6, "protanomaly"), (6, 8, "protanomaly"),
    # Deutan (2 deuteranopia, 2 deuteranomaly)
    (7, 8, "deuteranopia"), (8, 5, "deuteranopia"),
    (9, 2, "deuteranomaly"), (10, 15, "deuteranomaly"),
    # Tritan (2 tritanopia, 2 tritanomaly)
    (11, 6, "tritanopia"), (12, 3, "tritanopia"),
    (13, 26, "tritanomaly"), (14, 42, "tritanomaly"),
    # Achroma (2 achromatopsia, 2 achromatomaly)
    (15, 7, "achromatopsia"), (16, 16, "achromatopsia"),
    (17, 4, "achromatomaly"), (18, 10, "achromatomaly"),
]

def create_ishihara_plate(number, p_type, filename):
    size = 500
    # Fundo branco da imagem
    img = Image.new("RGB", (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Máscara do número
    mask_img = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask_img)
    
    try:
        # Tenta carregar uma fonte negritada para melhorar a visibilidade
        font = ImageFont.truetype("arialbd.ttf", 320)
    except:
        font = ImageFont.load_default()

    # Centralização
    w, h = mask_draw.textbbox((0, 0), str(number), font=font)[2:]
    mask_draw.text(((size-w)/2, (size-h)/2 - 40), str(number), fill=255, font=font)

    palette = COLOR_PALETTES[p_type]
    
    # Gerar 3500 círculos para maior densidade e clareza
    for _ in range(3500):
        x = random.randint(30, 470)
        y = random.randint(30, 470)
        
        # Manter dentro do círculo de Ishihara
        if ((x-250)**2 + (y-250)**2)**0.5 > 210:
            continue
            
        radius = random.randint(2, 9)
        
        # Variância de cor e brilho controlada
        var = random.randint(-15, 15)
        
        if mask_img.getpixel((x, y)) == 255:
            # Cor do Número
            r, g, b = palette["num"]
        else:
            # Cor do Fundo
            r, g, b = palette["bg"]
            
        color = (
            max(0, min(255, r + var)),
            max(0, min(255, g + var)),
            max(0, min(255, b + var))
        )
        
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color)

    img.save(f"images/{filename}", "WEBP", quality=95)

if __name__ == "__main__":
    if not os.path.exists("images"):
        os.makedirs("images")
    print("Gerando placas de alta precisao para NAVINCLUD...")
    for id_p, num, p_type in PLATES_DATA:
        create_ishihara_plate(num, p_type, f"plate{id_p}.webp")
        print(f"[OK] Placa {id_p} ({p_type}) gerada.")
    print("\nPronto! Substitua as imagens na pasta da extensão e teste novamente.")