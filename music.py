"""Musique de fond et effets sonores."""

import os

import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_PATH = os.path.join(BASE_DIR, "assets", "main_menu", "menu_theme.mp3")
BOSS_MUSIC_PATH = os.path.join(
    BASE_DIR, "assets", "characters", "hyena", "hyana_ost_boss.mp3"
)
GUN_SOUND_PATH = os.path.join(
    BASE_DIR, "assets", "characters", "player", "gun_sound.wav"
)

# Canaux réservés : 1 = fusil, 2 = grognements, 3 = entrée, 4 = défaite.
GUN_CHANNEL = 1
GROWL_CHANNEL = 2
ENTRY_CHANNEL = 3
DEFEAT_CHANNEL = 4

current_track = None
_gun_sound = None
_gun_channel = None
_sound_cache = {}


def _ensure_mixer():
    """Initialise le mixer si besoin. Retourne False si l'audio est indisponible."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.set_num_channels(max(8, pygame.mixer.get_num_channels()))
        return True
    except pygame.error:
        return False


def _play_music(path, volume, track):
    global current_track
    try:
        if not _ensure_mixer():
            return False
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)
        current_track = track
        return True
    except pygame.error:
        # Pas de carte son (ou fichier absent) : le jeu reste jouable.
        return False


def start_menu_music():
    """Musique de fond normale (menu et manche)."""
    if current_track == "menu":
        return
    _play_music(MUSIC_PATH, 0.32, "menu")


def start_boss_music():
    """Musique de boss, lancée à l'apparition du premier boss."""
    if current_track == "boss":
        return
    _play_music(BOSS_MUSIC_PATH, 0.30, "boss")


def stop_music():
    global current_track
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass
    current_track = None


def play_sound(relative_path, volume=0.5, channel=None):
    """Joue un effet sonore (avec cache).

    ``channel`` permet de réutiliser un canal dédié : le son précédent est
    alors coupé, ce qui évite que les grognements se superposent.
    """
    if not relative_path or not _ensure_mixer():
        return
    try:
        sound = _sound_cache.get(relative_path)
        if sound is None:
            sound = pygame.mixer.Sound(os.path.join(BASE_DIR, relative_path))
            _sound_cache[relative_path] = sound
        sound.set_volume(volume)
        if channel is None:
            sound.play()
        else:
            output = pygame.mixer.Channel(channel)
            output.stop()
            output.play(sound)
    except pygame.error:
        pass


def _get_gun_channel():
    """Canal réservé au fusil pour ne pas couper la musique ni les autres sons."""
    global _gun_channel
    if _gun_channel is None:
        _gun_channel = pygame.mixer.Channel(GUN_CHANNEL)
    return _gun_channel


def start_gun_loop():
    """Démarre la boucle du fusil, alignée sur le premier coup de feu.

    Le fichier contient exactement 10 détonations par seconde, comme le rythme
    de tir du joueur (PLAYER_FIRE_INTERVAL = 0.10 s) : lancer la boucle au
    moment du tir garde le son et l'animation synchronisés.
    """
    global _gun_sound
    if not _ensure_mixer():
        return
    try:
        if _gun_sound is None:
            _gun_sound = pygame.mixer.Sound(GUN_SOUND_PATH)
            _gun_sound.set_volume(0.15)
        channel = _get_gun_channel()
        # Ne pas relancer la boucle à chaque coup : sinon le son repart de
        # zéro en permanence et perd son rythme.
        if not channel.get_busy():
            channel.play(_gun_sound, loops=-1)
    except pygame.error:
        pass


def stop_gun_loop():
    """Coupe la boucle du fusil (pause, menu, fin de partie)."""
    if _gun_channel is not None:
        _gun_channel.stop()
