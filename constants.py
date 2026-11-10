"""Constantes partagées par tout le jeu."""

GAME_NAME = "Crazy Safari"

# Le jeu est dessiné dans une résolution virtuelle puis mis à l'échelle
# dans la fenêtre (avec des bandes noires si besoin).
VIRTUAL_WIDTH = 1920
VIRTUAL_HEIGHT = 1078

# Bande de savane dessinée au centre du HUD (bg_and_HUD.mp4).
PLAYFIELD_X = 738
PLAYFIELD_Y = 0
PLAYFIELD_WIDTH = 446
PLAYFIELD_HEIGHT = 1078

# Fichiers
HUD_IMAGE = "assets/game/game_hud.png"
MENU_BG_IMAGE = "assets/main_menu/main_menu_bg.png"
MENU_TITLE_IMAGE = "assets/main_menu/crazy_safari.png"
MENU_PLAY_IMAGE = "assets/main_menu/play.png"
MENU_MUSIC = "assets/main_menu/menu_theme.mp3"
PLAYER_IDLE_IMAGE = "assets/characters/player/idle_player.png"
PLAYER_FIRE_IMAGE_1 = "assets/characters/player/player_shootin_1.png"
PLAYER_FIRE_IMAGE_2 = "assets/characters/player/player_shootin_2.png"
PLAYER_BULLET_IMAGE = "assets/characters/player/bullet.png"
HYENA_IMAGE = "assets/characters/hyena/hyena_sprite.png"
HYENA_OST = "assets/characters/hyena/hyana_ost_boss.mp3"
HIGHSCORE_FILE = "highscore.txt"

# Joueur
PLAYER_SPEED = 345.0
PLAYER_FOCUS_SPEED = 165.0
PLAYER_RADIUS = 6
PLAYER_LIVES = 3
PLAYER_BOMBS = 2
PLAYER_INVULNERABLE_TIME = 2.6
PLAYER_FIRE_INTERVAL = 0.10
PLAYER_BULLET_SPEED = 1050.0
PLAYER_BULLET_DAMAGE = 1

# Petites hyènes
MINION_HP = 20
MINION_SPEED = 80.0
MINION_SCORE = 150
MINION_FIRE_INTERVAL_MIN = 1.3
MINION_FIRE_INTERVAL_MAX = 1.9
MINION_BULLET_SPEED = 250.0

# Boss
BOSS_HP = 1000
BOSS_SCORE = 5000
BOSS_BULLET_SPEED = 310.0
BOSS_ENTER_Y = 205

# Déroulement de la manche
STAGE_DURATION = 24.0
FIRST_SPAWN_DELAY = 1.2
SPAWN_INTERVAL_START = 1.35
SPAWN_INTERVAL_MIN = 0.7
BOSS_WARNING_TIME = 2.4
BOSS_INTERMISSION = 2.6
VICTORY_DELAY = 3.0

# Divers
BG_SCROLL_SPEED = 55.0
GRAZE_DISTANCE = 28
GRAZE_SCORE = 10
MAX_PARTICLES = 420

# Couleurs
GOLD = (236, 203, 116)
GOLD_DARK = (146, 118, 62)
CREAM = (245, 237, 216)
MUTED = (170, 160, 140)
WHITE = (255, 255, 255)
RED = (228, 66, 66)
PURPLE = (236, 92, 216)
VIOLET = (178, 116, 255)
DARK = (14, 11, 22)
PANEL_DARK = (10, 8, 18)
