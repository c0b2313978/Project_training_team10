import os

def read_map_data(file_path: str) -> tuple[list[list[str]], str]:
    """
    map_txt を読み、[grid] と [info] を処理する。
    - [grid] は # と . のみ（検証は最小限）
    - [info] は json=xxx.json だけを見る
    返り値: (grid: List[List[str]], json_path: str)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    section = None
    grid = []
    json_path = ""

    for line in lines:
        line = line.rstrip("\n")
        if not line:
            continue

        if line == "[grid]":
            section = 'grid'
            continue
        elif line == "[info]":
            section = 'info'
            continue

        if section == 'grid':
            grid.append(list(line))
            continue
        elif section == 'info':
            if line.startswith("json="):
                json_path = line.split("=", 1)[1].strip()
                # Normalize path separators to be OS-independent
                json_path = json_path.replace('\\', os.sep)
                continue

    return grid, json_path