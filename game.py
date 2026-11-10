"""Boucle principale, états du jeu et affichage du HUD."""

import math
import random

import pygame
from pygame.math import Vector2

from assets import Assets, asset_path
from bosses import BOSS_CLASSES
from music import start_gun_loop, start_menu_music, stop_gun_loop
from constants import (
    BOSS_WARNING_TIME,
    BG_SCROLL_SPEED,
    BOSS_INTERMISSION,
    CREAM,
    FIRST_SPAWN_DELAY,
    GAME_NAME,
    GOLD,
    GOLD_DARK,
    GRAZE_DISTANCE,
    GRAZE_SCORE,
    HIGHSCORE_FILE,
    MAX_PARTICLES,
    MINION_SCORE,
    MUTED,
    PANEL_DARK,
    PLAYER_BULLET_DAMAGE,
    PLAYER_INVULNERABLE_TIME,
    PLAYER_RADIUS,
    PLAYFIELD_HEIGHT,
    PLAYFIELD_WIDTH,
    PLAYFIELD_X,
    PLAYFIELD_Y,
    PURPLE,
    RED,
    SPAWN_INTERVAL_MIN,
    SPAWN_INTERVAL_START,
    STAGE_DURATION,
    VICTORY_DELAY,
    VIOLET,
    VIRTUAL_HEIGHT,
    VIRTUAL_WIDTH,
    WHITE,
)
from entities import Minion, Particle, Player

HIGHSCORE_PATH = asset_path(HIGHSCORE_FILE)
PLAYFIELD_RECT = pygame.Rect(
    PLAYFIELD_X, PLAYFIELD_Y, PLAYFIELD_WIDTH, PLAYFIELD_HEIGHT
)


def load_highscore():
    try:
        with open(HIGHSCORE_PATH, "r", encoding="utf-8") as file:
            return max(0, int(file.read().strip() or "0"))
    except (OSError, ValueError):
        return 0


