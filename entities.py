"""Entités du jeu : joueur, projectiles, hyènes et particules."""

import math
import random

import pygame
from pygame.math import Vector2

from constants import (
    MINION_BULLET_SPEED,
    MINION_FIRE_INTERVAL_MAX,
    MINION_FIRE_INTERVAL_MIN,
    MINION_HP,
    MINION_SPEED,
    PLAYER_BULLET_SPEED,
    PLAYER_FIRE_INTERVAL,
    PLAYER_FOCUS_SPEED,
    PLAYER_LIVES,
    PLAYER_BOMBS,
    PLAYER_RADIUS,
    PLAYER_SPEED,
    PLAYFIELD_HEIGHT as PF_H,
    PLAYFIELD_WIDTH as PF_W,
)


def aim_angle(start, target):
    return math.atan2(target.y - start.y, target.x - start.x)


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


class Bullet:
    """Un projectile, allié ou ennemi."""

    __slots__ = ("pos", "vel", "radius", "sprite", "friendly", "grazed", "dead")

    def __init__(self, pos, vel, radius, sprite, friendly=False):
        self.pos = Vector2(pos)
        self.vel = Vector2(vel)
        self.radius = radius
        self.sprite = sprite
        self.friendly = friendly
        self.grazed = False
        self.dead = False

    def update(self, dt):
        self.pos += self.vel * dt

    def out_of_bounds(self):
        margin = 45
        return (
            self.pos.x < -margin
            or self.pos.x > PF_W + margin
            or self.pos.y < -margin
            or self.pos.y > PF_H + margin
        )

    def draw(self, surface, offset, shadows=None):
        x = int(self.pos.x + offset.x)
        y = int(self.pos.y + offset.y)
        if shadows is not None:
            surface.blit(shadows, shadows.get_rect(center=(x, y)))
        surface.blit(self.sprite, self.sprite.get_rect(center=(x, y)))


class Player:
    """Le camion du chasseur, contrôlé au clavier."""

    def __init__(self, assets):
        self.assets = assets
        self.pos = Vector2(PF_W / 2, PF_H - 150)
        self.radius = PLAYER_RADIUS
        self.lives = PLAYER_LIVES
        self.bombs = PLAYER_BOMBS
        self.invuln = 2.0
        self.fire_cd = 0.0
        self.shot_index = 0
        self.fired = False
        self.focus = False

    def update(self, dt, keys, bullets, particles):
        self.fired = False
        direction = Vector2()
        if keys[pygame.K_LEFT] or keys[pygame.K_q] or keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_z] or keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            direction.y += 1

        self.focus = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        if direction.length_squared() > 0:
            direction.normalize_ip()

        speed = PLAYER_FOCUS_SPEED if self.focus else PLAYER_SPEED
        self.pos += direction * speed * dt
        self.pos.x = clamp(self.pos.x, 40, PF_W - 40)
        self.pos.y = clamp(self.pos.y, 92, PF_H - 54)

        if self.invuln > 0:
            self.invuln = max(0.0, self.invuln - dt)

        # Tir automatique : le chasseur ne s'arrête jamais de tirer.
        self.fire_cd -= dt
        while self.fire_cd <= 0:
            self.fire_cd += PLAYER_FIRE_INTERVAL
            self.shot_index += 1
            self.fired = True
            muzzle_y = self.pos.y - 48
            for offset_x in (-9, 9):
                bullets.append(
                    Bullet(
                        (self.pos.x + offset_x, muzzle_y),
                        (0, -PLAYER_BULLET_SPEED),
                        5,
                        self.assets.player_bullet,
                        friendly=True,
                    )
                )
            # Petite étincelle au bout du canon.
            if len(particles) < 200:
                particles.append(
                    Particle(
                        (self.pos.x, muzzle_y),
                        (random.uniform(-18, 18), random.uniform(-70, -30)),
                        random.uniform(0.07, 0.14),
                        self.assets.particle_sprites["gold"],
                    )
                )

    def current_sprite(self):
        # Les deux images de tir alternent à chaque coup de feu : l'animation
        # reste parfaitement synchronisée avec le son du fusil.
        return self.assets.player_frames[1 + self.shot_index % 2]

    def draw(self, surface, offset, focus):
        # Clignotement pendant l'invulnérabilité.
        if self.invuln > 0 and int(self.invuln * 16) % 2 == 0:
            return

        sprite = self.current_sprite()
        rect = sprite.get_rect(
            midbottom=(int(self.pos.x + offset.x), int(self.pos.y + offset.y + 48))
        )
        surface.blit(sprite, rect)

        if focus:
            center = (int(self.pos.x + offset.x), int(self.pos.y + offset.y))
            pygame.draw.circle(surface, (255, 246, 220), center, 8, 1)
            pygame.draw.circle(surface, (235, 72, 72), center, 3)

    def hit(self):
        """Retourne True si le joueur vient réellement d'être touché."""
        if self.invuln > 0:
            return False
        self.lives -= 1
        self.invuln = 2.6
        return True


