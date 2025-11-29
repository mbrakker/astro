# -*- coding: utf-8 -*-
"""
Tarot Layout - Keep Card Texture (v1.3.8)

Изменения v1.3.8:
- Для расклада из 1 карты добавлен вертикальный джиттер (jy) как у центральной карты в three.
- Введён MIN_ANGLE_VISUAL = 0.25°: при angle_jitter_deg>0 гарантируем небольшой наклон даже если рандом дал почти 0°.
"""

import os
import random
import argparse
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple

import numpy as np
import cv2

# -------------------- Константы --------------------
HARDCODED_ROI: Tuple[int, int, int, int] = (510, 176, 865, 627)  # (x1,y1,x2,y2)
ROI_INSET = 6
GAP_PX = 12
FIT_SCALE = 0.98
DEFAULT_ANGLE_JITTER_DEG = 1.0
DEFAULT_POS_JITTER_PX = 4
ROW_X_JITTER_PX = 8
ROW_Y_JITTER_PX = 2

# Минимально заметный наклон (для 1-карточного расклада)
MIN_ANGLE_VISUAL = 0.25  # градусы

# Физика карты
REAL_CARD_HEIGHT_MM = 120.0
CARD_THICKNESS_MM = 2.0

# Тени
AO_RING_PX = 1
AO_BLUR = 2
AO_OPACITY = 0.1
AO_GAMMA = 1.55

SHADOW_BLUR = 9
SHADOW_OPACITY = 0.1
LIGHT_PCT = 0.95
LIGHT_VECTOR_BASE_PX = 9
DEFAULT_SHADOW_OFFSET = (7, 7)

# Края
EDGE_FEATHER_PX = 2
EDGE_NOISE_STRENGTH = 0.04

# Подавление белой рамки по кромке
WHITE_BORDER_WIDTH = 3
WHITE_BORDER_SUPPRESS = 0.15

# Зерно
ADD_GRAIN_DEFAULT = False
GRAIN_STRENGTH_DEFAULT = 0.0

NO_RESAMPLE_TOLERANCE = 0.05
ALLOW_UPSCALE_DEFAULT = False

# Light wrap
WRAP_RADIUS = 7
WRAP_AMOUNT = 0.10

# LAB match
LAB_BLEND = 0.08

# Подсвет кромки (лаковый блик)
REFLECT_AMOUNT = 0.08

# Виньетка
VIGNETTE_STRENGTH = 0.08

# Scarlet table set
SCARLET_TABLE_TOTAL = 7
SCARLET_TABLE_NUMBER = 0

# -------------------- ImageMagick helpers --------------------

def find_imagemagick_bin() -> str:
    for cmd in ("magick", "convert"):
        if shutil.which(cmd):
            return cmd
    raise RuntimeError(
        "ImageMagick не найден. Установите 'imagemagick' и убедитесь, что команда 'magick' или 'convert' в PATH."
    )


def rotate_with_imagemagick(input_png: str, angle_deg: float, output_png: str, im_bin: str):
    cmd = [
        im_bin, input_png,
        "-alpha", "on",
        "-background", "none",
        "-virtual-pixel", "transparent",
        "-filter", "Lanczos",
        "-define", "filter:lobes=3",
        "-define", "filter:blur=0.985",
        "-rotate", str(angle_deg),
        "PNG32:" + output_png,
    ]
    subprocess.run(cmd, check=True)

# -------------------- Геометрия --------------------

def inset_roi(roi: Tuple[int, int, int, int], inset: int) -> Tuple[int, int, int, int]:
    x1, y1, x2, y2 = roi
    return (x1 + inset, y1 + inset, x2 - inset, y2 - inset)


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def compute_slot(roi: Tuple[int, int, int, int]):
    x1, y1, x2, y2 = inset_roi(roi, ROI_INSET)
    roi_w, roi_h = (x2 - x1), (y2 - y1)
    slot_w = int(((roi_w - 4 * GAP_PX) / 3.0) * FIT_SCALE)
    slot_h = int(((roi_h - 2 * GAP_PX) / 1.0) * FIT_SCALE)
    cx_left  = x1 + GAP_PX + int(slot_w * 0.5)
    cx_mid   = cx_left + GAP_PX + slot_w
    cx_right = cx_mid  + GAP_PX + slot_w
    cy = y1 + roi_h // 2
    centers = [(cx_left, cy), (cx_mid, cy), (cx_right, cy)]
    return slot_w, slot_h, x1, y1, (x2, y2), centers


