points = []
mean_hue = 0
global_eps = 10


def select(mat, i0, j0, val, eps):
    global mean_hue
    mat = mat.astype(int)
    que = [[i0, j0]]
    mean_hue = 0
    while len(que) > 0:
        top = que[0]
        que = que[1:]
        i = top[0]
        j = top[1]
        if abs(mat[i, j] - val) < eps:
            mean_hue += mat[i, j]
            points.append([i, j])
            mat[i, j] = -114514  # 破坏性选取法
            if i > 0:
                que.append([i - 1, j])
            if i < mat.shape[0] - 1:
                que.append([i + 1, j])
            if j > 0:
                que.append([i, j - 1])
            if j < mat.shape[1] - 1:
                que.append([i, j + 1])
    return mat == -114514


def wand(mat, i0, j0):
    global points
    points = []
    val = mat[i0, j0]
    mat = select(mat, i0, j0, val, global_eps)
    return points, mat, mean_hue / len(points)


def search(mat, hue, seed_x, seed_y):
    eps = global_eps / 2  # 防止漂变
    r = 0
    while r < 400:  # 单步追踪距离
        if seed_x - r < 0 or seed_y - r < 0 or seed_y + r >= mat.shape[0] or seed_x + r >= mat.shape[1]: break
        j0 = seed_x - r
        j1 = seed_x + r
        for i in range(seed_y - r, seed_y + r):
            if abs(mat[i, j0] - hue) < eps: return wand(mat, i, j0)
            if abs(mat[i, j1] - hue) < eps: return wand(mat, i, j1)
        i0 = seed_y - r
        i1 = seed_y + r
        for j in range(seed_x - r, seed_x + r):
            if abs(mat[i0, j] - hue) < eps: return wand(mat, i0, j)
            if abs(mat[i1, j] - hue) < eps: return wand(mat, i1, j)
        r += 1
    return None, None, None
