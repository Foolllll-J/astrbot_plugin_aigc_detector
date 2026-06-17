import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"
_BUNDLED_FONT = str(_FONTS_DIR / "MiSans-Regular.ttf")

_SYSTEM_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simsun.ttc",
]


def _find_cjk_font() -> str:
    try:
        from astrbot.core.utils.astrbot_path import get_astrbot_data_path

        custom = os.path.join(get_astrbot_data_path(), "font.ttf")
        if os.path.exists(custom):
            return custom
    except Exception:
        pass
    for path in _SYSTEM_CANDIDATES:
        if os.path.exists(path):
            return path
    return _BUNDLED_FONT


WIDTH = 900
MARGIN = 50
CONTENT_W = WIDTH - MARGIN * 2

BG = (249, 250, 251)
CARD_BG = (255, 255, 255)
BORDER = (229, 231, 235)
HEADER_BG = (17, 24, 39)
TEXT_PRIMARY = (17, 24, 39)
TEXT_SECONDARY = (75, 85, 99)
ACCENT = (55, 65, 81)
DONUT_BG = (229, 231, 235)
RESULT_AI = (220, 38, 38)
RESULT_SUSPECT = (217, 119, 6)
RESULT_UNKNOWN = (156, 163, 175)
RESULT_HUMAN = (34, 197, 94)

ANALYSIS_KEY_LABELS = {
    "physical_and_light": "物理与光影结构",
    "layer_and_alignment": "图层与排版对齐",
    "text_and_typography": "文字与排版逻辑",
    "artifacts_and_melting": "伪影与幻觉分析",
}


