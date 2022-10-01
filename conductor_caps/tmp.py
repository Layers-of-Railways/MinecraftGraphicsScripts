import os.path

import pygame
pygame.init()

if __name__ == "__main__": pass

for path_0 in ['cyan_conductor_cap.png', 'yellow_conductor_cap.png', 'black_conductor_cap.png', 'pink_conductor_cap.png', 'white_conductor_cap.png', 'orange_conductor_cap.png', 'green_conductor_cap.png', 'light_gray_conductor_cap.png', 'lime_conductor_cap.png', 'light_blue_conductor_cap.png', 'gray_conductor_cap.png', 'purple_conductor_cap.png', 'brown_conductor_cap.png', 'red_conductor_cap.png', 'magenta_conductor_cap.png', 'blue_conductor_cap.png']:
    path = os.path.join("/home/sam/PycharmProjects/MinecraftGraphicsScripts/conductor_caps/caps_edited_bkp", path_0)
    print(path)
    im = pygame.image.load(path)
    for x in range(im.get_width()):
        for y in range(im.get_height()):
            col = list(im.get_at((x, y)))
            if col[3] != 0:
                col[3] = 255
            if 30 < y < 50:
                col = (0, 0, 0, 0)
            im.set_at((x, y), col)
    pygame.image.save(im, os.path.join("/home/sam/PycharmProjects/MinecraftGraphicsScripts/conductor_caps/caps_edited", path_0))
