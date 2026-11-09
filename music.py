import pygame

pygame.mixer.init()
current_music = pygame.mixer.music.load("assets\main_menu\menu_theme.mp3")
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.4)