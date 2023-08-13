import json
import os


def obj_uniqueify(input_path: str, output_path: str):
    with open(input_path) as f:
        dat = f.read()


    counts: dict[str, int] = {}

    out = []
    for line in dat.split("\n"):
        line = line.strip()
        if line.startswith("o "):
            if "_" in line:
                try:
                    int(line.split("_")[-1])
                    out.append(line)
                    continue
                except ValueError:
                    pass
            object_name = line.removeprefix("o ").strip()
            idx = counts.get(object_name, 0)
            counts[object_name] = idx + 1
            out.append(f"o {object_name}_{idx}")
        else:
            out.append(line)

    with open(output_path, "w") as f:
        f.write("\n".join(out))

if __name__ == "__main__":
    for name in os.listdir("input"):
        obj_uniqueify(f"input/{name}", f"output/{name}")