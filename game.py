import pygame
from constants import *

class Game:
    
    def __init__(self):
        
        self.screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
        
        self.name = pygame.display.set_caption(GAME_NAME)
        
        self.bg_image = pygame.image.load("assets/main_menu/main_menu_bg.png")
        
        self.running = True
        
        self.bg_image = pygame.transform.scale(self.bg_image, self.screen.get_size())
        
        self.play_button = pygame.image.load("assets/main_menu/play.png").convert_alpha()

        self.title_image = pygame.image.load("assets/main_menu/crazy_safari.png").convert_alpha()
    
    def keyboard(self):

        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_d]:
            self.player.move_right()
        elif keys[pygame.K_q]:
            self.player.move_left()
        elif keys[pygame.K_z]:
            self.player.move_up()
        elif keys[pygame.K_s]:
            self.player.move_down()
            
    def run(self):
        clock = pygame.time.Clock()
        menu = True
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    
            self.screen.blit(self.bg_image, (0, 0))
            self.screen.blit(self.title_image, (self.screen.get_width() // 2 - self.title_image.get_width() // 2, self.screen.get_height() // 3.5 - self.title_image.get_height() // 2))
            self.title_image = pygame.transform.scale(self.title_image, (750, 250))
            self.screen.blit(self.play_button, (self.screen.get_width() // 2 - self.play_button.get_width() // 2, self.screen.get_height() // 1.7 - self.play_button.get_height() // 2))
            self.play_button = pygame.transform.scale(self.play_button, (400, 150))
            pygame.display.flip()
            
            clock.tick(60)
        pygame.quit() 
        