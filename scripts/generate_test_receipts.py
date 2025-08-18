#!/usr/bin/env python3

from PIL import Image, ImageDraw, ImageFont
import os

def create_receipt(text, filename, width=800, height=1000):
    """Create a test receipt image with the given text"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default system font, fallback to default if not available
    try:
        # Try different font paths for different systems
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Alternative Linux
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 20)
                font_small = ImageFont.truetype(path, 16)
                break
        if not font:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw the text
    y_offset = 30
    for line in text.strip().split('\n'):
        draw.text((50, y_offset), line, fill='black', font=font_small)
        y_offset += 25
    
    # Save the image
    img.save(filename)
    print(f"Created {filename}")

# Create Safeway receipt
safeway_text = """
SAFEWAY
Store #2934
123 Market Street
San Francisco, CA 94103
(415) 555-0123

RECEIPT

Date: 01/18/2025  Time: 16:45

GROCERY
Organic Milk 1 Gal         $6.99
Whole Wheat Bread          $3.49
Bananas 2.5 lb @ $0.69/lb  $1.73
Chicken Breast 1.8 lb      $12.99
Broccoli Crowns            $4.99
Greek Yogurt 32oz          $5.49
Eggs Large Dozen           $4.99

SUBTOTAL                   $40.67
TAX (8.625%)               $3.51
TOTAL                      $44.18

PAYMENT
Visa Card ****1234         $44.18

Thank you for shopping at Safeway!
Member ID: 4081234567
You saved $8.32 today!
"""

# Create Silpo (Ukrainian grocery store) receipt
silpo_text = """
СІЛЬПО
Магазин №142
вул. Хрещатик, 15
м. Київ, 01001
тел: (044) 123-45-67

ФІСКАЛЬНИЙ ЧЕК

Дата: 18.01.2025  Час: 14:23
Касир: Петренко О.В.

ТОВАРИ:
Хліб Український           32.50 грн
Молоко Яготинське 2.5%     42.90 грн
Сир твердий 300г          185.00 грн
Яблука Гала 1.2кг          48.60 грн
Картопля 2.5кг             37.50 грн
Курка охолоджена 1.3кг    156.00 грн
Олія соняшникова 1л        68.90 грн
Цукор 1кг                  42.00 грн
Помідори 0.8кг             64.00 грн

СУМА                      677.40 грн
ПДВ 20%                   112.90 грн

ДО СПЛАТИ                 677.40 грн
ГОТІВКА                   700.00 грн
РЕШТА                      22.60 грн

Дякуємо за покупку!
Картка лояльності: 3801234567
Ваша знижка: 45.80 грн
"""

# Create ATB (another Ukrainian store) receipt
atb_text = """
АТБ-Маркет
Магазин №567
пр. Перемоги, 89
м. Київ, 03115

КАСОВИЙ ЧЕК

18.01.2025  10:15
Каса №3

Борошно пшеничне 2кг       76.80
Масло вершкове 200г        89.90
Яйця курячі 10шт           44.50
Ковбаса варена 400г       124.00
Сметана 15% 400г           56.70
Огірки свіжі 0.6кг         42.00
Макарони 500г              28.90
Гречка 1кг                 68.00

ВСЬОГО:                   530.80
Готівка:                  550.00
Решта:                     19.20

ДЯКУЄМО!
"""

# Generate test images
os.makedirs('test-images', exist_ok=True)
create_receipt(safeway_text, 'test-images/safeway_receipt.png')
create_receipt(silpo_text, 'test-images/silpo_receipt.png', height=1200)
create_receipt(atb_text, 'test-images/atb_receipt.png', height=800)

print("\nTest receipts created successfully!")