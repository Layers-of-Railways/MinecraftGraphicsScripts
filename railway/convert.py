import pygame
import os
import time

pygame.init()

template_names = {
    "standard_track_mip_$.png": ("portal_track_mip_$.png", True),
    "standard_track_$.png": ("portal_track_$.png", False)
}

styles = [s for s in os.listdir("base_tracks") if os.path.isdir(os.path.join("base_tracks", s))]
print(f"Converting: {styles}")

for style in styles:
    print(f"Beginning {style}...")
    start = time.time()
    in_path = os.path.join("base_tracks", style)
    portal_path = os.path.join("portal_tracks", style)
    out_path = os.path.join("combined_tracks", style)
    os.makedirs(portal_path, exist_ok=True)
    os.makedirs(out_path, exist_ok=True)

    for in_name, dat in template_names.items():
        out_name, mip = dat
        in_full = os.path.join(in_path, in_name.replace("$", style))
        portal_full = os.path.join(portal_path, out_name.replace("$", style))

        out_base_full = os.path.join(out_path, in_name.replace("$", style))
        out_portal_full = os.path.join(out_path, out_name.replace("$", style))

        img = pygame.image.load(in_full)
        if mip:
            over = pygame.image.load("portal_overlay/portal_track_mip_overlay.png")
            img.blit(over, (0, 0))
        else:
            over = pygame.image.load("portal_overlay/portal_track_overlay.png")
            img.blit(over, (0, 0))

            img.fill((0, 0, 0, 0), pygame.Rect(22, 0, 4, 4))    # Remove extra square
            img.fill((0, 0, 0, 0), pygame.Rect(31, 21, 1, 11))  # Remove palette marker

            clone_from = (0, 8)
            clone_size = (22, 4)
            clone_to = (0, 28)
            for xo in range(clone_size[0]):
                for yo in range(clone_size[1]):
                    col = img.get_at((clone_from[0]+xo, clone_from[1]+yo))
                    img.set_at((clone_to[0]+xo, clone_to[1]+yo), col)

        pygame.image.save(img, portal_full)
        os.makedirs(os.path.dirname(out_base_full), exist_ok=True)
        os.makedirs(os.path.dirname(out_portal_full), exist_ok=True)
        cmd1 = f"cp \"{in_full}\" \"{out_base_full}\""
        cmd2 = f"cp \"{portal_full}\" \"{out_portal_full}\""
        os.system(cmd1)
        os.system(cmd2)

    os.system(f"cp \"base_tracks/{style}/standard_track_crossing_{style}.png\" \"combined_tracks/{style}/standard_track_crossing_{style}.png\"")

    print(f"Finished {style} in {round((time.time()-start)/1000, 4)} ms...\n")
os.system("zip -r combined_tracks.zip ./combined_tracks")
