import pygame
import sys
import time
import json
import os

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Molecule Clicker")

# Шрифты
try:
    FONT = pygame.font.Font(None, 24)
    TITLE_FONT = pygame.font.Font(None, 36)
except:
    FONT = pygame.font.SysFont("TimesNewRoman", 24)
    TITLE_FONT = pygame.font.SysFont("TimesNewRoman", 36, bold=True)

# Цвета
WHITE = (255, 255, 255)
DARK_BLUE = (20, 20, 40)
LIGHT_BLUE = (70, 130, 180)
GREEN = (46, 196, 182)
YELLOW = (255, 204, 0)
MENU_BG = (30, 30, 50, 180)
FRAME_COLOR = (100, 100, 200)
HIGHLIGHT = (255, 255, 100)
ERROR_COLOR = (255, 100, 100)
SLIDER_BG = (100, 100, 100)  # Цвет фона слайдера
SLIDER_FILL = (70, 130, 180)  # Цвет заполненной части слайдера

# Переменные игры
energy = 0
click_power = 1
auto_energy = 0
last_time = time.time()
notification_text = ""
notification_timer = 0
not_enough_text = ""
not_enough_timer = 0
show_pause_menu = False
volume = 0.5  # Начальная громкость (0.0 - 1.0)
dragging_slider = False  # Флаг для перетаскивания слайдера
SAVE_FILE = "save.json"  # Файл для сохранения прогресса

# Пути к ресурсам
ASSET_PATH = "assets/"

# Загрузка изображений
try:
    background = pygame.image.load(f"{ASSET_PATH}background_lab.png").convert()
    background = pygame.transform.scale(background, (WIDTH - 350, HEIGHT))
    h2o_icon = pygame.image.load(f"{ASSET_PATH}h2o.png").convert_alpha()
    enzyme_icon = pygame.image.load(f"{ASSET_PATH}enzyme.png").convert_alpha()
    reactor_icon = pygame.image.load(f"{ASSET_PATH}reactor.png").convert_alpha()
    catalyst_icon = pygame.image.load(f"{ASSET_PATH}catalyst.png").convert_alpha()
    superclick_icon = pygame.image.load(f"{ASSET_PATH}superclick.png").convert_alpha()
except Exception as e:
    print(f"Ошибка загрузки изображений: {e}")
    background = pygame.Surface((WIDTH - 350, HEIGHT)).convert()
    background.fill(DARK_BLUE)
    h2o_icon = enzyme_icon = reactor_icon = catalyst_icon = superclick_icon = None

# Загрузка звуков
try:
    click_sound = pygame.mixer.Sound(f"{ASSET_PATH}click.wav")
    buy_sound = pygame.mixer.Sound(f"{ASSET_PATH}buy.wav")
    not_enough_sound = pygame.mixer.Sound(f"{ASSET_PATH}not_enough.wav")
    pygame.mixer.music.load(f"{ASSET_PATH}music.mp3")
    pygame.mixer.music.set_volume(volume)  # Устанавливаем начальную громкость
    pygame.mixer.music.play(-1)
except Exception as e:
    print(f"Ошибка загрузки звука: {e}")

# Кнопки
button_width, button_height = 250, 120
button_x = WIDTH - button_width - 50
button_y = 50
button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

pause_button_rect = pygame.Rect(WIDTH - 120, HEIGHT - 60, 100, 40)  # Правый нижний угол

# Улучшения
upgrades = [
    {
        "name": "Катализатор",
        "icon": catalyst_icon,
        "description": "+1 к клику",
        "price": 50,
        "multiplier": 1.2,
        "level": 0,
        "y_pos": 160,
        "effect": lambda: increase_click_power(1),
    },
    {
        "name": "Фермент",
        "icon": enzyme_icon,
        "description": "+1/с",
        "price": 100,
        "multiplier": 1.2,
        "level": 0,
        "y_pos": 240,
        "effect": lambda: increase_auto_energy(1),
    },
    {
        "name": "Реактор",
        "icon": reactor_icon,
        "description": "+5/с",
        "price": 500,
        "multiplier": 1.2,
        "level": 0,
        "y_pos": 320,
        "effect": lambda: increase_auto_energy(5),
    },
    {
        "name": "Сверхклик",
        "icon": superclick_icon,
        "description": "x2 к клику",
        "price": 1000,
        "multiplier": 1.5,
        "level": 0,
        "y_pos": 400,
        "effect": lambda: increase_click_power(click_power),
    },
]

