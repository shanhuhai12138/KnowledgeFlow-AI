"""T3.1 截图留档主色分析：验证深浅色切换与页面渲染（非空白）"""
import os
from PIL import Image

d = "docs/verify/shots"
for f in sorted(os.listdir(d)):
    im = Image.open(os.path.join(d, f)).convert("RGB")
    colors = sorted(im.getcolors(maxcolors=100000), reverse=True)[:1]
    c, (r, g, b) = colors[0]
    print(f"{f:34s} 主色 #{r:02x}{g:02x}{b:02x} ({c / im.width / im.height * 100:.0f}%)")
