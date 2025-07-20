def encode_oriented_gauss_code(walk):
    label_map = {}
    code = []
    next_label = 1

    for i, v in enumerate(walk[:-1]):
        if v not in label_map:
            label_map[v] = next_label
            next_label += 1

        label = label_map[v]
        strand = label
        over = "+>" if i % 2 == 0 else "-<"
        code.append(f"{over}{strand}")

    return code

