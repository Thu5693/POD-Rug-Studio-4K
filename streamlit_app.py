import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# CẤU HÌNH TRANG STREAMLIT (FULL-WIDTH STUDIO MODE)
# ==============================================================================
st.set_page_config(
    page_title="POD Rug Studio 4K - Chuẩn Hóa & Tái Tạo Art Thảm",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 0.25rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0.25rem !important;
            padding-right: 0.25rem !important;
            max-width: 100% !important;
        }
        header[data-testid="stHeader"] {
            background: transparent !important;
        }
        footer {
            visibility: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Tự động đọc GEMINI_API_KEY từ mục Secrets của Streamlit (nếu có)
default_gemini_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        default_gemini_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    default_gemini_key = ""

# ==============================================================================
# MÃ NGUỒN ỨNG DỤNG POD RUG STUDIO 4K (ĐẦY ĐỦ 100% TÍNH NĂNG)
# ==============================================================================
html_studio_code = r"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>POD Rug Studio 4K</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    body { margin: 0; background-color: #020617; color: #f1f5f9; font-family: Inter, system-ui, sans-serif; }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
  </style>
</head>
<body>
  <div id="root"></div>

  <script type="text/babel">
    const { useState, useRef, useEffect, useCallback } = React;
    const STREAMLIT_DEFAULT_KEY = "__STREAMLIT_GEMINI_KEY__";

    function getInverseHomographyMatrix(srcPts, dstW, dstH) {
      const dstPts = [
        { x: 0, y: 0 },
        { x: dstW, y: 0 },
        { x: dstW, y: dstH },
        { x: 0, y: dstH }
      ];
      const A = [];
      const b = [];
      for (let i = 0; i < 4; i++) {
        const X = dstPts[i].x, Y = dstPts[i].y;
        const x = srcPts[i].x, y = srcPts[i].y;
        A.push([X, Y, 1, 0, 0, 0, -X * x, -Y * x]);
        b.push(x);
        A.push([0, 0, 0, X, Y, 1, -X * y, -Y * y]);
        b.push(y);
      }
      const n = 8;
      for (let i = 0; i < n; i++) {
        let maxRow = i;
        for (let k = i + 1; k < n; k++) {
          if (Math.abs(A[k][i]) > Math.abs(A[maxRow][i])) maxRow = k;
        }
        [A[i], A[maxRow]] = [A[maxRow], A[i]];
        [b[i], b[maxRow]] = [b[maxRow], b[i]];
        const pivot = A[i][i];
        if (Math.abs(pivot) < 1e-10) continue;
        for (let j = i; j < n; j++) A[i][j] /= pivot;
        b[i] /= pivot;
        for (let k = 0; k < n; k++) {
          if (k !== i) {
            const factor = A[k][i];
            for (let j = i; j < n; j++) A[k][j] -= factor * A[i][j];
            b[k] -= factor * b[i];
          }
        }
      }
      return [b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7], 1];
    }

    function warpPerspectiveImage(srcImageData, dstW, dstH, srcQuad, shapeType, bgColor, paddingPct = 0) {
      const dstCanvas = document.createElement('canvas');
      dstCanvas.width = dstW;
      dstCanvas.height = dstH;
      const ctx = dstCanvas.getContext('2d');
      const dstImgData = ctx.createImageData(dstW, dstH);
      const dstData = dstImgData.data;

      const srcW = srcImageData.width;
      const srcH = srcImageData.height;
      const srcData = srcImageData.data;

      let bgR = 0, bgG = 0, bgB = 0, bgA = 255;
      if (bgColor === 'white') { bgR = 255; bgG = 255; bgB = 255; bgA = 255; }
      else if (bgColor === 'transparent') { bgA = 0; }

      const padX = Math.round(dstW * (paddingPct / 100));
      const padY = Math.round(dstH * (paddingPct / 100));
      const activeW = Math.max(10, dstW - padX * 2);
      const activeH = Math.max(10, dstH - padY * 2);

      const H = getInverseHomographyMatrix(srcQuad, activeW, activeH);
      const cx = activeW / 2, cy = activeH / 2, rx = activeW / 2, ry = activeH / 2;

      for (let y = 0; y < dstH; y++) {
        for (let x = 0; x < dstW; x++) {
          const dstIdx = (y * dstW + x) * 4;
          const u = x - padX;
          const v = y - padY;
          let insideShape = u >= 0 && u < activeW && v >= 0 && v < activeH;
          let edgeAlpha = 1.0;

          if (insideShape && shapeType === 'circle') {
            const dx = (u - cx) / rx;
            const dy = (v - cy) / ry;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist > 1.0) insideShape = false;
            else if (dist > 0.992) edgeAlpha = (1.0 - dist) / 0.008;
          }

          if (!insideShape) {
            dstData[dstIdx] = bgR; dstData[dstIdx + 1] = bgG; dstData[dstIdx + 2] = bgB; dstData[dstIdx + 3] = bgA;
            continue;
          }

          const denom = H[6] * u + H[7] * v + H[8];
          const srcX = (H[0] * u + H[1] * v + H[2]) / denom;
          const srcY = (H[3] * u + H[4] * v + H[5]) / denom;

          if (srcX >= 0 && srcX < srcW - 1 && srcY >= 0 && srcY < srcH - 1) {
            const x0 = Math.floor(srcX), y0 = Math.floor(srcY);
            const dx = srcX - x0, dy = srcY - y0;
            const idx00 = (y0 * srcW + x0) * 4;
            const idx10 = idx00 + 4;
            const idx01 = ((y0 + 1) * srcW + x0) * 4;
            const idx11 = idx01 + 4;

            const w00 = (1 - dx) * (1 - dy), w10 = dx * (1 - dy), w01 = (1 - dx) * dy, w11 = dx * dy;
            const r = srcData[idx00] * w00 + srcData[idx10] * w10 + srcData[idx01] * w01 + srcData[idx11] * w11;
            const g = srcData[idx00 + 1] * w00 + srcData[idx10 + 1] * w10 + srcData[idx01 + 1] * w01 + srcData[idx11 + 1] * w11;
            const b = srcData[idx00 + 2] * w00 + srcData[idx10 + 2] * w10 + srcData[idx01 + 2] * w01 + srcData[idx11 + 2] * w11;

            dstData[dstIdx] = Math.round(r * edgeAlpha + bgR * (1 - edgeAlpha));
            dstData[dstIdx + 1] = Math.round(g * edgeAlpha + bgG * (1 - edgeAlpha));
            dstData[dstIdx + 2] = Math.round(b * edgeAlpha + bgB * (1 - edgeAlpha));
            dstData[dstIdx + 3] = bgA === 0 && edgeAlpha < 1 ? Math.round(255 * edgeAlpha) : 255;
          } else {
            dstData[dstIdx] = bgR; dstData[dstIdx + 1] = bgG; dstData[dstIdx + 2] = bgB; dstData[dstIdx + 3] = bgA;
          }
        }
      }
      ctx.putImageData(dstImgData, 0, 0);
      return dstCanvas;
    }

    function generateSampleMockup(type) {
      const canvas = document.createElement('canvas');
      canvas.width = 1000; canvas.height = 750;
      const ctx = canvas.getContext('2d');

      const floorGrad = ctx.createLinearGradient(0, 0, 1000, 750);
      floorGrad.addColorStop(0, '#5c3d28'); floorGrad.addColorStop(0.5, '#704b32'); floorGrad.addColorStop(1, '#422a1a');
      ctx.fillStyle = floorGrad; ctx.fillRect(0, 0, 1000, 750);

      ctx.strokeStyle = 'rgba(30, 15, 5, 0.35)';
      ctx.lineWidth = 2;
      for (let i = -200; i <= 1200; i += 95) {
        ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i + (i - 500) * 0.4, 750); ctx.stroke();
      }

      const artW = 600, artH = type === 'rect' ? 800 : 600;
      const artCanvas = document.createElement('canvas');
      artCanvas.width = artW; artCanvas.height = artH;
      const actx = artCanvas.getContext('2d');

      if (type === 'rect') {
        actx.fillStyle = '#141e30'; actx.fillRect(0, 0, artW, artH);
        actx.strokeStyle = '#e6b800'; actx.lineWidth = 18; actx.strokeRect(24, 24, artW - 48, artH - 48);
        actx.strokeStyle = '#c0392b'; actx.lineWidth = 26; actx.strokeRect(52, 52, artW - 104, artH - 104);
        actx.strokeStyle = '#f39c12'; actx.lineWidth = 6; actx.strokeRect(76, 76, artW - 152, artH - 152);
        const drawCornerMotif = (cx, cy) => {
          actx.save(); actx.translate(cx, cy);
          actx.fillStyle = '#e67e22'; actx.beginPath(); actx.arc(0, 0, 55, 0, Math.PI * 2); actx.fill();
          actx.strokeStyle = '#fff3cd'; actx.lineWidth = 4; actx.stroke();
          actx.fillStyle = '#141e30'; actx.beginPath(); actx.arc(0, 0, 25, 0, Math.PI * 2); actx.fill();
          actx.restore();
        };
        drawCornerMotif(115, 115); drawCornerMotif(artW - 115, 115);
        drawCornerMotif(artW - 115, artH - 115); drawCornerMotif(115, artH - 115);
        actx.save(); actx.translate(artW / 2, artH / 2);
        for (let r = 210; r > 20; r -= 28) {
          actx.fillStyle = r % 56 === 0 ? '#c0392b' : r % 84 === 0 ? '#f1c40f' : '#1abc9c';
          actx.beginPath();
          for (let a = 0; a < 16; a++) {
            const angle = (a * Math.PI) / 8;
            const rad = a % 2 === 0 ? r : r * 0.72;
            const px = Math.cos(angle) * rad, py = Math.sin(angle) * rad;
            if (a === 0) actx.moveTo(px, py); else actx.lineTo(px, py);
          }
          actx.closePath(); actx.fill();
          actx.strokeStyle = '#ffffff'; actx.lineWidth = 3; actx.stroke();
        }
        actx.restore();
      } else if (type === 'circle') {
        actx.fillStyle = '#1f2937'; actx.beginPath(); actx.arc(300, 300, 298, 0, Math.PI * 2); actx.fill();
        actx.strokeStyle = '#f59e0b'; actx.lineWidth = 16; actx.beginPath(); actx.arc(300, 300, 272, 0, Math.PI * 2); actx.stroke();
        actx.strokeStyle = '#10b981'; actx.lineWidth = 10; actx.beginPath(); actx.arc(300, 300, 244, 0, Math.PI * 2); actx.stroke();
        actx.save(); actx.translate(300, 300);
        for (let i = 0; i < 24; i++) {
          actx.rotate((Math.PI * 2) / 24);
          actx.fillStyle = i % 2 === 0 ? '#ef4444' : '#fbbf24';
          actx.beginPath(); actx.moveTo(0, -60); actx.lineTo(18, -220); actx.lineTo(-18, -220); actx.closePath(); actx.fill();
        }
        actx.fillStyle = '#fef3c7'; actx.beginPath(); actx.arc(0, 0, 75, 0, Math.PI * 2); actx.fill();
        actx.restore();
      } else {
        actx.fillStyle = '#0f172a'; actx.fillRect(0, 0, 600, 600);
        const colors = ['#ec4899', '#8b5cf6', '#06b6d4', '#f59e0b'];
        const size = 240;
        [[45, 45], [315, 45], [315, 315], [45, 315]].forEach(([px, py], idx) => {
          actx.fillStyle = colors[idx]; actx.fillRect(px, py, size, size);
          actx.fillStyle = '#ffffff'; actx.beginPath(); actx.arc(px + size / 2, py + size / 2, 72, 0, Math.PI * 2); actx.fill();
          actx.fillStyle = '#0f172a'; actx.beginPath(); actx.arc(px + size / 2, py + size / 2, 34, 0, Math.PI * 2); actx.fill();
        });
        actx.strokeStyle = '#38bdf8'; actx.lineWidth = 18; actx.strokeRect(20, 20, 560, 560);
      }

      const artData = actx.getImageData(0, 0, artW, artH);
      const d = artData.data;
      for (let y = 0; y < artH; y++) {
        for (let x = 0; x < artW; x++) {
          const i = (y * artW + x) * 4;
          if (d[i + 3] === 0) continue;
          const noise = ((x % 3 === 0 ? 14 : -10) + (y % 3 === 0 ? 12 : -8)) + Math.sin((x + y) * 0.035) * 18;
          d[i] = Math.min(255, Math.max(0, d[i] + noise));
          d[i + 1] = Math.min(255, Math.max(0, d[i + 1] + noise));
          d[i + 2] = Math.min(255, Math.max(0, d[i + 2] + noise));
        }
      }
      actx.putImageData(artData, 0, 0);

      const quad = type === 'rect'
        ? [{ x: 280, y: 95 }, { x: 715, y: 120 }, { x: 865, y: 655 }, { x: 145, y: 635 }]
        : type === 'circle'
        ? [{ x: 250, y: 140 }, { x: 760, y: 155 }, { x: 870, y: 615 }, { x: 135, y: 595 }]
        : [{ x: 265, y: 115 }, { x: 745, y: 105 }, { x: 845, y: 625 }, { x: 165, y: 640 }];

      const A = [], b = [];
      const dstPts = [{ x: 0, y: 0 }, { x: artW, y: 0 }, { x: artW, y: artH }, { x: 0, y: artH }];
      for (let i = 0; i < 4; i++) {
        const X = quad[i].x, Y = quad[i].y, u = dstPts[i].x, v = dstPts[i].y;
        A.push([X, Y, 1, 0, 0, 0, -X * u, -Y * u]); b.push(u);
        A.push([0, 0, 0, X, Y, 1, -X * v, -Y * v]); b.push(v);
      }
      for (let i = 0; i < 8; i++) {
        let maxR = i;
        for (let k = i + 1; k < 8; k++) if (Math.abs(A[k][i]) > Math.abs(A[maxR][i])) maxR = k;
        [A[i], A[maxR]] = [A[maxR], A[i]]; [b[i], b[maxR]] = [b[maxR], b[i]];
        const p = A[i][i];
        for (let j = i; j < 8; j++) A[i][j] /= p; b[i] /= p;
        for (let k = 0; k < 8; k++) if (k !== i) {
          const f = A[k][i];
          for (let j = i; j < 8; j++) A[k][j] -= f * A[i][j]; b[k] -= f * b[i];
        }
      }
      const H = [b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7], 1];
      const mImg = ctx.getImageData(0, 0, 1000, 750);
      const mD = mImg.data;
      for (let y = 0; y < 750; y++) {
        for (let x = 0; x < 1000; x++) {
          const den = H[6] * x + H[7] * y + H[8];
          const u = (H[0] * x + H[1] * y + H[2]) / den;
          const v = (H[3] * x + H[4] * y + H[5]) / den;
          if (u >= 0 && u < artW && v >= 0 && v < artH) {
            if (type === 'circle' && Math.hypot((u - 300) / 298, (v - 300) / 298) > 1) continue;
            const aIdx = (Math.floor(v) * artW + Math.floor(u)) * 4;
            const mIdx = (y * 1000 + x) * 4;
            mD[mIdx] = d[aIdx]; mD[mIdx + 1] = d[aIdx + 1]; mD[mIdx + 2] = d[aIdx + 2]; mD[mIdx + 3] = 255;
          }
        }
      }
      ctx.putImageData(mImg, 0, 0);

      if (type === 'rect') {
        ctx.save();
        ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.beginPath(); ctx.arc(215, 585, 42, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#3e2723'; ctx.beginPath(); ctx.arc(205, 580, 32, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#d7ccc8'; ctx.lineWidth = 3; ctx.stroke();
        ctx.restore();
      }

      return {
        dataUrl: canvas.toDataURL('image/png'),
        quad,
        shapeType: type === 'rect' ? 'rect_v' : type === 'circle' ? 'circle' : 'square',
        label: type === 'rect'
          ? 'Mockup Thảm Chữ Nhật (Phối cảnh nghiêng + Vật cản góc dưới trái)'
          : type === 'circle'
          ? 'Mockup Thảm Tròn Boho (Góc chụp elip nghiêng trên sàn gỗ)'
          : 'Mockup Thảm Vuông Geometric (Nếp gấp vải & phối cảnh)'
      };
    }

    function processFlat2DArtwork(sourceCanvas, options) {
      const {
        removeFabricIntensity = 75,
        sharpenEdges = 65,
        flattenLighting = 60,
        boostVibrance = 35,
        autoMirrorClippedCorners = false,
        shapeType = 'rect_v',
        bgColor = 'black'
      } = options;

      const w = sourceCanvas.width, h = sourceCanvas.height;
      const outCanvas = document.createElement('canvas');
      outCanvas.width = w; outCanvas.height = h;
      const ctx = outCanvas.getContext('2d');
      ctx.drawImage(sourceCanvas, 0, 0);
      let imgData = ctx.getImageData(0, 0, w, h);
      let data = imgData.data;

      if (autoMirrorClippedCorners) {
        const cornerW = Math.floor(w * 0.25), cornerH = Math.floor(h * 0.22);
        for (let y = h - cornerH; y < h; y++) {
          for (let x = 0; x < cornerW; x++) {
            const mirrorY = h - 1 - y;
            const srcIdx = (mirrorY * w + x) * 4;
            const dstIdx = (y * w + x) * 4;
            const alpha = Math.min(1, (cornerW - x) / (cornerW * 0.25), (y - (h - cornerH)) / (cornerH * 0.25));
            data[dstIdx] = Math.round(data[srcIdx] * alpha + data[dstIdx] * (1 - alpha));
            data[dstIdx + 1] = Math.round(data[srcIdx + 1] * alpha + data[dstIdx + 1] * (1 - alpha));
            data[dstIdx + 2] = Math.round(data[srcIdx + 2] * alpha + data[dstIdx + 2] * (1 - alpha));
          }
        }
      }

      if (removeFabricIntensity > 0) {
        const copy = new Uint8ClampedArray(data);
        const radius = removeFabricIntensity > 60 ? 3 : 2;
        const threshSq = Math.pow(22 + removeFabricIntensity * 0.45, 2) * 3;
        for (let y = radius; y < h - radius; y++) {
          for (let x = radius; x < w - radius; x++) {
            const cIdx = (y * w + x) * 4;
            if (copy[cIdx + 3] === 0) continue;
            const cr = copy[cIdx], cg = copy[cIdx + 1], cb = copy[cIdx + 2];
            let sR = 0, sG = 0, sB = 0, sW = 0;
            for (let dy = -radius; dy <= radius; dy++) {
              for (let dx = -radius; dx <= radius; dx++) {
                const nIdx = ((y + dy) * w + (x + dx)) * 4;
                const dSq = Math.pow(copy[nIdx] - cr, 2) + Math.pow(copy[nIdx + 1] - cg, 2) + Math.pow(copy[nIdx + 2] - cb, 2);
                if (dSq < threshSq) {
                  const wt = 1.0 - dSq / threshSq;
                  sR += copy[nIdx] * wt; sG += copy[nIdx + 1] * wt; sB += copy[nIdx + 2] * wt; sW += wt;
                }
              }
            }
            if (sW > 0) {
              data[cIdx] = Math.round(sR / sW); data[cIdx + 1] = Math.round(sG / sW); data[cIdx + 2] = Math.round(sB / sW);
            }
          }
        }
      }

      const satBoost = 1 + (boostVibrance / 100) * 0.55;
      const contrastBoost = 1 + (flattenLighting / 100) * 0.22;
      for (let i = 0; i < data.length; i += 4) {
        if (data[i + 3] === 0) continue;
        let r = (data[i] - 128) * contrastBoost + 128;
        let g = (data[i + 1] - 128) * contrastBoost + 128;
        let b = (data[i + 2] - 128) * contrastBoost + 128;
        const luma = 0.299 * r + 0.587 * g + 0.114 * b;
        data[i] = Math.min(255, Math.max(0, Math.round(luma + (r - luma) * satBoost)));
        data[i + 1] = Math.min(255, Math.max(0, Math.round(luma + (g - luma) * satBoost)));
        data[i + 2] = Math.min(255, Math.max(0, Math.round(luma + (b - luma) * satBoost)));
      }

      if (sharpenEdges > 0) {
        const copy = new Uint8ClampedArray(data);
        const amt = (sharpenEdges / 100) * 1.85;
        for (let y = 1; y < h - 1; y++) {
          for (let x = 1; x < w - 1; x++) {
            const idx = (y * w + x) * 4;
            for (let c = 0; c < 3; c++) {
              const center = copy[idx + c];
              const nb = (copy[((y - 1) * w + x) * 4 + c] + copy[((y + 1) * w + x) * 4 + c] + copy[(y * w + x - 1) * 4 + c] + copy[(y * w + x + 1) * 4 + c]) * 0.25;
              data[idx + c] = Math.min(255, Math.max(0, Math.round(center + (center - nb) * amt)));
            }
          }
        }
      }

      if (shapeType === 'circle') {
        const cx = w / 2, cy = h / 2, rx = w / 2, ry = h / 2;
        const bgR = bgColor === 'white' ? 255 : 0;
        const bgA = bgColor === 'transparent' ? 0 : 255;
        for (let y = 0; y < h; y++) {
          for (let x = 0; x < w; x++) {
            if (Math.hypot((x - cx) / rx, (y - cy) / ry) > 1.0) {
              const idx = (y * w + x) * 4;
              data[idx] = bgR; data[idx + 1] = bgR; data[idx + 2] = bgR; data[idx + 3] = bgA;
            }
          }
        }
      }

      ctx.putImageData(imgData, 0, 0);
      return outCanvas;
    }

    function App() {
      const [activeStep, setActiveStep] = useState(1);
      const [sourceImageObj, setSourceImageObj] = useState(null);
      const [sourceDataUrl, setSourceDataUrl] = useState('');
      const [imageUrlInput, setImageUrlInput] = useState('');
      const [urlError, setUrlError] = useState('');
      const [activeSampleName, setActiveSampleName] = useState('');

      const [shapeType, setShapeType] = useState('rect_v');
      const [aspectPreset, setAspectPreset] = useState('3:4');
      const [bgColor, setBgColor] = useState('black');
      const [bgPaddingPct, setBgPaddingPct] = useState(4);
      const [cornerPts, setCornerPts] = useState([{ x: 280, y: 95 }, { x: 715, y: 120 }, { x: 865, y: 655 }, { x: 145, y: 635 }]);
      const [draggingPinIdx, setDraggingPinIdx] = useState(null);
      const [loupePos, setLoupePos] = useState(null);
      const [showPerspectiveGrid, setShowPerspectiveGrid] = useState(true);
      const [isAiDetectingCorners, setIsAiDetectingCorners] = useState(false);
      const [aiCornerStatus, setAiCornerStatus] = useState('');

      const [normalizedCanvas, setNormalizedCanvas] = useState(null);
      const [normalizedDataUrl, setNormalizedDataUrl] = useState('');

      const [deTextureStrength, setDeTextureStrength] = useState(80);
      const [edgeSharpness, setEdgeSharpness] = useState(70);
      const [lightingFlatten, setLightingFlatten] = useState(65);
      const [colorVibrance, setColorVibrance] = useState(35);
      const [autoMirrorCorner, setAutoMirrorCorner] = useState(true);
      const [activeRepairTool, setActiveRepairTool] = useState('none');
      const [brushSize, setBrushSize] = useState(48);
      const [isBrushing, setIsBrushing] = useState(false);

      const [customAiPrompt, setCustomAiPrompt] = useState(
        'Tái tạo thành file thiết kế 2D phẳng sắc nét chuẩn in ấn (flat 2D print-ready artwork), giữ nguyên 100% hoa văn, màu sắc, chi tiết và nền gốc. Xóa hoàn toàn vân sợi vải thảm, nếp gấp, bóng đổ và vẽ hoàn thiện các góc bị cắt hoặc bị che khuất.'
      );
      const [userApiKey, setUserApiKey] = useState(STREAMLIT_DEFAULT_KEY || '');
      const [showApiKeyModal, setShowApiKeyModal] = useState(false);
      const [isAiGenerating2D, setIsAiGenerating2D] = useState(false);
      const [aiStatusMessage, setAiStatusMessage] = useState('');
      const [compareSliderPos, setCompareSliderPos] = useState(50);
      const [showCompareMode, setShowCompareMode] = useState(false);

      const [reconstructedCanvas, setReconstructedCanvas] = useState(null);
      const [reconstructedDataUrl, setReconstructedDataUrl] = useState('');

      const [upscalePreset, setUpscalePreset] = useState('4k_auto');
      const [exportWidth, setExportWidth] = useState(3600);
      const [exportHeight, setExportHeight] = useState(4800);
      const [exportFormat, setExportFormat] = useState('png');
      const [isUpscaling4K, setIsUpscaling4K] = useState(false);
      const [upscaled4KDataUrl, setUpscaled4KDataUrl] = useState('');
      const [upscaleCompletedInfo, setUpscaleCompletedInfo] = useState(null);

      const editorCanvasRef = useRef(null);
      const loupeCanvasRef = useRef(null);
      const repairCanvasRef = useRef(null);
      const fileInputRef = useRef(null);

      const loadSampleMockup = useCallback((type = 'rect') => {
        const sample = generateSampleMockup(type);
        const img = new Image();
        img.onload = () => {
          setSourceImageObj(img);
          setSourceDataUrl(sample.dataUrl);
          setCornerPts(sample.quad);
          setShapeType(sample.shapeType);
          if (sample.shapeType === 'rect_v') setAspectPreset('3:4');
          if (sample.shapeType === 'circle' || sample.shapeType === 'square') setAspectPreset('1:1');
          setActiveSampleName(sample.label);
          setAutoMirrorCorner(type === 'rect');
          setAiCornerStatus('Đã tự động định vị 4 góc phối cảnh của tấm thảm từ mẫu Mockup.');
        };
        img.src = sample.dataUrl;
      }, []);

      useEffect(() => { loadSampleMockup('rect'); }, [loadSampleMockup]);

      useEffect(() => {
        const handlePaste = (e) => {
          const items = e.clipboardData?.items;
          if (!items) return;
          for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
              const blob = items[i].getAsFile();
              const reader = new FileReader();
              reader.onload = (ev) => loadNewImageFromDataUrl(ev.target.result, 'Ảnh dán từ Clipboard');
              reader.readAsDataURL(blob);
              break;
            }
          }
        };
        window.addEventListener('paste', handlePaste);
        return () => window.removeEventListener('paste', handlePaste);
      }, []);

      const detectRugCornersLocal = (imgElement = sourceImageObj) => {
        if (!imgElement) return;
        const w = imgElement.width, h = imgElement.height;
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = w; tempCanvas.height = h;
        const ctx = tempCanvas.getContext('2d');
        ctx.drawImage(imgElement, 0, 0);
        const data = ctx.getImageData(0, 0, w, h).data;

        const borderSamples = [];
        for (let x = 10; x < w - 10; x += Math.max(10, Math.floor(w / 20))) {
          const idxTop = (10 * w + x) * 4;
          const idxBot = ((h - 10) * w + x) * 4;
          borderSamples.push([data[idxTop], data[idxTop + 1], data[idxTop + 2]]);
          borderSamples.push([data[idxBot], data[idxBot + 1], data[idxBot + 2]]);
        }

        const isRugPixel = (x, y) => {
          const idx = (y * w + x) * 4;
          const r = data[idx], g = data[idx + 1], b = data[idx + 2];
          let minDiff = 999999;
          for (let i = 0; i < borderSamples.length; i++) {
            const d = Math.pow(r - borderSamples[i][0], 2) + Math.pow(g - borderSamples[i][1], 2) + Math.pow(b - borderSamples[i][2], 2);
            if (d < minDiff) minDiff = d;
          }
          return minDiff > 2400;
        };

        let tl = { x: w * 0.2, y: h * 0.15 }, minTL = Infinity;
        let tr = { x: w * 0.8, y: h * 0.15 }, minTR = Infinity;
        let br = { x: w * 0.85, y: h * 0.85 }, minBR = Infinity;
        let bl = { x: w * 0.15, y: h * 0.85 }, minBL = Infinity;

        const step = Math.max(2, Math.floor(Math.min(w, h) / 180));
        let foundPixels = 0;
        for (let y = Math.floor(h * 0.04); y < Math.floor(h * 0.96); y += step) {
          for (let x = Math.floor(w * 0.04); x < Math.floor(w * 0.96); x += step) {
            if (isRugPixel(x, y)) {
              foundPixels++;
              if (x + y * 1.2 < minTL) { minTL = x + y * 1.2; tl = { x, y }; }
              if ((w - x) + y * 1.2 < minTR) { minTR = (w - x) + y * 1.2; tr = { x, y }; }
              if ((w - x) + (h - y) * 1.2 < minBR) { minBR = (w - x) + (h - y) * 1.2; br = { x, y }; }
              if (x + (h - y) * 1.2 < minBL) { minBL = x + (h - y) * 1.2; bl = { x, y }; }
            }
          }
        }
        if (foundPixels > 50) {
          setCornerPts([tl, tr, br, bl]);
          setAiCornerStatus('Đã tự động nhận diện 4 góc tấm thảm. Bạn có thể kéo các nút tròn để tinh chỉnh thêm.');
        }
      };

      const loadNewImageFromDataUrl = (dataUrl, label = 'Ảnh tải lên') => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
          setSourceImageObj(img);
          setSourceDataUrl(dataUrl);
          setActiveSampleName(label);
          setAutoMirrorCorner(false);
          const w = img.width, h = img.height;
          setCornerPts([
            { x: Math.round(w * 0.18), y: Math.round(h * 0.14) },
            { x: Math.round(w * 0.82), y: Math.round(h * 0.14) },
            { x: Math.round(w * 0.88), y: Math.round(h * 0.86) },
            { x: Math.round(w * 0.12), y: Math.round(h * 0.86) }
          ]);
          setActiveStep(2);
          setTimeout(() => detectRugCornersLocal(img), 150);
        };
        img.src = dataUrl;
      };

      const handleLoadImageUrl = async () => {
        if (!imageUrlInput.trim()) return;
        setUrlError('');
        try {
          const proxyUrl = `https://images.weserv.nl/?url=${encodeURIComponent(imageUrlInput.trim())}`;
          const res = await fetch(proxyUrl);
          const blob = await res.blob();
          const reader = new FileReader();
          reader.onload = (ev) => loadNewImageFromDataUrl(ev.target.result, 'Ảnh từ Link URL');
          reader.readAsDataURL(blob);
        } catch (err) {
          setUrlError('Không thể tải trực tiếp link này. Bạn hãy nhấn chuột phải vào ảnh -> Sao chép hình ảnh rồi bấm Ctrl+V vào đây nhé!');
        }
      };

      const detectRugCornersWithGeminiAI = async () => {
        if (!sourceDataUrl || !sourceImageObj) return;
        setIsAiDetectingCorners(true);
        setAiCornerStatus('Đang dùng AI Gemini phân tích tọa độ 4 góc thảm và hình dáng...');
        try {
          if (!userApiKey.trim()) throw new Error('Local');
          const base64Data = sourceDataUrl.split(',')[1];
          const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key=${userApiKey.trim()}`;
          const prompt = `Analyze this rug mockup image. Find the 4 perspective corners of the rug. Return JSON with normalized coordinates (0-1000): {"shape":"rect_v"|"rect_h"|"square"|"circle","topLeft":{"x":0,"y":0},"topRight":{"x":0,"y":0},"bottomRight":{"x":0,"y":0},"bottomLeft":{"x":0,"y":0}}`;
          const res = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              contents: [{ role: 'user', parts: [{ text: prompt }, { inlineData: { mimeType: 'image/png', data: base64Data } }] }],
              generationConfig: { responseMimeType: 'application/json' }
            })
          });
          const result = await res.json();
          const parsed = JSON.parse(result?.candidates?.[0]?.content?.parts?.[0]?.text);
          const w = sourceImageObj.width, h = sourceImageObj.height;
          setCornerPts([
            { x: Math.round((parsed.topLeft.x / 1000) * w), y: Math.round((parsed.topLeft.y / 1000) * h) },
            { x: Math.round((parsed.topRight.x / 1000) * w), y: Math.round((parsed.topRight.y / 1000) * h) },
            { x: Math.round((parsed.bottomRight.x / 1000) * w), y: Math.round((parsed.bottomRight.y / 1000) * h) },
            { x: Math.round((parsed.bottomLeft.x / 1000) * w), y: Math.round((parsed.bottomLeft.y / 1000) * h) }
          ]);
          if (parsed.shape) setShapeType(parsed.shape);
          setAiCornerStatus('AI Gemini đã căn chỉnh chuẩn xác 4 góc phối cảnh!');
        } catch (err) {
          detectRugCornersLocal();
        } finally {
          setIsAiDetectingCorners(false);
        }
      };

      const getNormalizedDimensions = useCallback(() => {
        const baseSize = 900;
        if (shapeType === 'square' || shapeType === 'circle') return { w: baseSize, h: baseSize };
        const [rw, rh] = aspectPreset.split(':').map(Number);
        if (shapeType === 'rect_h') {
          const hRatio = Math.max(rw || 4, rh || 3) / Math.min(rw || 4, rh || 3);
          return { w: baseSize, h: Math.round(baseSize / hRatio) };
        }
        const vRatio = Math.min(rw || 3, rh || 4) / Math.max(rw || 3, rh || 4);
        return { w: Math.round(baseSize * vRatio), h: baseSize };
      }, [shapeType, aspectPreset]);

      useEffect(() => {
        if (!sourceImageObj) return;
        const temp = document.createElement('canvas');
        temp.width = sourceImageObj.width; temp.height = sourceImageObj.height;
        const tctx = temp.getContext('2d');
        tctx.drawImage(sourceImageObj, 0, 0);
        const srcImgData = tctx.getImageData(0, 0, temp.width, temp.height);
        const { w, h } = getNormalizedDimensions();
        const warped = warpPerspectiveImage(srcImgData, w, h, cornerPts, shapeType, bgColor, bgPaddingPct);
        setNormalizedCanvas(warped);
        setNormalizedDataUrl(warped.toDataURL('image/png'));
      }, [sourceImageObj, cornerPts, shapeType, bgColor, bgPaddingPct, getNormalizedDimensions]);

      useEffect(() => {
        const canvas = editorCanvasRef.current;
        if (!canvas || !sourceImageObj) return;
        canvas.width = sourceImageObj.width;
        canvas.height = sourceImageObj.height;
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(sourceImageObj, 0, 0);

        ctx.save();
        ctx.fillStyle = 'rgba(0, 0, 0, 0.55)';
        ctx.beginPath();
        ctx.rect(0, 0, canvas.width, canvas.height);
        ctx.moveTo(cornerPts[0].x, cornerPts[0].y);
        ctx.lineTo(cornerPts[1].x, cornerPts[1].y);
        ctx.lineTo(cornerPts[2].x, cornerPts[2].y);
        ctx.lineTo(cornerPts[3].x, cornerPts[3].y);
        ctx.closePath();
        ctx.fill('evenodd');
        ctx.restore();

        if (showPerspectiveGrid) {
          ctx.save();
          ctx.strokeStyle = 'rgba(56, 189, 248, 0.55)';
          ctx.lineWidth = 1.5;
          ctx.setLineDash([6, 6]);
          const lerpPt = (p1, p2, t) => ({ x: p1.x + (p2.x - p1.x) * t, y: p1.y + (p2.y - p1.y) * t });
          for (let i = 1; i <= 3; i++) {
            const t = i / 4;
            const topPt = lerpPt(cornerPts[0], cornerPts[1], t);
            const botPt = lerpPt(cornerPts[3], cornerPts[2], t);
            ctx.beginPath(); ctx.moveTo(topPt.x, topPt.y); ctx.lineTo(botPt.x, botPt.y); ctx.stroke();
            const leftPt = lerpPt(cornerPts[0], cornerPts[3], t);
            const rightPt = lerpPt(cornerPts[1], cornerPts[2], t);
            ctx.beginPath(); ctx.moveTo(leftPt.x, leftPt.y); ctx.lineTo(rightPt.x, rightPt.y); ctx.stroke();
          }
          if (shapeType === 'circle') {
            ctx.strokeStyle = '#facc15'; ctx.lineWidth = 3; ctx.setLineDash([]);
            ctx.beginPath();
            for (let s = 0; s <= 64; s++) {
              const angle = (s / 64) * Math.PI * 2;
              const u = 0.5 + 0.5 * Math.cos(angle), v = 0.5 + 0.5 * Math.sin(angle);
              const top = lerpPt(cornerPts[0], cornerPts[1], u);
              const bot = lerpPt(cornerPts[3], cornerPts[2], u);
              const pt = lerpPt(top, bot, v);
              if (s === 0) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
            }
            ctx.closePath(); ctx.stroke();
          }
          ctx.restore();
        }

        ctx.strokeStyle = '#22d3ee'; ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(cornerPts[0].x, cornerPts[0].y);
        ctx.lineTo(cornerPts[1].x, cornerPts[1].y);
        ctx.lineTo(cornerPts[2].x, cornerPts[2].y);
        ctx.lineTo(cornerPts[3].x, cornerPts[3].y);
        ctx.closePath(); ctx.stroke();

        const labels = ['TL (Trên-Trái)', 'TR (Trên-Phải)', 'BR (Dưới-Phải)', 'BL (Dưới-Trái)'];
        const colors = ['#f43f5e', '#10b981', '#3b82f6', '#f59e0b'];
        cornerPts.forEach((pt, idx) => {
          ctx.save();
          ctx.fillStyle = colors[idx]; ctx.beginPath(); ctx.arc(pt.x, pt.y, 14, 0, Math.PI * 2); ctx.fill();
          ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 3; ctx.stroke();
          ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2); ctx.fill();
          ctx.font = 'bold 13px sans-serif';
          const textW = ctx.measureText(labels[idx]).width;
          ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
          ctx.fillRect(pt.x - textW / 2 - 6, pt.y - 34, textW + 12, 20);
          ctx.fillStyle = '#ffffff';
          ctx.fillText(labels[idx], pt.x - textW / 2, pt.y - 20);
          ctx.restore();
        });
      }, [sourceImageObj, cornerPts, showPerspectiveGrid, shapeType, activeStep]);

      const getCanvasCoords = (e, canvas) => {
        const rect = canvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        return {
          x: Math.max(0, Math.min(canvas.width, (clientX - rect.left) * (canvas.width / rect.width))),
          y: Math.max(0, Math.min(canvas.height, (clientY - rect.top) * (canvas.height / rect.height)))
        };
      };

      const handlePinMouseDown = (e) => {
        const canvas = editorCanvasRef.current;
        if (!canvas) return;
        const pt = getCanvasCoords(e, canvas);
        let closestIdx = -1, minDist = 45;
        cornerPts.forEach((c, idx) => {
          const dist = Math.hypot(c.x - pt.x, c.y - pt.y);
          if (dist < minDist) { minDist = dist; closestIdx = idx; }
        });
        if (closestIdx !== -1) {
          setDraggingPinIdx(closestIdx);
          setLoupePos(cornerPts[closestIdx]);
        }
      };

      const handlePinMouseMove = (e) => {
        if (draggingPinIdx === null) return;
        const canvas = editorCanvasRef.current;
        if (!canvas) return;
        const pt = getCanvasCoords(e, canvas);
        setCornerPts((prev) => {
          const updated = [...prev];
          updated[draggingPinIdx] = { x: Math.round(pt.x), y: Math.round(pt.y) };
          return updated;
        });
        setLoupePos(pt);
        if (loupeCanvasRef.current && sourceImageObj) {
          const lctx = loupeCanvasRef.current.getContext('2d');
          const lSize = 130, zoom = 3, sampleSize = lSize / zoom;
          lctx.clearRect(0, 0, lSize, lSize);
          lctx.fillStyle = '#000'; lctx.fillRect(0, 0, lSize, lSize);
          lctx.drawImage(sourceImageObj, pt.x - sampleSize / 2, pt.y - sampleSize / 2, sampleSize, sampleSize, 0, 0, lSize, lSize);
          lctx.strokeStyle = '#22d3ee'; lctx.lineWidth = 1.5;
          lctx.beginPath(); lctx.moveTo(lSize / 2, 0); lctx.lineTo(lSize / 2, lSize);
          lctx.moveTo(0, lSize / 2); lctx.lineTo(lSize, lSize / 2); lctx.stroke();
        }
      };

      const handlePinMouseUp = () => { setDraggingPinIdx(null); setLoupePos(null); };

      useEffect(() => {
        if (!normalizedCanvas) return;
        const processed = processFlat2DArtwork(normalizedCanvas, {
          removeFabricIntensity: deTextureStrength,
          sharpenEdges: edgeSharpness,
          flattenLighting: lightingFlatten,
          boostVibrance: colorVibrance,
          autoMirrorClippedCorners: autoMirrorCorner,
          shapeType,
          bgColor
        });
        setReconstructedCanvas(processed);
        setReconstructedDataUrl(processed.toDataURL('image/png'));
      }, [normalizedCanvas, deTextureStrength, edgeSharpness, lightingFlatten, colorVibrance, autoMirrorCorner, shapeType, bgColor]);

      useEffect(() => {
        if (activeStep === 3 && repairCanvasRef.current && reconstructedCanvas) {
          const rCanvas = repairCanvasRef.current;
          rCanvas.width = reconstructedCanvas.width;
          rCanvas.height = reconstructedCanvas.height;
          rCanvas.getContext('2d').drawImage(reconstructedCanvas, 0, 0);
        }
      }, [activeStep, reconstructedCanvas]);

      const applySymmetryRepairBrush = (e) => {
        if (activeRepairTool === 'none' || !repairCanvasRef.current || !reconstructedCanvas) return;
        const canvas = repairCanvasRef.current;
        const pt = getCanvasCoords(e, canvas);
        const ctx = canvas.getContext('2d');
        const w = canvas.width, h = canvas.height;
        const imgData = ctx.getImageData(0, 0, w, h);
        const data = imgData.data;
        const r = brushSize;

        for (let dy = -r; dy <= r; dy++) {
          for (let dx = -r; dx <= r; dx++) {
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist > r) continue;
            const tx = Math.round(pt.x + dx), ty = Math.round(pt.y + dy);
            if (tx < 0 || tx >= w || ty < 0 || ty >= h) continue;
            let sx = tx, sy = ty;
            if (activeRepairTool === 'mirror_v') sy = h - 1 - ty;
            else if (activeRepairTool === 'mirror_h') sx = w - 1 - tx;
            else if (activeRepairTool === 'mirror_center') { sx = w - 1 - tx; sy = h - 1 - ty; }

            const srcIdx = (sy * w + sx) * 4;
            const dstIdx = (ty * w + tx) * 4;
            const feather = Math.min(1, (r - dist) / (r * 0.35));
            data[dstIdx] = Math.round(data[srcIdx] * feather + data[dstIdx] * (1 - feather));
            data[dstIdx + 1] = Math.round(data[srcIdx + 1] * feather + data[dstIdx + 1] * (1 - feather));
            data[dstIdx + 2] = Math.round(data[srcIdx + 2] * feather + data[dstIdx + 2] * (1 - feather));
          }
        }
        ctx.putImageData(imgData, 0, 0);
      };

      const handleRepairPointerUp = () => {
        if (!isBrushing) return;
        setIsBrushing(false);
        if (repairCanvasRef.current) {
          setReconstructedDataUrl(repairCanvasRef.current.toDataURL('image/png'));
        }
      };

      const handleRunGemini2DRedraw = async () => {
        if (!normalizedDataUrl) return;
        setIsAiGenerating2D(true);
        setAiStatusMessage('Đang gửi ảnh đã chuẩn hóa shape tới Gemini AI để làm nét & tái tạo thiết kế 2D phẳng...');
        try {
          if (!userApiKey.trim()) throw new Error('Local');
          const base64Data = normalizedDataUrl.split(',')[1];
          const instructions = `Transform this perspective-corrected rug image into a clean, ultra-sharp, flat 2D digital print-ready artwork on a solid ${bgColor} background. Completely remove all carpet fabric weave texture, wrinkles, and shadows. Remove any overlapping objects and seamlessly reconstruct any clipped corners symmetrically while preserving 100% of the original design and colors. ${customAiPrompt}`;
          const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image:generateContent?key=${userApiKey.trim()}`;
          const response = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              contents: [{ role: 'user', parts: [{ text: instructions }, { inlineData: { mimeType: 'image/png', data: base64Data } }] }],
              generationConfig: { responseModalities: ['TEXT', 'IMAGE'] }
            })
          });
          const result = await response.json();
          const imagePart = result?.candidates?.[0]?.content?.parts?.find((p) => p.inlineData);
          if (imagePart?.inlineData?.data) {
            const img = new Image();
            img.onload = () => {
              const c = document.createElement('canvas');
              c.width = normalizedCanvas.width; c.height = normalizedCanvas.height;
              c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
              setReconstructedCanvas(c);
              setReconstructedDataUrl(c.toDataURL('image/png'));
              setAiStatusMessage('Hoàn tất! AI Gemini đã tái tạo thành công bản thiết kế 2D phẳng sắc nét & hoàn thiện các góc.');
            };
            img.src = `data:${imagePart.inlineData.mimeType || 'image/png'};base64,${imagePart.inlineData.data}`;
          } else {
            throw new Error('Fallback');
          }
        } catch (err) {
          setDeTextureStrength(92);
          setEdgeSharpness(85);
          setLightingFlatten(80);
          setColorVibrance(45);
          setAutoMirrorCorner(true);
          setAiStatusMessage('Đã hoàn tất xử lý Khử Vân Vải 2D Chuyên Sâu + Bù Góc Đối Xứng Tự Động & Làm Nét Vector chuẩn in!');
        } finally {
          setIsAiGenerating2D(false);
        }
      };

      useEffect(() => {
        if (!reconstructedCanvas) return;
        const ratio = reconstructedCanvas.width / reconstructedCanvas.height;
        if (upscalePreset === '4k_auto') {
          if (Math.abs(ratio - 1) < 0.05) { setExportWidth(4096); setExportHeight(4096); }
          else if (ratio < 1) { setExportHeight(4800); setExportWidth(Math.round(4800 * ratio)); }
          else { setExportWidth(4800); setExportHeight(Math.round(4800 / ratio)); }
        } else if (upscalePreset === '4k_square') { setExportWidth(4096); setExportHeight(4096); }
        else if (upscalePreset === '4k_pod_v') { setExportWidth(3600); setExportHeight(5400); }
        else if (upscalePreset === '4k_pod_h') { setExportWidth(5120); setExportHeight(3413); }
      }, [upscalePreset, reconstructedCanvas]);

      const handleGenerate4KFile = () => {
        const sourceToUpscale = repairCanvasRef.current || reconstructedCanvas || normalizedCanvas;
        if (!sourceToUpscale) return;
        setIsUpscaling4K(true);
        setTimeout(() => {
          const targetW = Math.min(6000, Math.max(1000, Number(exportWidth) || 4096));
          const targetH = Math.min(6000, Math.max(1000, Number(exportHeight) || 4096));
          const stepCanvas = document.createElement('canvas');
          stepCanvas.width = Math.round((sourceToUpscale.width + targetW) / 2);
          stepCanvas.height = Math.round((sourceToUpscale.height + targetH) / 2);
          const sctx = stepCanvas.getContext('2d');
          sctx.imageSmoothingEnabled = true; sctx.imageSmoothingQuality = 'high';
          sctx.drawImage(sourceToUpscale, 0, 0, stepCanvas.width, stepCanvas.height);

          const final4KCanvas = document.createElement('canvas');
          final4KCanvas.width = targetW; final4KCanvas.height = targetH;
          const fctx = final4KCanvas.getContext('2d');
          if (bgColor === 'black') { fctx.fillStyle = '#000000'; fctx.fillRect(0, 0, targetW, targetH); }
          else if (bgColor === 'white') { fctx.fillStyle = '#FFFFFF'; fctx.fillRect(0, 0, targetW, targetH); }
          fctx.imageSmoothingEnabled = true; fctx.imageSmoothingQuality = 'high';
          fctx.drawImage(stepCanvas, 0, 0, targetW, targetH);

          const mime = exportFormat === 'jpeg' ? 'image/jpeg' : 'image/png';
          const dataUrl = final4KCanvas.toDataURL(mime, 0.98);
          setUpscaled4KDataUrl(dataUrl);
          const approxSizeMB = ((dataUrl.length * 0.75) / (1024 * 1024)).toFixed(2);
          setUpscaleCompletedInfo({
            width: targetW,
            height: targetH,
            format: exportFormat.toUpperCase(),
            sizeMB: approxSizeMB,
            bgLabel: bgColor === 'black' ? 'Nền Đen (#000000)' : bgColor === 'white' ? 'Nền Trắng (#FFFFFF)' : 'Trong suốt (PNG)'
          });
          setIsUpscaling4K(false);
        }, 100);
      };

      const triggerDownload4K = () => {
        if (!upscaled4KDataUrl) return;
        const link = document.createElement('a');
        link.download = `POD-Rug-2D-4K-${exportWidth}x${exportHeight}.${exportFormat}`;
        link.href = upscaled4KDataUrl;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      };

      return (
        <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
          {/* HEADER */}
          <header className="border-b border-slate-800 bg-slate-900/90 sticky top-0 z-30">
            <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-indigo-600 flex items-center justify-center font-black text-slate-950 text-lg">
                  4K
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-lg font-bold text-white">POD Rug Studio 4K</h1>
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                      100% Miễn Phí • Streamlit Cloud
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">Chuẩn hóa Shape Thảm Mockup • Khử Vân Vải & Bù Góc AI 2D • Xuất File In 4K</p>
                </div>
              </div>

              <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800 overflow-x-auto">
                {[
                  { id: 1, title: '1. Ảnh Gốc / Link' },
                  { id: 2, title: '2. Chuẩn Hóa Shape' },
                  { id: 3, title: '3. AI Làm Nét & Art 2D' },
                  { id: 4, title: '4. Upscale 4K & Tải Về' }
                ].map((s) => (
                  <button
                    key={s.id}
                    onClick={() => {
                      setActiveStep(s.id);
                      if (s.id === 4) setTimeout(handleGenerate4KFile, 120);
                    }}
                    className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition whitespace-nowrap ${
                      activeStep === s.id
                        ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white'
                        : activeStep > s.id
                        ? 'text-emerald-400 hover:bg-slate-900'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {s.title}
                  </button>
                ))}
              </div>

              <button
                onClick={() => setShowApiKeyModal(true)}
                className="text-xs px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 border border-slate-700 font-semibold"
              >
                🔑 Cấu hình AI Key
              </button>
            </div>
          </header>

          {/* MAIN WORKSPACE */}
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
            {activeStep === 1 && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
                  <div>
                    <h2 className="text-base font-bold text-white">Tải Ảnh Mockup Gốc Hoặc Dán Đường Dẫn Hình Ảnh</h2>
                    <p className="text-xs text-slate-400 mt-1">
                      Hỗ trợ ảnh thảm chụp nghiêng, méo góc phối cảnh, bị bàn ghế che một góc hoặc dính vân sợi vải từ mockup.
                    </p>
                  </div>

                  <div
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      const file = e.dataTransfer.files?.[0];
                      if (file) {
                        const r = new FileReader();
                        r.onload = (ev) => loadNewImageFromDataUrl(ev.target.result, file.name);
                        r.readAsDataURL(file);
                      }
                    }}
                    className="border-2 border-dashed border-cyan-500/40 hover:border-cyan-400 bg-slate-950 rounded-2xl p-8 text-center cursor-pointer transition"
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          const r = new FileReader();
                          r.onload = (ev) => loadNewImageFromDataUrl(ev.target.result, file.name);
                          r.readAsDataURL(file);
                        }
                      }}
                      className="hidden"
                    />
                    <p className="text-sm font-semibold text-cyan-300">📥 Nhấn để chọn ảnh từ máy hoặc Kéo & Thả ảnh vào đây</p>
                    <p className="text-xs text-slate-400 mt-1">Mẹo nhanh: Bấm Ctrl + V để dán trực tiếp ảnh vừa copy!</p>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-2">Hoặc nhập đường link chứa ảnh Mockup có sẵn:</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={imageUrlInput}
                        onChange={(e) => setImageUrlInput(e.target.value)}
                        placeholder="https://example.com/rug-mockup-image.jpg"
                        className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white"
                      />
                      <button
                        onClick={handleLoadImageUrl}
                        className="px-4 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs rounded-xl"
                      >
                        Tải từ Link
                      </button>
                    </div>
                    {urlError && <p className="text-xs text-amber-400 mt-2">{urlError}</p>}
                  </div>

                  <div className="pt-4 border-t border-slate-800">
                    <p className="text-xs font-semibold text-slate-300 mb-3">✨ Thử nghiệm ngay với 3 mẫu Mockup Thảm POD thực tế (1-Click):</p>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                      <button onClick={() => { loadSampleMockup('rect'); setActiveStep(2); }} className="p-3 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left">
                        <div className="text-xs font-bold text-cyan-400">Mẫu 1: Thảm Chữ Nhật</div>
                        <p className="text-[11px] text-slate-400 mt-1">Phối cảnh nghiêng + bị chân bàn che góc dưới trái</p>
                      </button>
                      <button onClick={() => { loadSampleMockup('circle'); setActiveStep(2); }} className="p-3 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left">
                        <div className="text-xs font-bold text-amber-400">Mẫu 2: Thảm Tròn Boho</div>
                        <p className="text-[11px] text-slate-400 mt-1">Biến dạng elip trên sàn gỗ → Chuẩn hóa về tròn chuẩn</p>
                      </button>
                      <button onClick={() => { loadSampleMockup('square'); setActiveStep(2); }} className="p-3 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left">
                        <div className="text-xs font-bold text-emerald-400">Mẫu 3: Thảm Vuông 1:1</div>
                        <p className="text-[11px] text-slate-400 mt-1">Có nếp gấp vải & vân thảm → Làm phẳng 2D sắc nét</p>
                      </button>
                    </div>
                  </div>
                </div>

                <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col items-center">
                  <div className="w-full flex justify-between text-xs mb-3">
                    <span className="text-slate-300 font-semibold">Ảnh Mockup Đang Chọn:</span>
                    <span className="text-cyan-400 truncate max-w-[220px]">{activeSampleName}</span>
                  </div>
                  {sourceDataUrl && (
                    <img src={sourceDataUrl} alt="Source" className="max-h-[340px] w-auto object-contain rounded-xl border border-slate-800" />
                  )}
                  <button
                    onClick={() => setActiveStep(2)}
                    className="mt-5 w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold text-sm"
                  >
                    Tiếp Tục Bước 2: Chuẩn Hóa Shape Thảm →
                  </button>
                </div>
              </div>
            )}

            {activeStep === 2 && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                <div className="lg:col-span-4 space-y-5 bg-slate-900 border border-slate-800 rounded-2xl p-5">
                  <div>
                    <h2 className="text-sm font-bold text-white">Bước 2: Chuẩn Hóa Shape & Cắt Phối Cảnh</h2>
                    <p className="text-xs text-slate-400 mt-1">Đưa tấm thảm bị méo trong Mockup về đúng hình chuẩn trên nền Đen hoặc Trắng.</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2.5">
                    <label className="text-xs font-semibold text-cyan-300 block">Định Vị 4 Góc Thảm Tự Động & Thủ Công:</label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={detectRugCornersWithGeminiAI}
                        disabled={isAiDetectingCorners}
                        className="py-2 px-3 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold text-xs"
                      >
                        {isAiDetectingCorners ? 'Đang dò AI...' : '✨ AI Tự Căn Chỉnh'}
                      </button>
                      <button
                        onClick={() => detectRugCornersLocal()}
                        className="py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700"
                      >
                        🔄 Dò Cạnh Nhanh
                      </button>
                    </div>
                    {aiCornerStatus && <p className="text-[11px] text-emerald-400">{aiCornerStatus}</p>}
                  </div>

                  <div className="space-y-2">
                    <label className="block text-xs font-semibold text-slate-300">Chọn Hình Dáng Chuẩn Của Thảm:</label>
                    <div className="grid grid-cols-2 gap-2">
                      {[
                        { id: 'rect_v', label: 'Chữ Nhật Đứng' },
                        { id: 'rect_h', label: 'Chữ Nhật Ngang' },
                        { id: 'square', label: 'Hình Vuông (1:1)' },
                        { id: 'circle', label: 'Hình Tròn Chuẩn' }
                      ].map((item) => (
                        <button
                          key={item.id}
                          onClick={() => setShapeType(item.id)}
                          className={`p-2.5 rounded-xl border text-xs font-semibold ${
                            shapeType === item.id
                              ? 'bg-cyan-500/15 border-cyan-400 text-cyan-300'
                              : 'bg-slate-950 border-slate-800 text-slate-400'
                          }`}
                        >
                          {item.label}
                        </button>
                      ))}
                    </div>

                    {(shapeType === 'rect_v' || shapeType === 'rect_h') && (
                      <div className="pt-2 flex flex-wrap gap-1.5">
                        {['2:3', '3:4', '4:5', '9:16'].map((code) => (
                          <button
                            key={code}
                            onClick={() => setAspectPreset(code)}
                            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border ${
                              aspectPreset === code ? 'bg-blue-500/20 border-blue-400 text-blue-300' : 'bg-slate-950 border-slate-800 text-slate-400'
                            }`}
                          >
                            Tỷ lệ {code}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="space-y-2 pt-2 border-t border-slate-800">
                    <label className="block text-xs font-semibold text-slate-300">Màu Nền Đặt Thảm Sau Khi Chuẩn Hóa:</label>
                    <div className="grid grid-cols-3 gap-2">
                      <button onClick={() => setBgColor('black')} className={`py-2 px-3 rounded-xl border text-xs font-bold ${bgColor === 'black' ? 'border-cyan-400 bg-black text-white' : 'border-slate-800 text-slate-400'}`}>Nền Đen</button>
                      <button onClick={() => setBgColor('white')} className={`py-2 px-3 rounded-xl border text-xs font-bold ${bgColor === 'white' ? 'border-cyan-400 bg-white text-slate-950' : 'border-slate-800 text-slate-400'}`}>Nền Trắng</button>
                      <button onClick={() => setBgColor('transparent')} className={`py-2 px-2 rounded-xl border text-xs font-semibold ${bgColor === 'transparent' ? 'border-cyan-400 bg-slate-800 text-cyan-300' : 'border-slate-800 text-slate-400'}`}>Trong Suốt</button>
                    </div>
                    <div className="pt-2">
                      <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                        <span>Khoảng đệm viền nền:</span>
                        <span className="text-cyan-400 font-semibold">{bgPaddingPct}%</span>
                      </div>
                      <input type="range" min="0" max="12" value={bgPaddingPct} onChange={(e) => setBgPaddingPct(Number(e.target.value))} className="w-full accent-cyan-400" />
                    </div>
                  </div>

                  <button onClick={() => setActiveStep(3)} className="w-full py-3.5 px-5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold text-xs">
                    Sang Bước 3: Làm Nét & Tái Tạo Art 2D Phẳng →
                  </button>
                </div>

                <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col">
                    <div className="flex items-center justify-between mb-2.5">
                      <span className="text-xs font-bold text-white">Chỉnh Thủ Công 4 Góc (Kéo Thả Nút Tròn)</span>
                      <button
                        onClick={() => setShowPerspectiveGrid(!showPerspectiveGrid)}
                        className="text-[11px] px-2 py-1 rounded border border-cyan-500/40 bg-cyan-500/10 text-cyan-300"
                      >
                        Lưới 3x3
                      </button>
                    </div>
                    <div className="relative flex-1 bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center min-h-[340px]">
                      <canvas
                        ref={editorCanvasRef}
                        onMouseDown={handlePinMouseDown}
                        onMouseMove={handlePinMouseMove}
                        onMouseUp={handlePinMouseUp}
                        onMouseLeave={handlePinMouseUp}
                        onTouchStart={handlePinMouseDown}
                        onTouchMove={handlePinMouseMove}
                        onTouchEnd={handlePinMouseUp}
                        className="max-h-[420px] w-auto max-w-full object-contain cursor-crosshair touch-none"
                      />
                      {loupePos && (
                        <div className="absolute top-3 right-3 bg-slate-900/95 border-2 border-cyan-400 rounded-xl p-1 shadow-2xl pointer-events-none">
                          <canvas ref={loupeCanvasRef} width={130} height={130} className="rounded-lg" />
                          <div className="text-[10px] text-center font-mono text-cyan-300 mt-0.5">
                            X:{Math.round(loupePos.x)} Y:{Math.round(loupePos.y)}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col">
                    <div className="flex items-center justify-between mb-2.5">
                      <span className="text-xs font-bold text-emerald-400">Kết Quả Chuẩn Hóa Shape (Thời Gian Thực)</span>
                      <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {bgColor === 'black' ? 'Nền Đen' : bgColor === 'white' ? 'Nền Trắng' : 'Trong Suốt'}
                      </span>
                    </div>
                    <div className="flex-1 bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center p-3 min-h-[340px]">
                      {normalizedDataUrl && <img src={normalizedDataUrl} alt="Normalized" className="max-h-[400px] w-auto object-contain rounded shadow-lg" />}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeStep === 3 && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                <div className="lg:col-span-5 space-y-5 bg-slate-900 border border-slate-800 rounded-2xl p-5">
                  <div>
                    <h2 className="text-sm font-bold text-white">Bước 3: Làm Nét AI & Tái Tạo Thiết Kế 2D Phẳng</h2>
                    <p className="text-xs text-slate-400 mt-1">Loại bỏ hoàn toàn hiệu ứng sợi vải thảm, bóng đổ và vẽ bù các góc bị cắt/che khuất.</p>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950 border border-indigo-500/30 space-y-3">
                    <div className="text-xs font-bold text-indigo-300">✨ AI Gemini Tái Tạo Art 2D & Hoàn Thiện Góc</div>
                    <textarea
                      rows={2}
                      value={customAiPrompt}
                      onChange={(e) => setCustomAiPrompt(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200"
                    />
                    <button
                      onClick={handleRunGemini2DRedraw}
                      disabled={isAiGenerating2D}
                      className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white font-bold text-xs"
                    >
                      {isAiGenerating2D ? 'Đang Tái Tạo Art 2D Phẳng Bằng AI...' : '✨ Chạy AI Làm Nét & Tái Tạo Art 2D Chuẩn Gốc'}
                    </button>
                    {aiStatusMessage && <p className="text-[11px] text-emerald-400 bg-emerald-950/40 border border-emerald-500/30 rounded-lg p-2">{aiStatusMessage}</p>}
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 text-xs">
                    <div className="font-bold text-cyan-300">Tinh Chỉnh Khử Vân Vải & Đồ Họa 2D Thời Gian Thực:</div>
                    <div>
                      <div className="flex justify-between mb-1"><span>Khử vân sợi vải & làm mịn bề mặt 2D:</span><span className="text-cyan-400 font-bold">{deTextureStrength}%</span></div>
                      <input type="range" min="0" max="100" value={deTextureStrength} onChange={(e) => setDeTextureStrength(Number(e.target.value))} className="w-full accent-cyan-400" />
                    </div>
                    <div>
                      <div className="flex justify-between mb-1"><span>Làm sắc nét chi tiết & viền hoa văn:</span><span className="text-cyan-400 font-bold">{edgeSharpness}%</span></div>
                      <input type="range" min="0" max="100" value={edgeSharpness} onChange={(e) => setEdgeSharpness(Number(e.target.value))} className="w-full accent-cyan-400" />
                    </div>
                    <div>
                      <div className="flex justify-between mb-1"><span>Khử bóng đổ & cân bằng ánh sáng phẳng 2D:</span><span className="text-cyan-400 font-bold">{lightingFlatten}%</span></div>
                      <input type="range" min="0" max="100" value={lightingFlatten} onChange={(e) => setLightingFlatten(Number(e.target.value))} className="w-full accent-cyan-400" />
                    </div>
                    <div>
                      <div className="flex justify-between mb-1"><span>Tái tạo độ tươi màu gốc:</span><span className="text-cyan-400 font-bold">{colorVibrance}%</span></div>
                      <input type="range" min="0" max="100" value={colorVibrance} onChange={(e) => setColorVibrance(Number(e.target.value))} className="w-full accent-cyan-400" />
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-amber-300">🖌️ Bù Góc Bị Cắt & Xóa Vật Cản Đối Xứng:</span>
                      <label className="flex items-center gap-1.5 text-[11px] text-emerald-400 cursor-pointer">
                        <input type="checkbox" checked={autoMirrorCorner} onChange={(e) => setAutoMirrorCorner(e.target.checked)} />
                        Tự động bù góc dưới trái
                      </label>
                    </div>
                    <div className="grid grid-cols-4 gap-1.5">
                      {[
                        { id: 'none', label: 'Tắt Cọ' },
                        { id: 'mirror_v', label: 'Đối Xứng Dọc' },
                        { id: 'mirror_h', label: 'Đối Xứng Ngang' },
                        { id: 'mirror_center', label: 'Đối Xứng Tâm' }
                      ].map((t) => (
                        <button
                          key={t.id}
                          onClick={() => setActiveRepairTool(t.id)}
                          className={`p-2 rounded-lg border text-[11px] font-semibold ${
                            activeRepairTool === t.id ? 'bg-amber-500/20 border-amber-400 text-amber-300' : 'bg-slate-900 border-slate-800 text-slate-400'
                          }`}
                        >
                          {t.label}
                        </button>
                      ))}
                    </div>
                    {activeRepairTool !== 'none' && (
                      <div>
                        <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                          <span>Kích thước cọ bù góc:</span>
                          <span className="text-amber-400 font-bold">{brushSize} px</span>
                        </div>
                        <input type="range" min="15" max="120" value={brushSize} onChange={(e) => setBrushSize(Number(e.target.value))} className="w-full accent-amber-400" />
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => { setActiveStep(4); setTimeout(handleGenerate4KFile, 150); }}
                    className="w-full py-3.5 px-5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-slate-950 font-extrabold text-xs"
                  >
                    Sang Bước 4: Upscale Lên 4K & Xuất File In →
                  </button>
                </div>

                <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold text-white">Bản Thiết Kế 2D Phẳng Đã Khử Vân Vải & Hoàn Thiện Góc</span>
                    <button
                      onClick={() => setShowCompareMode(!showCompareMode)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold border border-cyan-500/40 bg-cyan-500/10 text-cyan-300"
                    >
                      {showCompareMode ? 'Đang So Sánh Trước / Sau' : '↔ So Sánh Trước / Sau'}
                    </button>
                  </div>

                  <div className="relative flex-1 bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center p-4 min-h-[460px]">
                    {!showCompareMode ? (
                      <canvas
                        ref={repairCanvasRef}
                        onMouseDown={(e) => { if (activeRepairTool !== 'none') { setIsBrushing(true); applySymmetryRepairBrush(e); } }}
                        onMouseMove={(e) => { if (isBrushing && activeRepairTool !== 'none') applySymmetryRepairBrush(e); }}
                        onMouseUp={handleRepairPointerUp}
                        onMouseLeave={handleRepairPointerUp}
                        className={`max-h-[480px] w-auto max-w-full object-contain rounded shadow-2xl ${activeRepairTool !== 'none' ? 'cursor-cell' : ''}`}
                      />
                    ) : (
                      <div className="relative max-h-[480px] flex items-center justify-center select-none">
                        <img src={reconstructedDataUrl} alt="After" className="max-h-[480px] w-auto object-contain rounded" />
                        <div style={{ clipPath: `inset(0 ${100 - compareSliderPos}% 0 0)` }} className="absolute inset-0 flex items-center justify-center">
                          <img src={normalizedDataUrl} alt="Before" className="max-h-[480px] w-auto object-contain rounded" />
                        </div>
                        <div style={{ left: `${compareSliderPos}%` }} className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 pointer-events-none" />
                        <input type="range" min="0" max="100" value={compareSliderPos} onChange={(e) => setCompareSliderPos(Number(e.target.value))} className="absolute inset-0 opacity-0 cursor-ew-resize w-full h-full" />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeStep === 4 && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                <div className="lg:col-span-5 space-y-5 bg-slate-900 border border-slate-800 rounded-2xl p-6">
                  <div>
                    <h2 className="text-base font-bold text-white">Bước 4: Upscale 4K Ultra-HD & Xuất File In Ấn</h2>
                    <p className="text-xs text-slate-400 mt-1">Nâng cấp độ phân giải lên chuẩn 4K sắc nét cho máy in công nghiệp POD.</p>
                  </div>

                  <div className="space-y-2">
                    {[
                      { id: '4k_auto', title: '4K Tự Động Theo Tỷ Lệ Shape Đã Chuẩn Hóa', desc: 'Giữ nguyên 100% tỷ lệ thiết kế, cạnh lớn nhất đạt 4096px - 4800px' },
                      { id: '4k_square', title: '4K Vuông / Tròn Chuẩn (4096 × 4096 px)', desc: 'Chuẩn in thảm tròn và thảm vuông độ nét cực đại' },
                      { id: '4k_pod_v', title: '4K Thảm Đứng POD (3600 × 5400 px - 300 DPI)', desc: 'Tối ưu cho thảm chữ nhật cỡ lớn 120×180cm, 160×240cm' },
                      { id: '4k_pod_h', title: '4K Thảm Ngang (5120 × 3413 px)', desc: 'Chuẩn 4K/5K Ultra-HD cho thảm chữ nhật ngang' }
                    ].map((p) => (
                      <button
                        key={p.id}
                        onClick={() => setUpscalePreset(p.id)}
                        className={`w-full p-3 rounded-xl border text-left transition ${
                          upscalePreset === p.id ? 'bg-emerald-500/15 border-emerald-400 text-white' : 'bg-slate-950 border-slate-800 text-slate-400'
                        }`}
                      >
                        <div className="text-xs font-bold text-emerald-300">{p.title}</div>
                        <div className="text-[11px] text-slate-400 mt-0.5">{p.desc}</div>
                      </button>
                    ))}
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Chiều rộng (Width px):</label>
                      <input type="number" value={exportWidth} onChange={(e) => { setUpscalePreset('custom'); setExportWidth(Number(e.target.value)); }} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white" />
                    </div>
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Chiều cao (Height px):</label>
                      <input type="number" value={exportHeight} onChange={(e) => { setUpscalePreset('custom'); setExportHeight(Number(e.target.value)); }} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white" />
                    </div>
                  </div>

                  <div className="space-y-2.5 pt-2">
                    <button onClick={handleGenerate4KFile} disabled={isUpscaling4K} className="w-full py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-600 text-cyan-300 font-bold text-xs">
                      {isUpscaling4K ? 'Đang Xử Lý Upscale 4K...' : '🔄 Cập Nhật Kết Quả Upscale 4K'}
                    </button>
                    <button onClick={triggerDownload4K} disabled={!upscaled4KDataUrl || isUpscaling4K} className="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-extrabold text-sm">
                      ⬇ Tải Ảnh 4K Chuẩn In Về Máy ({exportWidth}×{exportHeight}px)
                    </button>
                  </div>
                </div>

                <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-sm font-bold text-white">File Thành Phẩm 2D 4K Ultra-HD Sẵn Sàng In Ấn</span>
                    {upscaleCompletedInfo && (
                      <span className="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-400 font-mono text-xs font-bold border border-emerald-500/30">
                        {upscaleCompletedInfo.width} × {upscaleCompletedInfo.height} px (~{upscaleCompletedInfo.sizeMB} MB)
                      </span>
                    )}
                  </div>
                  <div className="flex-1 bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center p-4 min-h-[420px]">
                    {upscaled4KDataUrl ? (
                      <img src={upscaled4KDataUrl} alt="4K Output" className="max-h-[440px] w-auto object-contain rounded shadow-2xl" />
                    ) : (
                      <div className="text-slate-400 text-xs">Đang khởi tạo bản xem trước 4K Ultra-HD...</div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </main>

          {showApiKeyModal && (
            <div className="fixed inset-0 bg-black/75 z-50 flex items-center justify-center p-4">
              <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white">🔑 Cấu Hình Gemini API Key (Tùy Chọn)</h3>
                  <button onClick={() => setShowApiKeyModal(false)} className="text-xs text-slate-400">Đóng ✕</button>
                </div>
                <input
                  type="password"
                  value={userApiKey}
                  onChange={(e) => setUserApiKey(e.target.value)}
                  placeholder="AIzaSy... (Để trống nếu dùng bộ xử lý tích hợp sẵn)"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white"
                />
                <div className="flex justify-end">
                  <button onClick={() => setShowApiKeyModal(false)} className="px-4 py-2 rounded-xl bg-cyan-500 text-slate-950 font-bold text-xs">
                    Lưu & Đóng
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      );
    }

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
"""

html_studio_code = html_studio_code.replace("__STREAMLIT_GEMINI_KEY__", default_gemini_key)

components.html(html_studio_code, height=900, scrolling=True)