def draw_button(rect, text, icon=None, color=GREEN, hover_color=(0, 255, 200)):
    hovering = rect.collidepoint(pygame.mouse.get_pos())
    color_to_draw = hover_color if hovering else color

    pygame.draw.rect(screen, color_to_draw, rect, border_radius=15)

    if icon:
        icon_rect = icon.get_rect(center=(rect.x + 50, rect.centery))
        screen.blit(icon, icon_rect)
        label = TITLE_FONT.render(text, True, WHITE)
        text_rect = label.get_rect(midleft=(icon_rect.right + 15, rect.centery))
    else:
        label = TITLE_FONT.render(text, True, WHITE)
        text_rect = label.get_rect(center=rect.center)

    screen.blit(label, text_rect)

def draw_pause_button():
    hovering = pause_button_rect.collidepoint(pygame.mouse.get_pos())
    color = HIGHLIGHT if hovering else LIGHT_BLUE
    pygame.draw.rect(screen, color, pause_button_rect, border_radius=10)
    label = FONT.render("Пауза", True, WHITE)
    text_rect = label.get_rect(center=pause_button_rect.center)
    screen.blit(label, text_rect)

def draw_pause_menu():
    global volume  # Объявляем, что будем изменять глобальную переменную
    
    menu_w, menu_h = 500, 400
    menu_x = WIDTH // 2 - menu_w // 2
    menu_y = HEIGHT // 2 - menu_h // 2
    menu_rect = pygame.Rect(menu_x, menu_y, menu_w, menu_h)

    # Фон меню
    pause_surface = pygame.Surface((menu_w, menu_h), pygame.SRCALPHA)
    pause_surface.fill((50, 50, 50, 200))
    screen.blit(pause_surface, (menu_x, menu_y))
    pygame.draw.rect(screen, FRAME_COLOR, menu_rect, width=3, border_radius=15)

    # Заголовок
    title = TITLE_FONT.render("Купленные улучшения", True, WHITE)
    screen.blit(title, (menu_x + 20, menu_y + 20))

    # Список улучшений
    y = menu_y + 70
    for upg in upgrades:
        if upg["level"] > 0:
            if upg["icon"]:
                icon_rect = upg["icon"].get_rect(topleft=(menu_x + 30, y))
                screen.blit(upg["icon"], icon_rect)
            name_label = FONT.render(f"{upg['name']} (x{upg['level']})", True, WHITE)
            screen.blit(name_label, (menu_x + 70, y + 5))
            y += 50

    # Слайдер громкости
    slider_x = menu_x + 30
    slider_y = menu_y + menu_h - 100
    slider_w = 400
    slider_h = 10
    slider_rect = pygame.Rect(slider_x, slider_y, slider_w, slider_h)
    
    # Рисуем фон слайдера
    pygame.draw.rect(screen, SLIDER_BG, slider_rect, border_radius=5)
    
    # Рисуем заполненную часть слайдера
    fill_width = int(slider_w * volume)
    fill_rect = pygame.Rect(slider_x, slider_y, fill_width, slider_h)
    pygame.draw.rect(screen, SLIDER_FILL, fill_rect, border_radius=5)
    
    # Текст с текущей громкостью
    vol_text = FONT.render(f"Громкость: {int(volume * 100)}%", True, WHITE)
    screen.blit(vol_text, (slider_x, slider_y - 25))

    # Кнопки
    button_y = menu_y + menu_h - 40
    close_rect = pygame.Rect(menu_x + menu_w - 100, button_y, 80, 30)
    save_rect = pygame.Rect(menu_x + 20, button_y, 120, 30)
    reset_rect = pygame.Rect(menu_x + 160, button_y, 120, 30)

    # Кнопка закрыть
    if close_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(screen, YELLOW, close_rect, border_radius=10)
    else:
        pygame.draw.rect(screen, LIGHT_BLUE, close_rect, border_radius=10)
    close_label = FONT.render("Закрыть", True, WHITE)
    close_text_rect = close_label.get_rect(center=close_rect.center)
    screen.blit(close_label, close_text_rect)

    # Кнопка сохранить
    if save_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(screen, GREEN, save_rect, border_radius=10)
    else:
        pygame.draw.rect(screen, LIGHT_BLUE, save_rect, border_radius=10)
    save_label = FONT.render("Сохранить", True, WHITE)
    save_text_rect = save_label.get_rect(center=save_rect.center)
    screen.blit(save_label, save_text_rect)

    # Кнопка сбросить
    if reset_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(screen, ERROR_COLOR, reset_rect, border_radius=10)
    else:
        pygame.draw.rect(screen, LIGHT_BLUE, reset_rect, border_radius=10)
    reset_label = FONT.render("Сбросить", True, WHITE)
    reset_text_rect = reset_label.get_rect(center=reset_rect.center)
    screen.blit(reset_label, reset_text_rect)

    return close_rect, save_rect, reset_rect, slider_rect

