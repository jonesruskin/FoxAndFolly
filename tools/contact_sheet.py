"""Tile images into a labelled contact sheet: contact_sheet.py out.png cols w img1 img2 ..."""
import sys, cv2, numpy as np
out, cols, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
ims = []
for f in sys.argv[4:]:
    im = cv2.imread(f); h = int(im.shape[0] * w / im.shape[1])
    im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
    cv2.putText(im, f.split('/')[-1][:-4], (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
    ims.append(im)
while len(ims) % cols: ims.append(np.zeros_like(ims[0]))
rows = [np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]
cv2.imwrite(out, np.vstack(rows))
