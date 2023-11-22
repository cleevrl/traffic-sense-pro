import pygame

pygame.mixer.init(16000, -16, 1, 2048)

def play_sound():

    if not pygame.mixer.music.get_busy():

        print("Play!")
        pygame.mixer.music.load('data/voice/turn_around_with_siren.mp3')
        pygame.mixer.music.play()
    
    else:
        print("SPK is busying...")