def _wrap_text(draw, text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        line = ""
        for char in paragraph:
            test_line = line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = char
        if line:
            lines.append(line)
    return lines


def _text_height(font):
    bbox = font.getbbox("A国")
    return bbox[3] - bbox[1] if bbox else 20


def _line_height(font, spacing=10):
    return _text_height(font) + spacing


def generate_report(image_path: str, data: dict) -> str:
    analysis = data.get("analysis", {})
    conclusion = data.get("conclusion", {})
    image_type = data.get("image_type", "")
    result = conclusion.get("result", "无法确定")
    aigc_score = conclusion.get("aigc_score", 0)
    summary = conclusion.get("summary", "")
    if isinstance(summary, list):
        summary = "\n".join(summary)

    try:
        aigc_score = max(0, min(100, int(float(aigc_score))))
    except (ValueError, TypeError):
        aigc_score = 0

    font_path = _find_cjk_font()
    font_body = ImageFont.truetype(font_path, 20)
    font_card_title = ImageFont.truetype(font_path, 24)
    font_section = ImageFont.truetype(font_path, 28)
    font_header = ImageFont.truetype(font_path, 40)
    font_result = ImageFont.truetype(font_path, 34)
    font_donut_pct = ImageFont.truetype(font_path, 40)
    font_summary = ImageFont.truetype(font_path, 20)

    thumb = Image.open(image_path).convert("RGB")
    tw, th_orig = thumb.size
    max_dim = 500
    if tw > th_orig:
        if tw > max_dim:
            ratio = max_dim / tw
            tw, th_orig = max_dim, int(th_orig * ratio)
    else:
        if th_orig > max_dim:
            ratio = max_dim / th_orig
            tw, th_orig = int(tw * ratio), max_dim
    if tw > CONTENT_W:
        ratio = CONTENT_W / tw
        tw, th_orig = int(tw * ratio), int(th_orig * ratio)
    thumb = thumb.resize((tw, th_orig), Image.LANCZOS)

    image_type_h = 40 if image_type else 0

    temp_img = Image.new("RGB", (WIDTH, 100), BG)
    temp_draw = ImageDraw.Draw(temp_img)

    header_h = 80
    thumb_area_h = th_orig

    sec_title_h = _line_height(font_section, 8)
    analysis_h = sec_title_h + 24
    card_gap = 36
    for key, value in analysis.items():
        lines = _wrap_text(temp_draw, value, font_body, CONTENT_W - 80)
        card_h = (
            _line_height(font_card_title, 10)
            + 12
            + len(lines) * _line_height(font_body, 8)
            + 32
        )
        analysis_h += card_h + card_gap

    conc_title_h = _line_height(font_section, 8)
    donut_radius = 75
    donut_area_w = 380
    slines = (
        _wrap_text(temp_draw, summary, font_body, CONTENT_W - donut_area_w - 60)
        if summary
        else []
    )
    summary_h = (
        (_line_height(font_summary, 6) + 12 if slines else 0)
        + len(slines) * _line_height(font_body, 8)
    )
    conc_pad_top = 48
    conc_pad_bot = 48
    conclusion_card_h = max(donut_radius * 2 + 100, conc_pad_top + 60 + summary_h + conc_pad_bot)

    total_h = int(
        header_h
        + 80
        + thumb_area_h
        + 60
        + image_type_h
        + analysis_h
        + 48
        + conc_title_h
        + 24
        + conclusion_card_h
        + 60
    )

    img = Image.new("RGB", (WIDTH, total_h), BG)
    draw = ImageDraw.Draw(img)
    y = 0

    # Header
    draw.rounded_rectangle([0, 0, WIDTH, header_h], radius=0, fill=HEADER_BG)
    title_bbox = draw.textbbox((0, 0), "AIGC 检测报告", font=font_header)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(
        ((WIDTH - title_w) / 2, (header_h - 36) / 2),
        "AIGC 检测报告",
        font=font_header,
        fill=(255, 255, 255),
    )
    y = header_h + 80

    # Thumbnail
    tx = (WIDTH - tw) // 2
    img.paste(thumb, (tx, y))
    y += th_orig + 60

    # Image type tag
    if image_type:
        type_text = f"识别类型：{image_type}"
        draw.text((WIDTH // 2, y + 8), type_text, font=font_body, fill=TEXT_SECONDARY, anchor="mm")
        y += image_type_h

    # Analysis section
    draw.text((MARGIN, y), "检测分析", font=font_section, fill=TEXT_PRIMARY)
    y += sec_title_h + 24

    for key, value in analysis.items():
        lines = _wrap_text(draw, value, font_body, CONTENT_W - 80)
        card_h = (
            _line_height(font_card_title, 10)
            + 12
            + len(lines) * _line_height(font_body, 8)
            + 32
        )

        draw.rounded_rectangle(
            [MARGIN, y, MARGIN + CONTENT_W, y + card_h],
            radius=12,
            fill=CARD_BG,
            outline=BORDER,
            width=1,
        )
        draw.rounded_rectangle(
            [MARGIN + 18, y + 14, MARGIN + 21, y + card_h - 14],
            radius=2,
            fill=ACCENT,
        )

        ix = MARGIN + 40
        iy = y + 16
        card_label = ANALYSIS_KEY_LABELS.get(key, key)
        draw.text((ix, iy), card_label, font=font_card_title, fill=TEXT_PRIMARY)
        iy += _line_height(font_card_title, 10) + 12
        for line in lines:
            draw.text((ix, iy), line, font=font_body, fill=TEXT_SECONDARY)
            iy += _line_height(font_body, 8)
        y += card_h + card_gap

    y += 24

    # Conclusion section
    draw.text((MARGIN, y), "检测结论", font=font_section, fill=TEXT_PRIMARY)
    y += conc_title_h + 24

    result_color = RESULT_SUSPECT
    donut_color = RESULT_SUSPECT
    result_colors = {
        "AI生成": (RESULT_AI, RESULT_AI),
        "疑似AI生成": (RESULT_SUSPECT, RESULT_SUSPECT),
        "无法确定": (RESULT_UNKNOWN, RESULT_UNKNOWN),
        "非AI生成": (RESULT_HUMAN, RESULT_HUMAN),
    }
    if result in result_colors:
        result_color, donut_color = result_colors[result]

    slines = (
        _wrap_text(draw, summary, font_body, CONTENT_W - donut_area_w - 60)
        if summary
        else []
    )
    summary_h = (
        (_line_height(font_summary, 6) + 12 if slines else 0)
        + len(slines) * _line_height(font_body, 8)
    )
    conclusion_card_h = max(donut_radius * 2 + 100, conc_pad_top + 60 + summary_h + conc_pad_bot)

    draw.rounded_rectangle(
        [MARGIN, y, MARGIN + CONTENT_W, y + conclusion_card_h],
        radius=12,
        fill=CARD_BG,
        outline=BORDER,
        width=1,
    )

    # Donut chart
    cx = MARGIN + donut_area_w // 2
    cy = y + conclusion_card_h // 2
    thickness = 16
    draw.arc(
        [cx - donut_radius, cy - donut_radius, cx + donut_radius, cy + donut_radius],
        0, 360,
        fill=DONUT_BG, width=thickness,
    )
    end_angle = -90 + 360 * aigc_score / 100
    draw.arc(
        [cx - donut_radius, cy - donut_radius, cx + donut_radius, cy + donut_radius],
        -90, end_angle,
        fill=donut_color, width=thickness,
    )
    pct_text = f"{aigc_score}%"
    draw.text(
        (cx, cy), pct_text,
        font=font_donut_pct, fill=TEXT_PRIMARY, anchor="mm",
    )

    # Right side
    rx = MARGIN + donut_area_w + 36
    ry = y + conc_pad_top
    draw.text((rx, ry), result, font=font_result, fill=result_color)
    ry += _line_height(font_result, 12)

    if slines:
        ry += 24
        draw.text((rx, ry), "主要依据", font=font_summary, fill=TEXT_SECONDARY)
        ry += _line_height(font_summary, 6) + 12
        for line in slines:
            draw.text((rx, ry), line, font=font_body, fill=TEXT_SECONDARY)
            ry += _line_height(font_body, 8)

    output_path = str(Path(__file__).resolve().parent.parent / "report_output.png")
    img.save(output_path, "PNG")
    return output_path