class Minion:
    """Une hyène ordinaire qui descend en zigzag."""

    def __init__(self, assets, x, phase):
        self.assets = assets
        self.pos = Vector2(x, -70)
        self.base_x = x
        self.phase = phase
        self.time = 0.0
        self.speed = MINION_SPEED + random.uniform(-12, 12)
        self.amplitude = random.uniform(24, 46)
        self.hp = MINION_HP
        self.radius = 28
        self.flash = 0.0
        self.dead = False
        self.fire_cd = random.uniform(
            MINION_FIRE_INTERVAL_MIN, MINION_FIRE_INTERVAL_MAX
        )

    def update(self, dt, player_pos, bullets):
        self.time += dt
        self.pos.y += self.speed * dt
        self.pos.x = clamp(
            self.base_x + math.sin(self.time * 2.1 + self.phase) * self.amplitude,
            42,
            PF_W - 42,
        )
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        # Ne tire que lorsqu'elle est visible dans l'aire de jeu.
        if 30 < self.pos.y < PF_H - 210:
            self.fire_cd -= dt
            if self.fire_cd <= 0:
                self.fire_cd = random.uniform(
                    MINION_FIRE_INTERVAL_MIN, MINION_FIRE_INTERVAL_MAX
                )
                angle = aim_angle(self.pos, player_pos)
                for spread in (-0.11, 0.11):
                    self._shoot(bullets, angle + spread)

        if self.pos.y > PF_H + 80:
            self.dead = True

    def _shoot(self, bullets, angle):
        vel = Vector2(math.cos(angle), math.sin(angle)) * MINION_BULLET_SPEED
        bullets.append(
            Bullet(
                self.pos + Vector2(0, 18),
                vel,
                6,
                self.assets.enemy_bullet,
            )
        )

    def hit(self, damage):
        self.hp -= damage
        self.flash = 0.08
        return self.hp <= 0

    def draw(self, surface, offset):
        x = int(self.pos.x + offset.x)
        y = int(self.pos.y + offset.y)
        surface.blit(
            self.assets.minion_shadow,
            self.assets.minion_shadow.get_rect(center=(x, y + 30)),
        )
        sprite = self.assets.hyena_minion_flash if self.flash > 0 else self.assets.hyena_minion
        surface.blit(sprite, sprite.get_rect(center=(x, y)))


class Particle:
    __slots__ = ("pos", "vel", "life", "max_life", "sprite")

    def __init__(self, pos, vel, life, sprite):
        self.pos = Vector2(pos)
        self.vel = Vector2(vel)
        self.life = life
        self.max_life = life
        self.sprite = sprite

    def update(self, dt):
        self.pos += self.vel * dt
        self.vel *= 0.94
        self.life -= dt

    def draw(self, surface, offset):
        if self.life <= 0:
            return
        alpha = int(255 * max(0.0, self.life / self.max_life))
        self.sprite.set_alpha(alpha)
        surface.blit(
            self.sprite,
            self.sprite.get_rect(
                center=(int(self.pos.x + offset.x), int(self.pos.y + offset.y))
            ),
        )
