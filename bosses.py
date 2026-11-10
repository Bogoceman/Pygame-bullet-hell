"""Boss du jeu.

Chaque boss est une sous-classe de :class:`Boss`. Pour en ajouter un :

1. créer une sous-classe dans ce fichier ;
2. définir son nom, ses PV, son score, son sprite et ses motifs de tir ;
3. l'ajouter à ``BOSS_CLASSES``, dans l'ordre d'apparition.

Exemple minimal ::

    class HyenaAlpha(Boss):
        name = "HYÈNE ALPHA"
        max_hp_value = 600
        score_value = 2500
        bar_color = (120, 220, 140)

        def attack(self, dt, player_pos, bullets):
            ...  # motifs de tir personnalisés

``Boss`` fournit déjà l'entrée, les déplacements, les PV, le flash, le
dessin et un tir visé simple : une sous-classe peut donc être très courte.
"""

import math
import random

import pygame
from pygame.math import Vector2

from constants import (
    BOSS_BULLET_SPEED,
    BOSS_ENTER_Y,
    BOSS_HP,
    BOSS_SCORE,
    PLAYFIELD_WIDTH as PF_W,
    PURPLE,
)
from entities import Bullet, aim_angle
from music import DEFEAT_CHANNEL, ENTRY_CHANNEL, GROWL_CHANNEL, _play_music, play_sound

HYENA_SOUNDS = "assets/characters/hyena/"