def clamp_center_to_roi(center_xy: Tuple[int, int], src_wh: Tuple[int, int], roi: Tuple[int, int, int, int]) -> Tuple[int, int]:
    cx, cy = center_xy
    w, h = src_wh
    x1, y1, x2, y2 = inset_roi(roi, ROI_INSET)
    cx = clamp(cx, x1 + w // 2, x2 - w // 2)
    cy = clamp(cy, y1 + h // 2, y2 - h // 2)
    return cx, cy

# -------------------- Тени --------------------

def estimate_light_vector(dst_bgr: np.ndarray,
                          roi: Tuple[int, int, int, int],
                          pct: float = LIGHT_PCT,
                          base_px: int = LIGHT_VECTOR_BASE_PX) -> Tuple[int, int]:
    try:
        lab = cv2.cvtColor(dst_bgr, cv2.COLOR_BGR2LAB)
        L = lab[:, :, 0].astype(np.float32)
        thr = np.quantile(L, pct)
        mask = (L >= thr).astype(np.uint8)
        ys, xs = np.where(mask > 0)
        if xs.size < 10:
            raise ValueError("Not enough bright pixels")
        x_b = float(xs.mean()); y_b = float(ys.mean())
        rx1, ry1, rx2, ry2 = inset_roi(roi, ROI_INSET)
        cx = (rx1 + rx2) * 0.5; cy = (ry1 + ry2) * 0.5
        vec = np.array([cx - x_b, cy - y_b], dtype=np.float32)
        n = float(np.linalg.norm(vec))
        if n < 1e-3:
            return DEFAULT_SHADOW_OFFSET
        vec = vec / n
        off = vec * float(base_px)
        ox = int(np.clip(round(off[0]), -18, 18))
        oy = int(np.clip(round(off[1]), -18, 18))
        if ox == 0 and oy == 0:
            ox, oy = DEFAULT_SHADOW_OFFSET
        return (ox, oy)
    except Exception:
        return DEFAULT_SHADOW_OFFSET


def place_mask_on_canvas(mask_local: np.ndarray, canvas_shape: Tuple[int, int], x: int, y: int) -> np.ndarray:
    H, W = canvas_shape
    h, w = mask_local.shape[:2]
    mask_full = np.zeros((H, W), dtype=np.uint8)
    x0 = max(0, x); y0 = max(0, y)
    x1 = min(W, x + w); y1 = min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return mask_full
    sx0, sy0 = x0 - x, y0 - y
    sx1, sy1 = sx0 + (x1 - x0), sy0 + (y1 - y0)
    mask_full[y0:y1, x0:x1] = mask_local[sy0:sy1, sx0:sx1]
    return mask_full


def add_contact_shadow(dst_bgr: np.ndarray,
                       mask_full: np.ndarray,
                       ring_px: int = AO_RING_PX,
                       blur: int = AO_BLUR,
                       opacity: float = AO_OPACITY,
                       gamma: float = AO_GAMMA) -> np.ndarray:
    k = ring_px * 2 + 1
    kernel = np.ones((k, k), np.uint8)
    dil = cv2.dilate(mask_full, kernel, iterations=1)
    ring = cv2.subtract(dil, mask_full)
    b = blur + (1 - blur % 2)
    ring_blur = cv2.GaussianBlur(ring, (b, b), 0)
    dark = (ring_blur.astype(np.float32) / 255.0)
    dark = np.power(dark, gamma) * (opacity * 85)
    out = dst_bgr.astype(np.float32)
    for c in range(3):
        out[:, :, c] = np.clip(out[:, :, c] - dark, 0, 255)
    return out.astype(np.uint8)


def add_directional_shadow(dst_bgr: np.ndarray,
                           mask_full: np.ndarray,
                           offset: Tuple[int, int],
                           blur: int = SHADOW_BLUR,
                           opacity: float = SHADOW_OPACITY) -> np.ndarray:
    ox, oy = offset
    h, w = mask_full.shape[:2]
    T = np.float32([[1, 0, ox], [0, 1, oy]])
    shifted = cv2.warpAffine(mask_full, T, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    k = blur + (1 - blur % 2)
    blurred = cv2.GaussianBlur(shifted, (k, k), 0)
    dist = cv2.distanceTransform((mask_full>0).astype(np.uint8), cv2.DIST_L2, 3)
    dist = cv2.normalize(dist, None, 0, 1, cv2.NORM_MINMAX)
    penumbra = cv2.GaussianBlur(dist, (k, k), 0)
    alpha = (blurred.astype(np.float32) / 255.0) * (0.55 + 0.45*penumbra)
    alpha = np.power(alpha, 1.2) * (opacity * 95)
    noise = (np.random.rand(*alpha.shape) - 0.5) * 0.15
    alpha = np.clip(alpha + noise, 0, 1)
    out = dst_bgr.astype(np.float32)
    for c in range(3):
        out[:, :, c] = out[:, :, c] * (1 - alpha)
    return np.clip(out, 0, 255).astype(np.uint8)

# -------------------- Light wrap / LAB match / Edge reflect --------------------

def edge_band(mask: np.ndarray, width: int = 2) -> np.ndarray:
    k = width*2 + 1
    dil = cv2.dilate(mask, np.ones((k,k), np.uint8), iterations=1)
    ring = cv2.subtract(dil, mask)
    return ring


def light_wrap_local(canvas_region: np.ndarray, bg_region: np.ndarray, mask_region: np.ndarray,
                     radius: int = WRAP_RADIUS, amount: float = WRAP_AMOUNT) -> np.ndarray:
    r = radius + (1 - radius % 2)
    bg_blur = cv2.GaussianBlur(bg_region, (r, r), 0)
    ring = edge_band(mask_region, width=2)
    ring_f = (ring.astype(np.float32)/255.0)[:, :, None]
    out = canvas_region.astype(np.float32)
    out = out*(1.0 - amount*ring_f) + bg_blur*(amount*ring_f)
    if EDGE_NOISE_STRENGTH > 0:
        noise = np.random.randn(*ring_f.shape).astype(np.float32)
        out += noise * (EDGE_NOISE_STRENGTH*20.0) * ring_f
    return np.clip(out, 0, 255).astype(np.uint8)


def lab_match(src_bgr: np.ndarray, ref_bgr: np.ndarray, blend: float = LAB_BLEND) -> np.ndarray:
    if src_bgr.size == 0 or ref_bgr.size == 0:
        return src_bgr
    if min(src_bgr.shape[:2]) < 2 or min(ref_bgr.shape[:2]) < 2:
        return src_bgr
    src_lab = cv2.cvtColor(src_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    ref_lab = cv2.cvtColor(ref_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    for i in range(3):
        s = src_lab[:, :, i]
        r = ref_lab[:, :, i]
        s_mean, s_std = float(s.mean()), float(s.std())
        r_mean, r_std = float(r.mean()), float(r.std())
        s_std = max(s_std, 1e-6)
        r_std = max(r_std, 1e-6)
        src_lab[:, :, i] = (s - s_mean) * (r_std / s_std) + r_mean
    matched = cv2.cvtColor(np.clip(src_lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    return cv2.addWeighted(src_bgr, 1 - blend, matched, blend, 0)


def add_reflect_edge(region_bgr: np.ndarray, mask_u8: np.ndarray, amount: float = REFLECT_AMOUNT) -> np.ndarray:
    band = edge_band(mask_u8, 2)
    band_f = (band.astype(np.float32)/255.0)[:, :, None]
    bright = cv2.GaussianBlur(region_bgr, (3, 3), 0) + 30
    out = region_bgr.astype(np.float32) * (1 - amount*band_f) + bright.astype(np.float32) * (amount*band_f)
    return np.clip(out, 0, 255).astype(np.uint8)


def suppress_white_border(region_bgr: np.ndarray, bg_region_bgr: np.ndarray, mask_u8: np.ndarray,
                          width: int = WHITE_BORDER_WIDTH, strength: float = WHITE_BORDER_SUPPRESS) -> np.ndarray:
    """Слегка приглушаем «светящуюся» белую рамку на узкой полосе по краю карты."""
    if strength <= 0 or width <= 0:
        return region_bgr

    er_k = max(1, width)
    er = cv2.erode(mask_u8, np.ones((er_k, er_k), np.uint8), iterations=1)
    inner_band = cv2.subtract(mask_u8, er)

    hsv = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)
    white_like = ((V > 200) & (S < 60)).astype(np.uint8) * 255

    band = cv2.bitwise_and(inner_band, white_like)
    if band.max() == 0:
        return region_bgr

    lab = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[:, :, 0]

    k = width*2 + 1
    band_soft = cv2.GaussianBlur(band, (k, k), 0).astype(np.float32) / 255.0

    L = L * (1.0 - strength * band_soft)
    lab[:, :, 0] = L
    dimmed = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)

    bg_mix = cv2.GaussianBlur(bg_region_bgr, (3, 3), 0).astype(np.float32)
    out = dimmed * (1.0 - 0.25*band_soft[:, :, None]) + bg_mix * (0.25*band_soft[:, :, None])
    return np.clip(out, 0, 255).astype(np.uint8)

# -------------------- Grain & Vignette --------------------

def add_camera_grain_bg_only(img_bgr: np.ndarray, mask_union: np.ndarray, strength: float) -> np.ndarray:
    if strength <= 0:
        return img_bgr
    h, w = img_bgr.shape[:2]
    noise = np.random.randn(h, w, 3).astype(np.float32)
    out = img_bgr.astype(np.float32)
    inv = (mask_union == 0)[:, :, None].astype(np.float32)
    out += noise * (strength * 255.0) * inv
    return np.clip(out, 0, 255).astype(np.uint8)


def add_soft_vignette(img_bgr: np.ndarray, strength: float = VIGNETTE_STRENGTH) -> np.ndarray:
    if strength <= 0:
        return img_bgr
    h, w = img_bgr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w/2.0, h/2.0
    r = np.sqrt((xx-cx)**2 + (yy-cy)**2)
    r = r / (r.max()+1e-6)
    v = 1 - (r**1.5) * strength
    v = v.astype(np.float32)
    out = img_bgr.astype(np.float32)
    for c in range(3):
        out[:, :, c] *= v
    return np.clip(out, 0, 255).astype(np.uint8)

# -------------------- Reverse path helper --------------------

def map_card_path_with_reverse(path: str, is_reversed: bool) -> str:
    """Возвращаем путь к нужной картинке. Если reversed-вариант отсутствует — используем прямую, логируем варнинг."""
    if not is_reversed:
        return path
    norm = Path(path).as_posix()
    base_dir, base_name = os.path.split(norm)
    root, ext = os.path.splitext(base_name)
    rev_dir = os.path.join(base_dir, "reverse")
    rev_name = f"{root}_reversed{ext}"
    rev_path = os.path.join(rev_dir, rev_name)
    if not os.path.exists(rev_path):
        print(f"[reverse-missing][fallback] Нет файла перевёрнутой карты: {rev_path}. Использую upright: {path}")
        return path  # graceful-fallback
    return rev_path

# -------------------- Основной конвейер --------------------

def compose_three_cards_keep_texture(seed_path: str,
                                     card_paths: List[str],
                                     out_path: str,
                                     reversed_flags: List[bool],
                                     angle_jitter_deg: float,
                                     pos_jitter_px: int,
                                     allow_upscale: bool,
                                     add_grain: bool,
                                     grain_strength: float) -> None:
    assert len(card_paths) == 3, "Нужно ровно 3 карты."
    if reversed_flags is None or len(reversed_flags) != 3:
        reversed_flags = [False, False, False]

    im_bin = find_imagemagick_bin()

    base_bgr = cv2.imread(seed_path, cv2.IMREAD_COLOR)
    if base_bgr is None:
        raise FileNotFoundError(f"Не удалось открыть фон: {seed_path}")
    H, W = base_bgr.shape[:2]

    shadow_offset = estimate_light_vector(base_bgr, HARDCODED_ROI, pct=LIGHT_PCT, base_px=LIGHT_VECTOR_BASE_PX)
    slot_w, slot_h, *_ , centers = compute_slot(HARDCODED_ROI)

    row_dx = random.randint(-ROW_X_JITTER_PX, ROW_X_JITTER_PX)
    row_dy = random.randint(-ROW_Y_JITTER_PX, ROW_Y_JITTER_PX)

    centers_row = []
    for (cx, cy) in centers:
        centers_row.append((cx + row_dx, cy + row_dy))

    centers_j = []
    for (cx, cy) in centers_row:
        jx = random.randint(-pos_jitter_px, pos_jitter_px)
        jy = 0  # как было в three
        centers_j.append((cx + jx, cy + jy))

    tmp_to_clean: List[str] = []

    rotated_meta = []  # (tmp_path, w, h)
    scales = []
    angles_used = []
    for i, src in enumerate(card_paths):
        p_eff = map_card_path_with_reverse(src, bool(reversed_flags[i]))
        ang = random.uniform(-angle_jitter_deg, angle_jitter_deg) if angle_jitter_deg > 0 else 0.0
        tmp_rot = tempfile.NamedTemporaryFile(delete=False, suffix=".png"); tmp_rot.close()
        rotate_with_imagemagick(p_eff, ang, tmp_rot.name, im_bin)
        tmp_to_clean.append(tmp_rot.name)

        card_bgra_tmp = cv2.imread(tmp_rot.name, cv2.IMREAD_UNCHANGED)
        if card_bgra_tmp is None:
            raise FileNotFoundError(f"Не удалось открыть повернутую карту: {tmp_rot.name}")
        h_tmp, w_tmp = card_bgra_tmp.shape[:2]
        scales.append(min(slot_w / float(w_tmp), slot_h / float(h_tmp)))
        rotated_meta.append((tmp_rot.name, w_tmp, h_tmp))
        angles_used.append(ang)

    scale_all = min(1.0, min(scales))  # единый масштаб без апскейла

    try:
        canvas = base_bgr.copy()
        mask_union = np.zeros((H, W), dtype=np.uint8)

        for i, (tmp_path, w0, h0) in enumerate(rotated_meta):
            card_bgra = cv2.imread(tmp_path, cv2.IMREAD_UNCHANGED)
            if card_bgra is None:
                raise FileNotFoundError(f"Не удалось открыть повернутую карту: {tmp_path}")
            if card_bgra.shape[2] == 4:
                src_bgr = card_bgra[:, :, :3]
                alpha = card_bgra[:, :, 3]
            else:
                src_bgr = card_bgra
                alpha = np.full(src_bgr.shape[:2], 255, np.uint8)

            if abs(scale_all - 1.0) > 1e-6:
                new_w = max(1, int(round(w0 * scale_all)))
                new_h = max(1, int(round(h0 * scale_all)))
                src_bgr = cv2.resize(src_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
                alpha   = cv2.resize(alpha,   (new_w, new_h), interpolation=cv2.INTER_AREA)
                h, w = new_h, new_w
            else:
                h, w = h0, w0

            px_per_mm = max(0.5, h / REAL_CARD_HEIGHT_MM)
            ao_ring_px_local = int(max(1, round(px_per_mm * 0.3)))
            ao_blur_local = int(max(1, round(px_per_mm * 0.8)))
            if ao_blur_local % 2 == 0:
                ao_blur_local += 1
            ao_opacity_local = min(0.09, 0.07 + px_per_mm*0.002)

            max_offset_px = int(max(1, round(px_per_mm * CARD_THICKNESS_MM * 0.3)))
            ox_est, oy_est = shadow_offset
            mag = max(1e-6, (ox_est**2 + oy_est**2) ** 0.5)
            scale_off = min(1.0, max_offset_px / mag)
            ox_loc = int(round(ox_est * scale_off))
            oy_loc = int(round(oy_est * scale_off))
            if ox_loc == 0 and oy_loc == 0:
                ox_loc = 1 if ox_est >= 0 else -1
                oy_loc = 1 if oy_est >= 0 else -1

            shadow_blur_local = int(max(3, round(px_per_mm * 0.9)))
            if shadow_blur_local % 2 == 0:
                shadow_blur_local += 1
            shadow_opacity_local = min(0.10, 0.06 + px_per_mm*0.002)

            mask_local = (alpha > 0).astype(np.uint8) * 255
            if EDGE_FEATHER_PX > 0:
                kf = EDGE_FEATHER_PX*2 + 1
                mask_local = cv2.GaussianBlur(mask_local, (kf, kf), EDGE_FEATHER_PX/2)

            cx, cy = centers_j[i]
            cx, cy = clamp_center_to_roi((cx, cy), (w, h), HARDCODED_ROI)
            x = cx - w // 2
            y = cy - h // 2

            mask_full = place_mask_on_canvas(mask_local, (H, W), x, y)
            mask_union = cv2.bitwise_or(mask_union, mask_full)
            canvas = add_contact_shadow(canvas, mask_full,
                                        ring_px=ao_ring_px_local, blur=ao_blur_local,
                                        opacity=ao_opacity_local, gamma=AO_GAMMA)
            canvas = add_directional_shadow(canvas, mask_full, (ox_loc, oy_loc),
                                            blur=shadow_blur_local, opacity=shadow_opacity_local)

            x0 = max(0, x); y0 = max(0, y)
            x1 = min(W, x + w); y1 = min(H, y + h)
            sx0, sy0 = x0 - x, y0 - y
            sx1, sy1 = sx0 + (x1 - x0), sy0 + (y1 - y0)
            if x0 >= x1 or y0 >= y1 or sx0 >= sx1 or sy0 >= sy1:
                continue

            src_crop = src_bgr[sy0:sy1, sx0:sx1]
            alpha_crop = mask_local[sy0:sy1, sx0:sx1]
            bg_crop = canvas[y0:y1, x0:x1]

            m = (alpha_crop.astype(np.float32)/255.0)[:, :, None]
            blended = bg_crop.astype(np.float32)*(1-m) + src_crop.astype(np.float32)*m
            local = np.clip(blended, 0, 255).astype(np.uint8)

            local = lab_match(local, bg_crop, blend=LAB_BLEND)
            local = light_wrap_local(local, bg_crop, alpha_crop, radius=WRAP_RADIUS, amount=WRAP_AMOUNT)
            local = add_reflect_edge(local, alpha_crop, amount=REFLECT_AMOUNT)
            local = suppress_white_border(local, bg_crop, alpha_crop,
                                          width=WHITE_BORDER_WIDTH, strength=WHITE_BORDER_SUPPRESS)

            canvas[y0:y1, x0:x1] = local

        canvas = add_camera_grain_bg_only(canvas, mask_union, strength=grain_strength if add_grain else 0.0)
        canvas = add_soft_vignette(canvas, strength=VIGNETTE_STRENGTH)

        ext = os.path.splitext(out_path)[1].lower()
        if ext in (".jpg", ".jpeg"):
            cv2.imwrite(out_path, canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 96])
        else:
            cv2.imwrite(out_path, canvas, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])

    finally:
        for p in tmp_to_clean:
            try:
                os.remove(p)
            except Exception:
                pass


def compose_cards_keep_texture(seed_path: str,
                               card_paths: List[str],
                               out_path: str,
                               reversed_flags: List[bool],
                               angle_jitter_deg: float = DEFAULT_ANGLE_JITTER_DEG,
                               pos_jitter_px: int = DEFAULT_POS_JITTER_PX,
                               allow_upscale: bool = ALLOW_UPSCALE_DEFAULT,
                               add_grain: bool = ADD_GRAIN_DEFAULT,
                               grain_strength: float = GRAIN_STRENGTH_DEFAULT) -> None:
    """
    Универсальный вход: поддерживает 1 или 3 карты.
    - 3 карты: идентично compose_three_cards_keep_texture
    - 1 карта: по центру ROI, теперь с вертикальным джиттером и гарантированным лёгким наклоном.
    """
    n = len(card_paths)
    if n == 3:
        return compose_three_cards_keep_texture(
            seed_path=seed_path,
            card_paths=card_paths,
            out_path=out_path,
            reversed_flags=reversed_flags,
            angle_jitter_deg=angle_jitter_deg,
            pos_jitter_px=pos_jitter_px,
            allow_upscale=allow_upscale,
            add_grain=add_grain,
            grain_strength=grain_strength,
        )
    if n != 1:
        raise AssertionError("compose_cards_keep_texture поддерживает только 1 или 3 карты.")

    # ------- Реализация для 1 карты (по центру ROI) -------
    im_bin = find_imagemagick_bin()

    base_bgr = cv2.imread(seed_path, cv2.IMREAD_COLOR)
    if base_bgr is None:
        raise FileNotFoundError(f"Не удалось открыть фон: {seed_path}")
    H, W = base_bgr.shape[:2]

    shadow_offset = estimate_light_vector(base_bgr, HARDCODED_ROI, pct=LIGHT_PCT, base_px=LIGHT_VECTOR_BASE_PX)
    slot_w, slot_h, *_ , centers = compute_slot(HARDCODED_ROI)
    center_mid = centers[1]  # центральная позиция

    # Общий сдвиг ряда + горизонтальный и вертикальный джиттер как «живой» центральной карты
    row_dx = random.randint(-ROW_X_JITTER_PX, ROW_X_JITTER_PX)
    row_dy = random.randint(-ROW_Y_JITTER_PX, ROW_Y_JITTER_PX)
    cx_row, cy_row = (center_mid[0] + row_dx, center_mid[1] + row_dy)

    jx = random.randint(-pos_jitter_px, pos_jitter_px)
    jy = random.randint(-pos_jitter_px, pos_jitter_px)  # раньше было 0, теперь как у трёх — есть небольшой Y-джиттер
    cx_final, cy_final = (cx_row + jx, cy_row + jy)

    tmp_to_clean: List[str] = []

    # Поворот/масштаб (гарантируем небольшой наклон при включённом jitter)
    src = card_paths[0]
    p_eff = map_card_path_with_reverse(src, bool(reversed_flags[0]))
    if angle_jitter_deg > 0:
        ang = random.uniform(-angle_jitter_deg, angle_jitter_deg)
        if abs(ang) < MIN_ANGLE_VISUAL and angle_jitter_deg >= MIN_ANGLE_VISUAL:
            ang = MIN_ANGLE_VISUAL if random.random() < 0.5 else -MIN_ANGLE_VISUAL
    else:
        ang = 0.0

    tmp_rot = tempfile.NamedTemporaryFile(delete=False, suffix=".png"); tmp_rot.close()
    rotate_with_imagemagick(p_eff, ang, tmp_rot.name, im_bin)
    tmp_to_clean.append(tmp_rot.name)

    card_bgra_tmp = cv2.imread(tmp_rot.name, cv2.IMREAD_UNCHANGED)
    if card_bgra_tmp is None:
        raise FileNotFoundError(f"Не удалось открыть повернутую карту: {tmp_rot.name}")
    h0, w0 = card_bgra_tmp.shape[:2]
    scale = min(slot_w / float(w0), slot_h / float(h0))
    scale_all = min(1.0, scale)

    try:
        canvas = base_bgr.copy()

        card_bgra = cv2.imread(tmp_rot.name, cv2.IMREAD_UNCHANGED)
        if card_bgra is None:
            raise FileNotFoundError(f"Не удалось открыть повернутую карту: {tmp_rot.name}")
        if card_bgra.shape[2] == 4:
            src_bgr = card_bgra[:, :, :3]
            alpha = card_bgra[:, :, 3]
        else:
            src_bgr = card_bgra
            alpha = np.full(src_bgr.shape[:2], 255, np.uint8)

        if abs(scale_all - 1.0) > 1e-6:
            new_w = max(1, int(round(w0 * scale_all)))
            new_h = max(1, int(round(h0 * scale_all)))
            src_bgr = cv2.resize(src_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
            alpha   = cv2.resize(alpha,   (new_w, new_h), interpolation=cv2.INTER_AREA)
            h, w = new_h, new_w
        else:
            h, w = h0, w0

        px_per_mm = max(0.5, h / REAL_CARD_HEIGHT_MM)
        ao_ring_px_local = int(max(1, round(px_per_mm * 0.3)))
        ao_blur_local = int(max(1, round(px_per_mm * 0.8)))
        if ao_blur_local % 2 == 0:
            ao_blur_local += 1
        ao_opacity_local = min(0.09, 0.07 + px_per_mm*0.002)

        max_offset_px = int(max(1, round(px_per_mm * CARD_THICKNESS_MM * 0.3)))
        ox_est, oy_est = shadow_offset
        mag = max(1e-6, (ox_est**2 + oy_est**2) ** 0.5)
        scale_off = min(1.0, max_offset_px / mag)
        ox_loc = int(round(ox_est * scale_off))
        oy_loc = int(round(oy_est * scale_off))
        if ox_loc == 0 and oy_loc == 0:
            ox_loc = 1 if ox_est >= 0 else -1
            oy_loc = 1 if oy_est >= 0 else -1

        shadow_blur_local = int(max(3, round(px_per_mm * 0.9)))
        if shadow_blur_local % 2 == 0:
            shadow_blur_local += 1
        shadow_opacity_local = min(0.10, 0.06 + px_per_mm*0.002)

        mask_local = (alpha > 0).astype(np.uint8) * 255
        if EDGE_FEATHER_PX > 0:
            kf = EDGE_FEATHER_PX*2 + 1
            mask_local = cv2.GaussianBlur(mask_local, (kf, kf), EDGE_FEATHER_PX/2)

        cx, cy = clamp_center_to_roi((cx_final, cy_final), (w, h), HARDCODED_ROI)
        x = cx - w // 2
        y = cy - h // 2

        mask_full = place_mask_on_canvas(mask_local, (H, W), x, y)
        canvas = add_contact_shadow(canvas, mask_full,
                                    ring_px=ao_ring_px_local, blur=ao_blur_local,
                                    opacity=ao_opacity_local, gamma=AO_GAMMA)
        canvas = add_directional_shadow(canvas, mask_full, (ox_loc, oy_loc),
                                        blur=shadow_blur_local, opacity=shadow_opacity_local)

        x0 = max(0, x); y0 = max(0, y)
        x1 = min(W, x + w); y1 = min(H, y + h)
        sx0, sy0 = x0 - x, y0 - y
        sx1, sy1 = sx0 + (x1 - x0), sy0 + (y1 - y0)
        if not (x0 < x1 and y0 < y1 and sx0 < sx1 and sy0 < sy1):
            final = canvas
        else:
            src_crop = src_bgr[sy0:sy1, sx0:sx1]
            alpha_crop = mask_local[sy0:sy1, sx0:sx1]
            bg_crop = canvas[y0:y1, x0:x1]

            m = (alpha_crop.astype(np.float32)/255.0)[:, :, None]
            blended = bg_crop.astype(np.float32)*(1-m) + src_crop.astype(np.float32)*m
            local = np.clip(blended, 0, 255).astype(np.uint8)

            local = lab_match(local, bg_crop, blend=LAB_BLEND)
            local = light_wrap_local(local, bg_crop, alpha_crop, radius=WRAP_RADIUS, amount=WRAP_AMOUNT)
            local = add_reflect_edge(local, alpha_crop, amount=REFLECT_AMOUNT)
            local = suppress_white_border(local, bg_crop, alpha_crop,
                                          width=WHITE_BORDER_WIDTH, strength=WHITE_BORDER_SUPPRESS)

            canvas[y0:y1, x0:x1] = local
            final = canvas

        final = add_soft_vignette(add_camera_grain_bg_only(final, mask_full, strength=grain_strength if add_grain else 0.0),
                                  strength=VIGNETTE_STRENGTH)

        ext = os.path.splitext(out_path)[1].lower()
        if ext in (".jpg", ".jpeg"):
            cv2.imwrite(out_path, final, [int(cv2.IMWRITE_JPEG_QUALITY), 96])
        else:
            cv2.imwrite(out_path, final, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])

    finally:
        for p in tmp_to_clean:
            try:
                os.remove(p)
            except Exception:
                pass

# -------------------- CLI --------------------

def parse_flags(s: str) -> List[bool]:
    s = s.strip().lower()
    parts = [p.strip() for p in s.replace("upright", "0").replace("reversed", "1").split(",")]
    return [p in ("1", "true", "t", "yes", "y") for p in parts]


def main():
    global ROW_X_JITTER_PX, ROW_Y_JITTER_PX, SCARLET_TABLE_NUMBER

    script_dir = os.path.abspath(os.path.dirname(__file__))
    default_seed = os.path.join(script_dir, "scarlet_table.jpg")
    default_cards = [
        os.path.join(script_dir, "tarot", "major_arcana_empress.png"),
        os.path.join(script_dir, "tarot", "minor_arcana_cups_6.png"),
        os.path.join(script_dir, "tarot", "minor_arcana_pentacles_10.png"),
    ]
    default_out = os.path.join(script_dir, "test_keep_texture.jpg")

    ap = argparse.ArgumentParser(description="Compose 3 tarot cards — realism via environment (no texture change).")
    ap.add_argument("--seed", default=default_seed)
    ap.add_argument("--cards", nargs=3, default=default_cards)
    ap.add_argument("--reversed", default="0,0,0")
    ap.add_argument("--out", default=default_out)
    ap.add_argument("--rng_seed", type=int, default=None)
    ap.add_argument("--angle_jitter_deg", type=float, default=DEFAULT_ANGLE_JITTER_DEG)
    ap.add_argument("--pos_jitter_px", type=int, default=DEFAULT_POS_JITTER_PX)
    ap.add_argument("--allow_upscale", action="store_true", help="Разрешить апскейл карты при нехватке пикселей.")
    ap.add_argument("--grain", action="store_true", default=ADD_GRAIN_DEFAULT, help="Включить камерный grain (только фон).")
    ap.add_argument("--grain_strength", type=float, default=GRAIN_STRENGTH_DEFAULT, help="Сила зерна 0..0.05.")
    ap.add_argument("--row_x_jitter_px", type=int, default=ROW_X_JITTER_PX, help="Общий сдвиг ряда по X (px).")
    ap.add_argument("--row_y_jitter_px", type=int, default=ROW_Y_JITTER_PX, help="Общий сдвиг ряда по Y (px).")
    args = ap.parse_args()

    ROW_X_JITTER_PX = args.row_x_jitter_px
    ROW_Y_JITTER_PX = args.row_y_jitter_px

    if args.rng_seed is not None:
        random.seed(args.rng_seed)

    if SCARLET_TABLE_TOTAL >= 0:
        SCARLET_TABLE_NUMBER = random.randint(0, SCARLET_TABLE_TOTAL)
        selected_name = "scarlet_table.jpg" if SCARLET_TABLE_NUMBER == 0 else f"scarlet_table{SCARLET_TABLE_NUMBER}.jpg"
        selected_seed = os.path.join(script_dir, selected_name)
        if args.seed == default_seed:
            args.seed = selected_seed

    flags = parse_flags(args.reversed)

    compose_three_cards_keep_texture(
        seed_path=args.seed,
        card_paths=args.cards,
        out_path=args.out,
        reversed_flags=flags,
        angle_jitter_deg=args.angle_jitter_deg,
        pos_jitter_px=args.pos_jitter_px,
        allow_upscale=args.allow_upscale,
        add_grain=args.grain,
        grain_strength=args.grain_strength,
    )
    print("✅ Saved:", args.out)


if __name__ == "__main__":
    main()