def draw_menu_frame():
    menu_surface = pygame.Surface((350, HEIGHT), pygame.SRCALPHA)
    menu_surface.fill(MENU_BG)
    screen.blit(menu_surface, (0, 0))
    pygame.draw.rect(screen, FRAME_COLOR, pygame.Rect(0, 0, 350, HEIGHT), width=3)

def draw_stats(x, y):
    stats = [
        f"Энергия: {int(energy)}",
        f"Очки за клик: {click_power}",
        f"Автопроизводство: {auto_energy:.1f}/с"
    ]
    for i, line in enumerate(stats):
        label = FONT.render(line, True, WHITE)
        screen.blit(label, (x, y + i * 30))

def check_upgrade_click(pos):
    global energy, notification_text, notification_timer, not_enough_timer
    x, y = pos
    if x > 350:
        return
    for upg in upgrades:
        if upg["y_pos"] <= y <= upg["y_pos"] + 60:
            if energy >= upg["price"]:
                energy -= upg["price"]
                upg["price"] *= upg["multiplier"]
                upg["level"] += 1
                upg["effect"]()
                notification_text = f"Куплено: {upg['name']}!"
                notification_timer = 2.0
                try:
                    buy_sound.play()
                except:
                    pass
                return
            else:
                not_enough_timer = 2.0
                try:
                    not_enough_sound.play()
                except:
                    pass
                return

def draw_upgrades():
    for upg in upgrades:
        if upg["icon"] is not None:
            icon_rect = upg["icon"].get_rect(topleft=(40, upg["y_pos"]))
            screen.blit(upg["icon"], icon_rect)
        name_label = FONT.render(upg["name"], True, WHITE)
        desc_label = FONT.render(upg["description"], True, LIGHT_BLUE)
        price_label = FONT.render(f"Цена: {int(upg['price'])}", True, YELLOW)

        upgrade_rect = pygame.Rect(40, upg["y_pos"], 300, 60)
        if upgrade_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(screen, HIGHLIGHT, upgrade_rect, width=3, border_radius=10)

        screen.blit(name_label, (80, upg["y_pos"] + 5))
        screen.blit(desc_label, (80, upg["y_pos"] + 25))
        screen.blit(price_label, (80, upg["y_pos"] + 45))

