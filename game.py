import pygame
from constants import *

class Game:
    
    def __init__(self):
        
        self.screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
        
        self.name = pygame.display.set_caption(GAME_NAME)
        
        self.running = True
    
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
        while self.running :
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit() 
                    
                    
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit() 
                    

            pygame.display.flip()
            clock.tick(60)