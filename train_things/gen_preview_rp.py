import os
import tempfile


def gen(color: str):
    tmp_dir = tempfile.mkdtemp()
    print("Working directory:", tmp_dir)

    cmd = f"cp -r \"rp_base\" \"{tmp_dir}\""
    os.system(cmd)

    dst = os.path.join(tmp_dir, "rp_base", "assets", "create", "textures", "block")
    print(dst)

    copies = {
        "single_outline.png": "andesite_casing.png",
        "single_outline_white.png": "brass_casing.png",
        "connected_full.png": "andesite_casing_connected.png",
        "connected_full_white.png": "brass_casing_connected.png",
        "boiler_front.png": "../../../../pack.png"
    }

    for frm, to in copies.items():
        frm_path = os.path.join("output", "colorized", color, frm.replace("$", color))
        to_path = os.path.join(dst, to)
        cmd = f"cp \"{frm_path}\" \"{to_path}\""
        os.system(cmd)

    with open(os.path.join(tmp_dir, "rp_base", "pack.mcmeta"), "r") as f:
        contents = f.read()
    with open(os.path.join(tmp_dir, "rp_base", "pack.mcmeta"), "w") as f:
        f.write(contents.replace("<REPLACE>", color))

    os.system(f"cd \"{os.path.join(tmp_dir, 'rp_base')}\"; zip -r ../preview_rp.zip .")

    os.system(f"cp \"{os.path.join(tmp_dir, 'preview_rp.zip')}\" \"preview_rps/train_preview_{color}.zip\"")

    os.system(f"rm -r \"{tmp_dir}\"")


colors = [s for s in os.listdir("output/colorized") if os.path.isdir(os.path.join("output/colorized", s))]
print("Colors:\n\t" + ("\n\t".join(colors)))
for s in colors:
    print(s)
    gen(s)
