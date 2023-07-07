import os

if __name__ == "__main__":
    all_names = []
    for entry in os.scandir(input("dir: ")):
        if entry.is_dir():
            all_names.append(entry.name)
    all_names.sort()
    indent = "            "
    out = ""
    for name in all_names:
        out += indent + '"' + name + '",\n'
    out = out[:-2]
    print(out)