def save_highscore(score):
    try:
        with open(HIGHSCORE_PATH, "w", encoding="utf-8") as file:
            file.write(str(score))
    except OSError:
        pass


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(GAME_NAME)
        self.screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
        start_menu_music()

        self.assets = Assets()
        try:
            pygame.display.set_icon(self.assets.icon)
        except pygame.error:
            pass

        self.canvas = pygame.Surface(
            (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        ).convert()
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "menu"
        self.menu_time = 0.0

        self.hi_score = load_highscore()
        self.new_record = False
        self.mouse = Vector2(-10000, -10000)
        self.hover_play = False
        self.hover_replay = False
        self.hover_menu = False
        self._cursor_hand = False

        self.viewport = pygame.Rect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        self.scale = 1.0
        self._screen_size = self.screen.get_size()
        self.update_viewport()

        # Zone cliquable du bouton « jouer » du menu.
        self.play_rect = pygame.Rect(
            0,
            0,
            self.assets.play_button.get_width(),
            self.assets.play_button.get_height(),
        )
        self.play_rect.center = (VIRTUAL_WIDTH // 2, int(VIRTUAL_HEIGHT / 1.7))

        self.replay_rect = pygame.Rect(VIRTUAL_WIDTH // 2 - 230, 700, 460, 78)
        self.menu_rect = pygame.Rect(VIRTUAL_WIDTH // 2 - 230, 800, 460, 78)

        self.reset_world()

    # ------------------------------------------------------------------
    # Cycle de vie
    # ------------------------------------------------------------------
    def reset_world(self):
        self.player = Player(self.assets)
        self.bullets = []
        self.enemies = []
        self.boss = None
        self.particles = []

        self.score = 0
        self.graze = 0
        self.stage_time = 0.0
        self.spawn_cd = FIRST_SPAWN_DELAY
        self.wave = 0

        self.boss_spawned = False
        self.boss_index = 0
        self.next_boss_timer = 0.0
        self.victory_pending = False
        self.win_timer = 0.0

        self.scroll = 0.0
        self.shake = 0.0
        self.flash = 0.0
        self.fade = 0.0

        self.banner = ""
        self.banner_color = GOLD
        self.banner_timer = 0.0
        self.banner_total = 1.0

    def start_game(self):
        self.reset_world()
        stop_gun_loop()
        self.state = "playing"
        self.new_record = False
        self.fade = 0.85
        self.set_banner("STAGE 1  ·  SAVANE", 2.8, GOLD)
        self.player.invuln = 2.0

    def go_menu(self):
        self.state = "menu"
        stop_gun_loop()
        self.menu_time = 0.0
        self.set_banner("", 0, GOLD)

    def run(self):
        while self.running:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()

    # ------------------------------------------------------------------
    # Entrées
    # ------------------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self._screen_size = self.screen.get_size()
                self.update_viewport()
            elif event.type == pygame.MOUSEMOTION:
                self.update_mouse(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.update_mouse(event.pos)
                self.handle_click(self.mouse)
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

    def handle_key(self, key):
        if self.state == "menu":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start_game()
            elif key == pygame.K_ESCAPE:
                self.running = False
        elif self.state == "playing":
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self.state = "paused"
                stop_gun_loop()
            elif key == pygame.K_x:
                self.use_bomb()
            elif key == pygame.K_r:
                self.start_game()
        elif self.state == "paused":
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self.state = "playing"
            elif key == pygame.K_r:
                self.start_game()
            elif key == pygame.K_m:
                self.go_menu()
        elif self.state in ("gameover", "win"):
            if key in (pygame.K_r, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.start_game()
            elif key in (pygame.K_m, pygame.K_ESCAPE):
                self.go_menu()

    def handle_click(self, pos):
        if self.state == "menu":
            if self.play_rect.inflate(40, 24).collidepoint(pos):
                self.start_game()
        elif self.state in ("gameover", "win"):
            if self.replay_rect.collidepoint(pos):
                self.start_game()
            elif self.menu_rect.collidepoint(pos):
                self.go_menu()

    def update_mouse(self, screen_pos=None):
        if screen_pos is None:
            screen_pos = pygame.mouse.get_pos()
        if self.viewport.collidepoint(screen_pos) and self.scale > 0:
            self.mouse = Vector2(
                (screen_pos[0] - self.viewport.x) / self.scale,
                (screen_pos[1] - self.viewport.y) / self.scale,
            )
        else:
            self.mouse = Vector2(-10000, -10000)

    def set_cursor(self, hand):
        if hand == self._cursor_hand:
            return
        self._cursor_hand = hand
        try:
            pygame.mouse.set_cursor(
                pygame.SYSTEM_CURSOR_HAND if hand else pygame.SYSTEM_CURSOR_ARROW
            )
        except pygame.error:
            pass

    # ------------------------------------------------------------------
    # Mise à jour
    # ------------------------------------------------------------------
    def update(self, dt):
        self.update_mouse()

        if self.state == "menu":
            self.menu_time += dt
            self.hover_play = self.play_rect.inflate(40, 24).collidepoint(self.mouse)
            self.set_cursor(self.hover_play)
        elif self.state == "playing":
            self.set_cursor(False)
            self.update_world(dt)
        elif self.state == "paused":
            self.set_cursor(False)
        else:
            self.hover_replay = self.replay_rect.collidepoint(self.mouse)
            self.hover_menu = self.menu_rect.collidepoint(self.mouse)
            self.set_cursor(self.hover_replay or self.hover_menu)
            self.update_particles(dt)
            self.scroll += BG_SCROLL_SPEED * 0.25 * dt

        self.update_visual_timers(dt)

    def update_world(self, dt):
        self.stage_time += dt
        self.scroll += BG_SCROLL_SPEED * dt

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.bullets, self.particles)

        # Le son du fusil démarre au premier coup et boucle sur le rythme
        # exact des tirs (10 coups par seconde).
        if self.player.fired and not self.victory_pending:
            start_gun_loop()

        if not self.victory_pending:
            self.update_spawning(dt)
            for minion in self.enemies:
                minion.update(dt, self.player.pos, self.bullets)
            if self.boss is not None and not self.boss.dead:
                self.boss.update(dt, self.player.pos, self.bullets)

        for bullet in self.bullets:
            bullet.update(dt)
            if bullet.out_of_bounds():
                bullet.dead = True

        self.update_collisions()
        self.cleanup()
        self.update_particles(dt)

        if self.victory_pending and self.state == "playing":
            self.win_timer -= dt
            if self.win_timer <= 0:
                self.finish("win")

    def update_visual_timers(self, dt):
        if self.banner_timer > 0:
            self.banner_timer = max(0.0, self.banner_timer - dt)
        if self.shake > 0:
            self.shake = max(0.0, self.shake - dt * 34)
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)
        if self.fade > 0:
            self.fade = max(0.0, self.fade - dt * 1.8)

    def update_spawning(self, dt):
        if self.boss_spawned:
            # Enchaînement des boss : après une victoire, le suivant arrive
            # après une courte pause (BOSS_INTERMISSION).
            if (
                self.boss is None
                and not self.victory_pending
                and self.next_boss_timer > 0
            ):
                self.next_boss_timer -= dt
                if self.next_boss_timer <= 0:
                    self.spawn_boss()
            return

        self.spawn_cd -= dt
        if self.spawn_cd <= 0 and self.stage_time < STAGE_DURATION - 1.0:
            self.wave += 1
            self.spawn_cd = max(
                SPAWN_INTERVAL_MIN,
                SPAWN_INTERVAL_START - self.stage_time * 0.025,
            )
            x = random.uniform(60, PLAYFIELD_WIDTH - 60)
            self.enemies.append(
                Minion(self.assets, x, random.uniform(0, math.tau))
            )
            if self.wave % 4 == 0:
                self.enemies.append(
                    Minion(
                        self.assets,
                        PLAYFIELD_WIDTH - x,
                        random.uniform(0, math.tau),
                    )
                )

        if self.stage_time >= STAGE_DURATION:
            self.spawn_boss()

    def spawn_boss(self):
        self.boss_spawned = True
        self.next_boss_timer = 0.0
        boss_class = BOSS_CLASSES[self.boss_index]
        self.boss = boss_class(self.assets)
        # Arène nette pour l'arrivée du boss.
        self.enemies.clear()
        for bullet in self.bullets:
            if not bullet.friendly:
                bullet.dead = True
        self.set_banner(
            f"!! {self.boss.name} !!",
            BOSS_WARNING_TIME,
            self.boss.banner_color,
        )
        self.shake = 9

    def set_banner(self, text, duration, color):
        self.banner = text
        self.banner_timer = duration
        self.banner_total = max(0.001, duration)
        self.banner_color = color

    # ------------------------------------------------------------------
    # Collisions
    # ------------------------------------------------------------------
    def update_collisions(self):
        self.collide_player_bullets()
        if self.state != "playing":
            return
        self.collide_enemy_bullets()
        if self.state != "playing":
            return
        self.collide_minions()

    def collide_player_bullets(self):
        boss = self.boss
        for bullet in self.bullets:
            if bullet.dead or not bullet.friendly:
                continue

            if boss is not None and not boss.dead:
                if (bullet.pos - boss.pos).length_squared() < (
                    boss.radius + bullet.radius
                ) ** 2:
                    bullet.dead = True
                    self.add_particles(bullet.pos, "gold", 2, 80, 0.25)
                    if boss.hit(PLAYER_BULLET_DAMAGE):
                        self.on_boss_defeated()
                    continue

            for minion in self.enemies:
                if minion.dead:
                    continue
                if (bullet.pos - minion.pos).length_squared() < (
                    minion.radius + bullet.radius
                ) ** 2:
                    bullet.dead = True
                    self.add_particles(bullet.pos, "gold", 2, 80, 0.25)
                    if minion.hit(PLAYER_BULLET_DAMAGE):
                        self.kill_minion(minion)
                    break

    def collide_enemy_bullets(self):
        player = self.player
        for bullet in self.bullets:
            if bullet.dead or bullet.friendly:
                continue
            distance_sq = (bullet.pos - player.pos).length_squared()

            if not bullet.grazed and distance_sq < (
                GRAZE_DISTANCE + bullet.radius
            ) ** 2:
                bullet.grazed = True
                self.graze += 1
                self.score += GRAZE_SCORE
                if random.random() < 0.2:
                    self.add_particles(bullet.pos, "white", 1, 25, 0.3)

            if player.invuln <= 0 and distance_sq < (
                PLAYER_RADIUS + bullet.radius
            ) ** 2:
                bullet.dead = True
                self.damage_player()
                if self.state != "playing":
                    return

    def collide_minions(self):
        if self.player.invuln > 0:
            return
        for minion in self.enemies:
            if minion.dead:
                continue
            if (minion.pos - self.player.pos).length_squared() < (
                minion.radius + PLAYER_RADIUS + 6
            ) ** 2:
                self.kill_minion(minion, give_score=False)
                self.damage_player()
                if self.state != "playing":
                    return

    def damage_player(self):
        if not self.player.hit():
            return

        self.shake = 16
        self.flash = 0.24
        self.add_particles(self.player.pos, "red", 24, 260, 0.8)
        self.add_particles(self.player.pos, "smoke", 10, 120, 0.9)

        # On nettoie les balles autour du joueur pour laisser une chance.
        for bullet in self.bullets:
            if not bullet.friendly and (
                bullet.pos - self.player.pos
            ).length_squared() < 130**2:
                bullet.dead = True

        if self.player.lives <= 0:
            self.set_banner("GAME OVER", 2.0, RED)
            self.finish("gameover")
        else:
            self.player.pos = Vector2(
                PLAYFIELD_WIDTH / 2, PLAYFIELD_HEIGHT - 150
            )
            self.player.invuln = PLAYER_INVULNERABLE_TIME
            self.set_banner("VIE PERDUE", 1.4, RED)

    def kill_minion(self, minion, give_score=True):
        if minion.dead:
            return
        minion.dead = True
        if give_score:
            self.score += MINION_SCORE
        self.add_particles(minion.pos, "purple", 16, 230, 0.75)
        self.add_particles(minion.pos, "white", 6, 130, 0.45)

    def on_boss_defeated(self):
        if self.victory_pending or self.boss is None:
            return
        boss = self.boss
        boss_pos = boss.pos.copy()
        boss.dead = True
        self.boss = None
        self.score += boss.score_value
        self.shake = 18
        self.flash = 0.4
        for key, count, speed, life in boss.death_particles:
            self.add_particles(boss_pos, key, count, speed, life)
        self.enemies.clear()
        for bullet in self.bullets:
            if not bullet.friendly:
                bullet.dead = True
        self.player.invuln = max(self.player.invuln, 4.0)

        if self.boss_index + 1 < len(BOSS_CLASSES):
            # Il reste des boss : on prépare le suivant.
            self.boss_index += 1
            self.next_boss_timer = BOSS_INTERMISSION
            next_name = BOSS_CLASSES[self.boss_index].name
            self.set_banner(
                f"{next_name} APPROCHE !", BOSS_INTERMISSION, boss.banner_color
            )
        else:
            self.victory_pending = True
            self.set_banner("SAVANE LIBÉRÉE !", VICTORY_DELAY, GOLD)
            self.win_timer = VICTORY_DELAY
            stop_gun_loop()

    def cleanup(self):
        self.bullets = [bullet for bullet in self.bullets if not bullet.dead]
        self.enemies = [minion for minion in self.enemies if not minion.dead]
        if len(self.particles) > MAX_PARTICLES:
            del self.particles[: len(self.particles) - MAX_PARTICLES]

    def use_bomb(self):
        if self.state != "playing" or self.player.bombs <= 0:
            return
        self.player.bombs -= 1
        self.player.invuln = max(self.player.invuln, 2.0)
        self.shake = 14
        self.flash = 0.45

        for bullet in self.bullets:
            if not bullet.friendly:
                bullet.dead = True

        for minion in list(self.enemies):
            if minion.hit(40):
                self.kill_minion(minion)

        if self.boss is not None and not self.boss.dead:
            self.boss.flash = 0.25
            if self.boss.hit(70):
                self.on_boss_defeated()

        if not self.victory_pending:
            self.set_banner("BOMBE !", 0.7, VIOLET)

    def finish(self, state):
        if self.state in ("gameover", "win"):
            return
        self.state = state
        stop_gun_loop()
        if self.score > self.hi_score:
            self.hi_score = self.score
            self.new_record = True
            save_highscore(self.hi_score)
        else:
            self.new_record = False

    # ------------------------------------------------------------------
    # Particules
    # ------------------------------------------------------------------
    def add_particles(self, pos, color_key, count, speed, life=0.6):
        if count <= 0:
            return
        sprite = self.assets.particle_sprites[color_key]
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            velocity = random.uniform(speed * 0.3, speed)
            self.particles.append(
                Particle(
                    Vector2(pos),
                    Vector2(math.cos(angle), math.sin(angle)) * velocity,
                    random.uniform(life * 0.6, life * 1.2),
                    sprite,
                )
            )

    def update_particles(self, dt):
        for particle in self.particles:
            particle.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------
    def update_viewport(self):
        width, height = self.screen.get_size()
        scale = min(width / VIRTUAL_WIDTH, height / VIRTUAL_HEIGHT)
        view_width = max(1, int(VIRTUAL_WIDTH * scale))
        view_height = max(1, int(VIRTUAL_HEIGHT * scale))
        self.viewport = pygame.Rect(
            (width - view_width) // 2,
            (height - view_height) // 2,
            view_width,
            view_height,
        )
        self.scale = view_width / VIRTUAL_WIDTH

    def draw(self):
        current_size = self.screen.get_size()
        if current_size != self._screen_size:
            self._screen_size = current_size
            self.update_viewport()

        self.canvas.fill((0, 0, 0))
        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_game()

        self.present()

    def draw_menu(self):
        canvas = self.canvas
        canvas.blit(self.assets.menu_bg, (0, 0))

        # Poussière dorée flottant dans le menu.
        sprite = self.assets.particle_sprites["gold"]
        for i in range(22):
            phase = self.menu_time * 0.4 + i
            x = (i * 173 + math.sin(phase) * 70 + 60) % VIRTUAL_WIDTH
            y = (
                VIRTUAL_HEIGHT
                - ((self.menu_time * 30 + i * 97) % (VIRTUAL_HEIGHT + 40))
                + 20
            )
            alpha = 35 + int(45 * (0.5 + 0.5 * math.sin(phase * 1.7)))
            sprite.set_alpha(alpha)
            canvas.blit(sprite, sprite.get_rect(center=(int(x), int(y))))
        sprite.set_alpha(255)

        title_rect = self.assets.menu_title.get_rect(
            center=(VIRTUAL_WIDTH // 2, int(VIRTUAL_HEIGHT / 3.5))
        )
        canvas.blit(self.assets.menu_title, title_rect)

        self.hover_play = self.play_rect.inflate(40, 24).collidepoint(self.mouse)
        if self.hover_play:
            canvas.blit(
                self.assets.play_glow,
                self.assets.play_glow.get_rect(center=self.play_rect.center),
            )
        button = (
            self.assets.play_button_hover
            if self.hover_play
            else self.assets.play_button
        )
        canvas.blit(button, button.get_rect(center=self.play_rect.center))

        canvas.blit(
            self.assets.menu_bottom_shade,
            (0, VIRTUAL_HEIGHT - self.assets.menu_bottom_shade.get_height()),
        )
        self.blit_text(
            canvas,
            f"MEILLEUR SCORE : {self.hi_score:07d}",
            30,
            GOLD,
            (VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 92),
            "center",
            bold=True,
        )
        self.blit_text(
            canvas,
            "ZQSD / FLÈCHES : SE DÉPLACER   ·   MAJ : FOCUS   ·   X : BOMBE",
            22,
            MUTED,
            (VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 48),
            "center",
        )

    def draw_game(self):
        canvas = self.canvas
        canvas.blit(self.assets.hud, (0, 0))
        canvas.set_clip(PLAYFIELD_RECT)

        offset = Vector2(PLAYFIELD_X, PLAYFIELD_Y)
        self.draw_background(canvas)

        for minion in self.enemies:
            minion.draw(canvas, offset)
        if self.boss is not None:
            self.boss.draw(canvas, offset)

        for bullet in self.bullets:
            if bullet.friendly:
                bullet.draw(canvas, offset, self.assets.player_bullet_shadow)

        self.player.draw(canvas, offset, self.player.focus)

        for bullet in self.bullets:
            if not bullet.friendly:
                bullet.draw(canvas, offset)

        for particle in self.particles:
            particle.draw(canvas, offset)

        if self.boss is not None:
            self.boss.draw_health_bar(canvas, offset)

        self.draw_banner(canvas)

        if self.flash > 0:
            overlay = self.assets.playfield_flash
            overlay.set_alpha(
                int(95 * min(1.0, self.flash / 0.45))
            )
            canvas.blit(overlay, (PLAYFIELD_X, PLAYFIELD_Y))

        canvas.set_clip(None)
        self.draw_hud(canvas)
        self.draw_state_overlay(canvas)

        if self.fade > 0:
            alpha = int(190 * min(1.0, self.fade / 0.85))
            overlay = pygame.Surface(
                (VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, alpha))
            canvas.blit(overlay, (0, 0))

    def draw_background(self, canvas):
        tile_height = self.assets.bg_tile_height
        offset_y = self.scroll % tile_height
        top = PLAYFIELD_Y + offset_y - tile_height
        canvas.blit(self.assets.bg_tile, (PLAYFIELD_X, top))
        canvas.blit(
            self.assets.bg_tile, (PLAYFIELD_X, top + tile_height)
        )
        canvas.blit(
            self.assets.playfield_shade, (PLAYFIELD_X, PLAYFIELD_Y)
        )

    def draw_banner(self, canvas):
        if self.banner_timer <= 0 or not self.banner:
            return
        alpha = 255
        if self.banner_timer < 0.7:
            alpha = int(255 * self.banner_timer / 0.7)

        text = self.assets.text(self.banner, 36, self.banner_color, bold=True)
        # Réduit la police si le nom du boss est long, pour rester dans l'arène.
        max_width = PLAYFIELD_WIDTH - 26
        size = 36
        while text.get_width() > max_width and size > 18:
            size -= 2
            text = self.assets.text(
                self.banner, size, self.banner_color, bold=True
            )
        shadow = self.assets.text(self.banner, size, (10, 8, 14), bold=True)
        text.set_alpha(alpha)
        shadow.set_alpha(alpha)
        center = (PLAYFIELD_X + PLAYFIELD_WIDTH // 2, 300)
        for dx, dy in ((-2, 2), (2, 2), (0, 3)):
            rect = shadow.get_rect(center=(center[0] + dx, center[1] + dy))
            canvas.blit(shadow, rect)
        canvas.blit(text, text.get_rect(center=center))
        text.set_alpha(255)
        shadow.set_alpha(255)

    def draw_hud(self, canvas):
        # Panneau de droite : scores alignés à droite sur les lignes du HUD.
        self.blit_text(
            canvas,
            f"{self.hi_score:07d}",
            36,
            GOLD,
            (1852, 175),
            "midright",
            bold=True,
        )
        self.blit_text(
            canvas,
            f"{self.score:07d}",
            38,
            CREAM,
            (1852, 265),
            "midright",
            bold=True,
        )

        stats = (
            ("VIES", str(max(0, self.player.lives))),
            ("BOMBES", str(self.player.bombs)),
            ("GRAZE", str(self.graze)),
        )
        for index, (label, value) in enumerate(stats):
            y = 390 + index * 37
            self.blit_text(canvas, label, 20, MUTED, (1245, y))
            self.blit_text(canvas, value, 25, CREAM, (1425, y - 4), bold=True)

        if self.victory_pending:
            objective = "SAVANE LIBÉRÉE"
            objective_color = GOLD
        elif self.boss is not None:
            objective = (
                f"OBJECTIF : {self.boss.name}  "
                f"({self.boss_index + 1}/{len(BOSS_CLASSES)})"
            )
            objective_color = PURPLE
        elif self.boss_spawned:
            objective = f"BOSS SUIVANT : {BOSS_CLASSES[self.boss_index].name}"
            objective_color = PURPLE
        else:
            objective = "OBJECTIF : SURVIVRE"
            objective_color = MUTED
        self.blit_text(canvas, objective, 20, objective_color, (1245, 510))

        # Panneau de gauche : manche + contrôles.
        self.blit_text(canvas, "SAVANE", 44, GOLD, (84, 558), bold=True)

        if self.victory_pending:
            stage_info = "MENACE ÉLIMINÉE"
        elif self.boss is not None:
            stage_info = (
                f"{self.boss.name}   "
                f"{max(0, self.boss.hp):03d}/{self.boss.max_hp}"
            )
        elif self.boss_spawned:
            stage_info = f"PROCHAIN BOSS : {BOSS_CLASSES[self.boss_index].name}"
        else:
            stage_info = f"VAGUE {self.wave:02d}   ·   {len(self.enemies)} HYÈNES"
        self.blit_text(canvas, stage_info, 24, CREAM, (84, 620))

        progress = min(1.0, self.stage_time / STAGE_DURATION)
        if self.boss is not None:
            progress = max(0.0, self.boss.hp / self.boss.max_hp)
            fill_color = (
                self.boss.enraged_bar_color
                if self.boss.enraged
                else self.boss.bar_color
            )
        elif self.victory_pending:
            progress = 1.0
            fill_color = GOLD
        else:
            fill_color = GOLD
        bar = pygame.Rect(84, 670, 572, 10)
        pygame.draw.rect(canvas, (8, 6, 14), bar)
        pygame.draw.rect(canvas, GOLD_DARK, bar, 1)
        pygame.draw.rect(
            canvas, fill_color, (bar.x, bar.y, int(bar.width * progress), bar.height)
        )

        controls = (
            ("ZQSD / FLÈCHES", "DÉPLACER"),
            ("MAJ", "FOCUS"),
            ("AUTO", "TIR AUTOMATIQUE"),
            ("X", "BOMBE"),
            ("ÉCHAP", "PAUSE"),
        )
        for index, (key, action) in enumerate(controls):
            y = 814 + index * 32
            self.blit_text(canvas, key, 22, GOLD, (84, y), bold=True)
            self.blit_text(canvas, action, 22, CREAM, (340, y))

    def draw_state_overlay(self, canvas):
        if self.state == "paused":
            canvas.blit(self.assets.dim_overlay, (0, 0))
            self.blit_text(
                canvas,
                "PAUSE",
                82,
                GOLD,
                (VIRTUAL_WIDTH // 2, 330),
                "center",
                bold=True,
            )
            self.blit_text(
                canvas,
                "ÉCHAP / P : REPRENDRE",
                30,
                CREAM,
                (VIRTUAL_WIDTH // 2, 455),
                "center",
            )
            self.blit_text(
                canvas,
                "R : RECOMMENCER    ·    M : MENU",
                26,
                MUTED,
                (VIRTUAL_WIDTH // 2, 505),
                "center",
            )
            return

        if self.state not in ("gameover", "win"):
            return

        canvas.blit(self.assets.dim_overlay, (0, 0))
        panel = pygame.Surface((980, 760), pygame.SRCALPHA)
        panel.fill((*PANEL_DARK, 224))
        panel_rect = panel.get_rect(center=(VIRTUAL_WIDTH // 2, 540))
        canvas.blit(panel, panel_rect)
        pygame.draw.rect(
            canvas, GOLD_DARK, panel_rect, 2, border_radius=16
        )

        if self.state == "win":
            title = "SAVANE LIBÉRÉE !"
            title_color = GOLD
            subtitle = "La reine hyène est vaincue."
        else:
            title = "GAME OVER"
            title_color = RED
            subtitle = "Les hyènes ont eu raison du chasseur."

        self.blit_text(
            canvas,
            title,
            84,
            title_color,
            (VIRTUAL_WIDTH // 2, 285),
            "center",
            bold=True,
        )
        self.blit_text(
            canvas,
            subtitle,
            26,
            MUTED,
            (VIRTUAL_WIDTH // 2, 365),
            "center",
        )
        self.blit_text(
            canvas,
            "SCORE",
            26,
            MUTED,
            (VIRTUAL_WIDTH // 2, 435),
            "center",
        )
        self.blit_text(
            canvas,
            f"{self.score:07d}",
            56,
            CREAM,
            (VIRTUAL_WIDTH // 2, 485),
            "center",
            bold=True,
        )
        self.blit_text(
            canvas,
            f"MEILLEUR SCORE : {self.hi_score:07d}",
            28,
            GOLD,
            (VIRTUAL_WIDTH // 2, 580),
            "center",
        )
        if self.new_record:
            self.blit_text(
                canvas,
                "NOUVEAU RECORD !",
                30,
                PURPLE,
                (VIRTUAL_WIDTH // 2, 635),
                "center",
                bold=True,
            )

        self.hover_replay = self.replay_rect.collidepoint(self.mouse)
        self.hover_menu = self.menu_rect.collidepoint(self.mouse)
        self.draw_button(
            canvas, self.replay_rect, "REJOUER  (R)", self.hover_replay
        )
        self.draw_button(
            canvas, self.menu_rect, "MENU  (M)", self.hover_menu
        )

    def draw_button(self, canvas, rect, label, hover):
        fill = (52, 40, 70) if hover else (26, 20, 38)
        border = GOLD if hover else GOLD_DARK
        pygame.draw.rect(canvas, fill, rect, border_radius=12)
        pygame.draw.rect(canvas, border, rect, 2, border_radius=12)
        self.blit_text(
            canvas,
            label,
            30,
            CREAM if not hover else WHITE,
            rect.center,
            "center",
            bold=True,
        )

    def blit_text(
        self, canvas, text, size, color, pos, anchor="topleft", bold=False
    ):
        surface = self.assets.text(text, size, color, bold=bold)
        rect = surface.get_rect()
        if anchor == "center":
            rect.center = (int(pos[0]), int(pos[1]))
        elif anchor == "midright":
            rect.midright = (int(pos[0]), int(pos[1]))
        else:
            rect.topleft = (int(pos[0]), int(pos[1]))
        canvas.blit(surface, rect)

    def present(self):
        self.screen.fill((0, 0, 0))
        destination = self.viewport.copy()

        if self.shake > 0.2:
            magnitude = max(1, int(self.shake * self.scale))
            destination.x += random.randint(-magnitude, magnitude)
            destination.y += random.randint(-magnitude, magnitude)

        if destination.size == (VIRTUAL_WIDTH, VIRTUAL_HEIGHT):
            self.screen.blit(self.canvas, destination.topleft)
        else:
            scaled = pygame.transform.smoothscale(
                self.canvas, destination.size
            )
            self.screen.blit(scaled, destination.topleft)
