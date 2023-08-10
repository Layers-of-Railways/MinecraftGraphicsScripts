import json
import os


def auto_uv(input_path: str, output_path: str):
    with open(input_path) as f:
        dat = json.load(f)

    dat: dict[str, ...]
    elements: list[dict[str, ...]] = dat["elements"]

    for element in elements:
        if "rotation" in element and "angle" in element["rotation"] and element["rotation"]["angle"] != 0:
            continue
        frm: tuple[float, float, float] = element["from"]
        to: tuple[float, float, float] = element["to"]
        faces: dict[str, dict[str, ...]] = element["faces"]
        fx = frm[0] % 16
        fy = frm[1] % 16
        fz = frm[2] % 16

        tx = fx + (to[0] - frm[0])
        ty = fy + (to[1] - frm[1])
        tz = fz + (to[2] - frm[2])

        for face_name, face in faces.items():
            uv0: tuple[float, float] = face["uv"][:2]
            uv1: tuple[float, float] = face["uv"][2:]
            if face_name == "south":
                # make uv0 and uv1
                # with (0, 0) being the top left corner and (16, 16) being the bottom right corner
                # y is the vertical axis
                uv0 = (fx, 16 - ty)
                uv1 = (tx, 16 - fy)
            elif face_name == "north":
                uv0 = (16 - tx, 16 - ty)
                uv1 = (16 - fx, 16 - fy)
            elif face_name == "west":
                uv0 = (fz, 16 - ty)
                uv1 = (tz, 16 - fy)
            elif face_name == "east":
                uv0 = (16 - tz, 16 - ty)
                uv1 = (16 - fz, 16 - fy)
            elif face_name == "up" or face_name == "down":
                uv0 = (fx, fz)
                uv1 = (tx, tz)
            face["uv"] = uv0 + uv1
            if "rotation" in face:
                del face["rotation"]

    with open(output_path, "w") as f:
        json.dump(dat, f, indent="\t")

if __name__ == "__main__":
    auto_uv("input.json", "output.json")
    for name in os.listdir("input"):
        auto_uv(f"input/{name}", f"output/{name}")