def draw_notification():
    global notification_timer, not_enough_timer
    if notification_timer > 0:
        notif = FONT.render(notification_text, True, YELLOW)
        screen.blit(notif, (WIDTH // 2 - notif.get_width() // 2, HEIGHT - 50))
        notification_timer -= 0.1
    if not_enough_timer > 0:
        notif = FONT.render("Недостаточно энергии!", True, ERROR_COLOR)
        screen.blit(notif, (WIDTH // 2 - notif.get_width() // 2, HEIGHT - 80))
        not_enough_timer -= 0.1

# Функции для улучшений
def increase_click_power(amount):
    global click_power
    click_power += amount

def increase_auto_energy(amount):
    global auto_energy
    auto_energy += amount

# Функции сохранения и загрузки
def save_game():
    save_data = {
        "energy": energy,
        "click_power": click_power,
        "auto_energy": auto_energy,
        "volume": volume,
        "upgrades": []
    }
    
    for upg in upgrades:
        save_data["upgrades"].append({
            "name": upg["name"],
            "price": upg["price"],
            "level": upg["level"]
        })
    
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(save_data, f)
        return True
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False

def load_game():
    global energy, click_power, auto_energy, volume
    
    if not os.path.exists(SAVE_FILE):
        return False
    
    try:
        with open(SAVE_FILE, "r") as f:
            save_data = json.load(f)
        
        energy = save_data.get("energy", 0)
        click_power = save_data.get("click_power", 1)
        auto_energy = save_data.get("auto_energy", 0)
        volume = save_data.get("volume", 0.5)
        pygame.mixer.music.set_volume(volume)
        
        loaded_upgrades = save_data.get("upgrades", [])
        for i, upg_data in enumerate(loaded_upgrades):
            if i < len(upgrades):
                upgrades[i]["price"] = upg_data.get("price", upgrades[i]["price"])
                upgrades[i]["level"] = upg_data.get("level", 0)
                
                # Применяем эффекты купленных улучшений
                if upgrades[i]["level"] > 0:
                    for _ in range(upgrades[i]["level"]):
                        upgrades[i]["effect"]()
        
        return True
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return False

def reset_game():
    global energy, click_power, auto_energy, volume
    
    energy = 0
    click_power = 1
    auto_energy = 0
    volume = 0.5
    pygame.mixer.music.set_volume(volume)
    
    for upg in upgrades:
        upg["price"] = upg.get("base_price", upg["price"])  # Возвращаем начальную цену
        upg["level"] = 0
    
    # Удаляем файл сохранения, если он существует
    if os.path.exists(SAVE_FILE):
        try:
            os.remove(SAVE_FILE)
        except:
            pass

# Загружаем сохранение при старте
load_game()

# Основной цикл
running = True
while running:
    dt = time.time() - last_time
    last_time = time.time()

    energy += auto_energy * dt

    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if button_rect.collidepoint(event.pos):
                energy += click_power
                try:
                    click_sound.play()
                except:
                    pass

            elif pause_button_rect.collidepoint(event.pos):
                show_pause_menu = not show_pause_menu

            elif show_pause_menu:
                close_rect, save_rect, reset_rect, slider_rect = draw_pause_menu()
                if close_rect.collidepoint(event.pos):
                    show_pause_menu = False
                elif save_rect.collidepoint(event.pos):
                    if save_game():
                        notification_text = "Игра сохранена!"
                        notification_timer = 2.0
                elif reset_rect.collidepoint(event.pos):
                    reset_game()
                    notification_text = "Прогресс сброшен!"
                    notification_timer = 2.0
                elif slider_rect.collidepoint(event.pos):
                    dragging_slider = True
                    # Обновляем громкость при клике на слайдер
                    mouse_x = event.pos[0]
                    new_volume = (mouse_x - slider_rect.x) / slider_rect.width
                    volume = max(0.0, min(1.0, new_volume))
                    pygame.mixer.music.set_volume(volume)

            elif not show_pause_menu and event.pos[0] < 350:
                check_upgrade_click(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            dragging_slider = False

        elif event.type == pygame.MOUSEMOTION:
            if dragging_slider and show_pause_menu:
                # Обновляем громкость при перетаскивании слайдера
                mouse_x = event.pos[0]
                slider_rect = pygame.Rect(WIDTH // 2 - 250 + 30, HEIGHT // 2 + 100, 400, 10)
                new_volume = (mouse_x - slider_rect.x) / slider_rect.width
                volume = max(0.0, min(1.0, new_volume))
                pygame.mixer.music.set_volume(volume)

    # Рисование
    screen.blit(background, (350, 0))
    draw_menu_frame()
    draw_stats(20, 50)
    draw_upgrades()
    draw_button(button_rect, "CLICK!", h2o_icon)
    draw_pause_button()

    if show_pause_menu:
        draw_pause_menu()

    draw_notification()

    # Обновление экрана
    pygame.display.flip()
    pygame.time.Clock().tick(60)

# Сохраняем игру при выходе
save_game()
pygame.quit()
sys.exit()