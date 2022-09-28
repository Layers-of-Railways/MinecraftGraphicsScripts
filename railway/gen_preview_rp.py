import os
import tempfile


def gen(style: str):
    tmp_dir = tempfile.mkdtemp()
    print("Working directory:", tmp_dir)

    cmd = f"cp -r \"rp_base\" \"{tmp_dir}\""
    os.system(cmd)

    dst = os.path.join(tmp_dir, "rp_base", "assets", "create", "textures", "block")
    print(dst)

    copies = {
        "portal_track_$.png": "portal_track.png",
        "portal_track_mip_$.png": "portal_track_mip.png",
        "standard_track_$.png": "standard_track.png",
        "standard_track_crossing_$.png": "standard_track_crossing.png",
        "standard_track_mip_$.png": "standard_track_mip.png"
    }

    for frm, to in copies.items():
        frm_path = os.path.join("combined_tracks", style, frm.replace("$", style))
        to_path = os.path.join(dst, to)
        cmd = f"cp \"{frm_path}\" \"{to_path}\""
        os.system(cmd)

    os.system(f"cd \"{os.path.join(tmp_dir, 'rp_base')}\"; zip -r ../preview_rp.zip .")

    os.system(f"cp \"{os.path.join(tmp_dir, 'preview_rp.zip')}\" \"preview_rps/rr_preview_{style}.zip\"")

    os.system(f"rm -r \"{tmp_dir}\"")


styles = [s for s in os.listdir("base_tracks") if os.path.isdir(os.path.join("base_tracks", s))]
print("Styles:\n\t" + ("\n\t".join(styles)))
for s in styles:
    print(s)
    gen(s)
