"""Chargement, découpe et mise à l'échelle des assets du jeu."""

import os

import pygame

from constants import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def asset_path(relative_path):
    """Chemin absolu depuis la racine du projet."""
    return os.path.join(BASE_DIR, relative_path)


class Assets:
    """Charge tous les assets une seule fois et garde les versions utiles."""

    def __init__(self):
        self._text_cache = {}
        self._font_cache = {}

        # ------------------------------------------------------------
        # Fond de jeu + HUD (une image extraite de bg_and_HUD.mp4)
        # ------------------------------------------------------------
        hud = pygame.image.load(asset_path(HUD_IMAGE)).convert()
        self.hud = hud.subsurface(
            pygame.Rect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        ).copy()

        self.playfield_bg = self.hud.subsurface(
            pygame.Rect(
                PLAYFIELD_X, PLAYFIELD_Y, PLAYFIELD_WIDTH, PLAYFIELD_HEIGHT
            )
        ).copy()

        # La savane est répétée en miroir pour un défilement sans coupure.
        flipped = pygame.transform.flip(self.playfield_bg, False, True)
        self.bg_tile = pygame.Surface(
            (PLAYFIELD_WIDTH, PLAYFIELD_HEIGHT * 2)
        ).convert()
        self.bg_tile.blit(self.playfield_bg, (0, 0))
        self.bg_tile.blit(flipped, (0, PLAYFIELD_HEIGHT))
        self.bg_tile_height = self.bg_tile.get_height()

        # Voile sombre pour faire ressortir les projectiles sur le sable.
        self.playfield_shade = pygame.Surface(
            (PLAYFIELD_WIDTH, PLAYFIELD_HEIGHT), pygame.SRCALPHA
        )
        self.playfield_shade.fill((8, 6, 16, 46))

        self.playfield_flash = pygame.Surface(
            (PLAYFIELD_WIDTH, PLAYFIELD_HEIGHT), pygame.SRCALPHA
        )
        self.playfield_flash.fill((255, 238, 228, 255))

        # ------------------------------------------------------------
        # Menu
        # ------------------------------------------------------------
        menu_bg = pygame.image.load(asset_path(MENU_BG_IMAGE)).convert()
        self.menu_bg = pygame.transform.smoothscale(
            menu_bg, (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        )
        self.menu_title = self._fit_width(
            self._crop(
                pygame.image.load(asset_path(MENU_TITLE_IMAGE)).convert_alpha()
            ),
            790,
        )
        self.play_button = self._fit_width(
            self._crop(
                pygame.image.load(asset_path(MENU_PLAY_IMAGE)).convert_alpha()
            ),
            425,
        )
        self.play_button_hover = pygame.transform.smoothscale(
            self.play_button,
            (
                int(self.play_button.get_width() * 1.06),
                int(self.play_button.get_height() * 1.06),
            ),
        )
        self.play_glow = self._make_glow(620, 250)
        self.menu_bottom_shade = pygame.Surface(
            (VIRTUAL_WIDTH, 170), pygame.SRCALPHA
        )
        for y in range(self.menu_bottom_shade.get_height()):
            ratio = y / self.menu_bottom_shade.get_height()
            alpha = int(105 * ratio**1.5)
            pygame.draw.line(
                self.menu_bottom_shade,
                (6, 4, 10, alpha),
                (0, y),
                (VIRTUAL_WIDTH, y),
            )

        # ------------------------------------------------------------
        # Personnages
        # ------------------------------------------------------------
        idle = self._crop(
            pygame.image.load(asset_path(PLAYER_IDLE_IMAGE)).convert_alpha()
        )
        fire_1 = self._crop(
            pygame.image.load(asset_path(PLAYER_FIRE_IMAGE_1)).convert_alpha()
        )
        fire_2 = self._crop(
            pygame.image.load(asset_path(PLAYER_FIRE_IMAGE_2)).convert_alpha()
        )
        self.player_frames = [
            self._fit_height(idle, 106),
            self._fit_height(fire_1, 106),
            self._fit_height(fire_2, 106),
        ]

        hyena = self._crop(
            pygame.image.load(asset_path(HYENA_IMAGE)).convert_alpha()
        )
        self.hyena_minion = self._fit_height(hyena, 80)
        self.hyena_minion_flash = self._make_flash(self.hyena_minion, 120)
        self.hyena_boss = self._fit_height(hyena, 240)
        self.hyena_boss_flash = self._make_flash(self.hyena_boss, 55)
        self.minion_shadow = pygame.Surface((58, 18), pygame.SRCALPHA)
        pygame.draw.ellipse(
            self.minion_shadow, (0, 0, 0, 70), self.minion_shadow.get_rect()
        )

        # ------------------------------------------------------------
        # Projectiles
        # ------------------------------------------------------------
        bullet = self._crop(
            pygame.image.load(asset_path(PLAYER_BULLET_IMAGE)).convert_alpha()
        )
        self.player_bullet = pygame.transform.scale(bullet, (10, 17))
        self.player_bullet_shadow = pygame.Surface((18, 26), pygame.SRCALPHA)
        pygame.draw.ellipse(
            self.player_bullet_shadow, (10, 4, 8, 80),
            self.player_bullet_shadow.get_rect(),
        )

        self.enemy_bullet = self._make_orb(
            radius=7,
            outline=(52, 10, 40),
            middle=PURPLE,
            core=(255, 232, 255),
            glow=(255, 90, 230),
        )
        self.boss_bullet = self._make_orb(
            radius=8,
            outline=(38, 12, 58),
            middle=VIOLET,
            core=(245, 238, 255),
            glow=(150, 90, 255),
        )

        # ------------------------------------------------------------
        # Particules, halo, icône
        # ------------------------------------------------------------
        self.particle_sprites = {
            "gold": self._make_particle((255, 186, 70)),
            "white": self._make_particle((255, 246, 220)),
            "purple": self._make_particle((226, 90, 230)),
            "violet": self._make_particle((164, 112, 255)),
            "smoke": self._make_particle((90, 74, 66)),
            "red": self._make_particle((240, 70, 60)),
        }
        self.dim_overlay = pygame.Surface(
            (VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA
        )
        self.dim_overlay.fill((0, 0, 0, 165))
        self.icon = self.player_frames[0]

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------
    @staticmethod
    def _crop(surface, threshold=8):
        """Retire les marges transparentes d'un sprite."""
        mask = pygame.mask.from_surface(surface, threshold)
        rects = mask.get_bounding_rects()
        if not rects:
            return surface
        rect = rects[0]
        if len(rects) > 1:
            rect = rect.unionall(rects[1:])
        if rect.width == 0 or rect.height == 0:
            return surface
        return surface.subsurface(rect).copy()

    @staticmethod
    def _fit_height(surface, height):
        width = max(1, round(surface.get_width() * height / surface.get_height()))
        return pygame.transform.smoothscale(surface, (width, height))

    @staticmethod
    def _fit_width(surface, width):
        height = max(1, round(surface.get_height() * width / surface.get_width()))
        return pygame.transform.smoothscale(surface, (width, height))

    @staticmethod
    def _make_flash(surface, amount=120):
        flash = surface.copy()
        flash.fill(
            (amount, amount, amount, 0), special_flags=pygame.BLEND_RGB_ADD
        )
        return flash

    @staticmethod
    def _make_orb(radius, outline, middle, core, glow):
        pad = 6
        size = radius * 2 + pad * 2
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        for extra, alpha in ((5, 34), (3, 66), (1, 110)):
            pygame.draw.circle(
                surface, (*glow, alpha), (center, center), radius + extra
            )
        pygame.draw.circle(surface, outline, (center, center), radius)
        pygame.draw.circle(surface, middle, (center, center), radius - 2)
        pygame.draw.circle(surface, core, (center, center), max(1, radius - 4))
        return surface

    @staticmethod
    def _make_particle(color):
        surface = pygame.Surface((16, 16), pygame.SRCALPHA)
        for radius, alpha in ((8, 26), (6, 55), (4, 130), (2, 255)):
            pygame.draw.circle(surface, (*color, alpha), (8, 8), radius)
        return surface

    @staticmethod
    def _make_glow(width, height):
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        rect = surface.get_rect()
        for i in range(16):
            alpha = 4 + i * 2
            shrink = 18 - i
            pygame.draw.ellipse(
                surface,
                (*GOLD, alpha),
                rect.inflate(-shrink * 2, -shrink),
            )
        return surface

    # ------------------------------------------------------------------
    # Texte
    # ------------------------------------------------------------------
    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self._font_cache:
            self._font_cache[key] = pygame.font.SysFont(
                "georgia", size, bold=bold
            )
        return self._font_cache[key]

    def text(self, text, size, color, bold=False):
        key = (text, size, color, bold)
        if key not in self._text_cache:
            if len(self._text_cache) > 400:
                self._text_cache.clear()
            self._text_cache[key] = self.font(size, bold).render(
                text, True, color
            )
        return self._text_cache[key]