class Boss:
    """Classe de base de tous les boss.

    Les attributs de classe décrivent le boss ; les sous-classes peuvent les
    redéfinir ou surcharger ``move`` / ``attack`` / ``load_sprites``.
    """

    name = "BOSS"
    max_hp_value = BOSS_HP
    score_value = BOSS_SCORE

    hit_radius = 80
    entry_y = BOSS_ENTER_Y
    enter_speed = 190.0
    sway_x = 105.0
    sway_y = 16.0
    sway_speed_x = 0.55
    sway_speed_y = 0.9

    bullet_speed = BOSS_BULLET_SPEED
    bullet_radius = 7

    banner_color = PURPLE
    name_color = (247, 232, 255)
    bar_color = (174, 110, 255)
    enraged_bar_color = (235, 74, 200)
    enraged_ratio = 0.5

    # Tir visé par défaut (utilisé si la sous-classe ne surcharge pas attack).
    aim_interval = 1.2
    aim_count = 1
    aim_spread = 0.0

    # Sons : une sous-classe peut les remplacer ou les laisser à None.
    entry_sound = None
    defeat_sound = None
    growl_sounds = ()
    entry_sound_volume = 0.55
    defeat_sound_volume = 0.60
    growl_volume = 0.42
    growl_cooldown = 0.5

    death_particles = (
        ("purple", 60, 360, 1.2),
        ("gold", 24, 260, 1.0),
        ("white", 24, 220, 0.8),
    )

    def __init__(self, assets):
        self.assets = assets
        self.pos = Vector2(PF_W / 2, -150)
        self.target_y = self.entry_y
        self.time = 0.0
        self.hp = self.max_hp_value
        self.max_hp = self.max_hp_value
        self.radius = self.hit_radius
        self.entering = True
        self.dead = False
        self.flash = 0.0
        self.sprite, self.flash_sprite = self.load_sprites(assets)
        self.bullet_sprite = self.load_bullet(assets)
        self.aim_cd = self.aim_interval
        self.growl_cd = 0.0

        if self.entry_sound:
            play_sound(
                self.entry_sound, self.entry_sound_volume, ENTRY_CHANNEL
            )

    # ------------------------------------------------------------------
    # Personnalisation
    # ------------------------------------------------------------------
    def load_sprites(self, assets):
        """Retourne (sprite normal, sprite flash) du boss."""
        return assets.hyena_boss, assets.hyena_boss_flash

    def load_bullet(self, assets):
        """Sprite des projectiles du boss."""
        return assets.boss_bullet

    @property
    def enraged(self):
        return self.hp <= self.max_hp * self.enraged_ratio

    # ------------------------------------------------------------------
    # Mise à jour
    # ------------------------------------------------------------------
    def update(self, dt, player_pos, bullets):
        self.time += dt
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)
        if self.growl_cd > 0:
            self.growl_cd = max(0.0, self.growl_cd - dt)

        if self.entering:
            self.pos.y += self.enter_speed * dt
            if self.pos.y >= self.target_y:
                self.pos.y = self.target_y
                self.entering = False
                self.time = 0.0
            return

        self.move(dt)
        self.attack(dt, player_pos, bullets)

    def move(self, dt):
        """Déplacement d'attente, au-dessus de l'arène."""
        self.pos.x = (
            PF_W / 2 + math.sin(self.time * self.sway_speed_x) * self.sway_x
        )
        self.pos.y = (
            self.target_y + math.sin(self.time * self.sway_speed_y) * self.sway_y
        )

    def attack(self, dt, player_pos, bullets):
        """Tir visé simple : surchargez cette méthode pour un vrai motif."""
        self.aim_cd -= dt
        if self.aim_cd > 0:
            return
        self.aim_cd = self.aim_interval
        self.growl()
        base = aim_angle(self.pos, player_pos)
        for index in range(self.aim_count):
            angle = base + (index - (self.aim_count - 1) / 2) * self.aim_spread
            self.shoot(bullets, angle)

    def growl(self):
        """Joue un grognement aléatoire (un seul à la fois)."""
        if self.growl_cd > 0 or not self.growl_sounds:
            return
        self.growl_cd = self.growl_cooldown
        play_sound(
            random.choice(self.growl_sounds),
            self.growl_volume,
            GROWL_CHANNEL,
        )
        
    def on_entered(self):
        """Appelé par le jeu quand le boss est entré dans l'arène (son de
        grognement, etc.)."""
        self.pygame.mixer.music.load(self.entry_sound)

    def on_defeated(self):
        """Appelé par le jeu quand le boss meurt (son de défaite, etc.)."""
        if self.defeat_sound:
            play_sound(
                self.defeat_sound, self.defeat_sound_volume, DEFEAT_CHANNEL
            )

    def shoot(self, bullets, angle, speed=None):
        speed = self.bullet_speed if speed is None else speed
        bullets.append(
            Bullet(
                self.pos + Vector2(0, 34),
                Vector2(math.cos(angle), math.sin(angle)) * speed,
                self.bullet_radius,
                self.bullet_sprite,
            )
        )

    def hit(self, damage):
        self.hp -= damage
        self.flash = 0.07
        return self.hp <= 0

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------
    def draw(self, surface, offset):
        x = int(self.pos.x + offset.x)
        y = int(self.pos.y + offset.y)
        sprite = self.flash_sprite if self.flash > 0 else self.sprite
        surface.blit(sprite, sprite.get_rect(center=(x, y)))

    def draw_health_bar(self, surface, offset):
        left = int(offset.x + 34)
        top = int(offset.y + 24)
        width = PF_W - 68
        pygame.draw.rect(surface, (8, 6, 14), (left - 3, top - 3, width + 6, 16))
        pygame.draw.rect(
            surface, (146, 118, 62), (left - 1, top - 1, width + 2, 12), 1
        )
        ratio = max(0.0, self.hp / self.max_hp)
        color = self.enraged_bar_color if self.enraged else self.bar_color
        pygame.draw.rect(surface, color, (left, top, int(width * ratio), 10))
        label = self.assets.text(self.name, 20, self.name_color, bold=True)
        surface.blit(label, label.get_rect(center=(left + width // 2, top + 27)))


class HyenaQueen(Boss):
    """La reine hyène : tirs visés, anneaux et double spirale en phase 2."""

    name = "REINE HYÈNE"
    max_hp_value = BOSS_HP
    score_value = BOSS_SCORE
    growl_sounds = (HYENA_SOUNDS + "hyena_growl_1.wav", HYENA_SOUNDS + "hyena_growl_2.wav")
    defeat_sound = HYENA_SOUNDS + "hyena_defeated.wav"
    entry_sound = HYENA_SOUNDS + "hyena_entry.wav"

    def __init__(self, assets):
        super().__init__(assets)
        self.aim_cd = 1.4
        self.ring_cd = 2.2
        self.spiral_cd = 0.18
        self.ring_offset = random.uniform(0, math.tau)
        self.spiral_angle = random.uniform(0, math.tau)
        self.on_entered
        _play_music(HYENA_SOUNDS + "hyana_ost_boss.mp3", 0.10, "boss")

    def attack(self, dt, player_pos, bullets):
        # Tir visé.
        self.aim_cd -= dt
        if self.aim_cd <= 0:
            self.aim_cd = 0.95 if self.enraged else 1.2
            base = aim_angle(self.pos, player_pos)
            count = 5 if self.enraged else 3
            spread = 0.19 if self.enraged else 0.11
            self.growl()
            for index in range(count):
                angle = base + (index - (count - 1) / 2) * spread
                self.shoot(bullets, angle)

        # Anneau de balles.
        self.ring_cd -= dt
        if self.ring_cd <= 0:
            self.ring_cd = 1.9 if self.enraged else 2.4
            self.growl()
            count = 26 if self.enraged else 20
            self.ring_offset += 0.21
            for index in range(count):
                angle = self.ring_offset + index * math.tau / count
                self.shoot(bullets, angle, 175)

        # Double spirale en phase 2.
        if self.enraged:
            self.spiral_cd -= dt
            if self.spiral_cd <= 0:
                self.growl()
                self.spiral_cd = 0.11
                self.spiral_angle += 0.47
                self.shoot(bullets, self.spiral_angle, 205)
                self.shoot(bullets, self.spiral_angle + math.pi, 205)


# Ordre d'apparition des boss. Ajoutez vos sous-classes ici.
BOSS_CLASSES = [HyenaQueen]
