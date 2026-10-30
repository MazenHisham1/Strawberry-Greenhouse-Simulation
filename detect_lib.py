import numpy as np, cv2

SEED = (325, 350)   # a pixel on the foreground leaf (image is 640x480)

def analyse(path):
    bgr = cv2.imread(path)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = [hsv[:, :, i].astype(int) for i in range(3)]
    green  = (h >= 40) & (h <= 90) & (s > 60)
    yellow = (h >= 20) & (h < 40) & (s > 80)
    whitish = (s < 50) & (v > 180)
    whitish[:200, :] = False   # ignore the sky at the top of the frame
    leaf = (green | yellow | whitish).astype(np.uint8)
    n, lab = cv2.connectedComponents(leaf)
    k = lab[SEED[1], SEED[0]]
    if k == 0:
        return None
    comp = (lab == k).astype(np.uint8)
    cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(max(cnts, key=cv2.contourArea))
    hm = np.zeros(comp.shape, np.uint8); cv2.fillConvexPoly(hm, hull, 1); hm = hm.astype(bool)
    area = hm.sum()
    yel = (yellow & hm).sum() / max(1, ((green | yellow) & hm).sum())
    white = (whitish & hm).sum() / area
    spot = ((((h < 20) | (h > 170)) & (s > 80) & (v < 150)) & hm).sum() / area
    return dict(yellow=yel, white=white, spot=spot)

def classify(f):
    if f is None: return "no_plant_found"
    if f["yellow"] > 0.5: return "yellowing"
    if f["white"] > 0.05: return "powdery_mildew"
    if f["spot"] > 0.008: return "leaf_spot"
    return "healthy"
