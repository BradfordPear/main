// Dependency-free PNG icon generator for the Dethrone PWA.
// Rasterizes a gold crown on a charcoal rounded square using only Node's zlib.
// Run: node scripts/gen-icons.mjs
import { deflateSync } from 'node:zlib'
import { writeFileSync, mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const outDir = join(__dirname, '..', 'public', 'icons')
mkdirSync(outDir, { recursive: true })

const CHARCOAL = [14, 14, 18]
const GOLD = [245, 196, 81]
const CYAN = [124, 245, 255]

function makeCanvas(size) {
  const buf = new Uint8Array(size * size * 4) // RGBA, transparent
  return { size, buf }
}
function setPx(c, x, y, [r, g, b], a = 255) {
  if (x < 0 || y < 0 || x >= c.size || y >= c.size) return
  const i = (y * c.size + x) * 4
  c.buf[i] = r; c.buf[i + 1] = g; c.buf[i + 2] = b; c.buf[i + 3] = a
}
function fillRoundedRect(c, x0, y0, w, h, radius, color) {
  for (let y = y0; y < y0 + h; y++) {
    for (let x = x0; x < x0 + w; x++) {
      const dx = Math.max(x0 + radius - x, x - (x0 + w - 1 - radius), 0)
      const dy = Math.max(y0 + radius - y, y - (y0 + h - 1 - radius), 0)
      if (dx * dx + dy * dy <= radius * radius) setPx(c, x, y, color)
    }
  }
}
function fillPolygon(c, pts, color) {
  const ys = pts.map((p) => p[1])
  const minY = Math.floor(Math.min(...ys))
  const maxY = Math.ceil(Math.max(...ys))
  for (let y = minY; y <= maxY; y++) {
    const xs = []
    for (let i = 0; i < pts.length; i++) {
      const [x1, y1] = pts[i]
      const [x2, y2] = pts[(i + 1) % pts.length]
      if ((y1 <= y && y2 > y) || (y2 <= y && y1 > y)) {
        xs.push(x1 + ((y - y1) / (y2 - y1)) * (x2 - x1))
      }
    }
    xs.sort((a, b) => a - b)
    for (let k = 0; k + 1 < xs.length; k += 2) {
      for (let x = Math.round(xs[k]); x < Math.round(xs[k + 1]); x++) setPx(c, x, y, color)
    }
  }
}
function fillCircle(c, cx, cy, r, color) {
  for (let y = cy - r; y <= cy + r; y++) {
    for (let x = cx - r; x <= cx + r; x++) {
      if ((x - cx) ** 2 + (y - cy) ** 2 <= r * r) setPx(c, x, y, color)
    }
  }
}

function drawIcon(size) {
  const c = makeCanvas(size)
  const s = size / 64 // scale factor from 64px design grid
  fillRoundedRect(c, 0, 0, size, size, 14 * s, CHARCOAL)
  // Crown body
  fillPolygon(
    c,
    [
      [12 * s, 44 * s],
      [10 * s, 22 * s],
      [22 * s, 32 * s],
      [32 * s, 15 * s],
      [42 * s, 32 * s],
      [54 * s, 22 * s],
      [52 * s, 44 * s],
    ],
    GOLD
  )
  fillRoundedRect(c, 12 * s, 45 * s, 40 * s, 7 * s, 2 * s, GOLD)
  // Jewels
  fillCircle(c, Math.round(32 * s), Math.round(15 * s), Math.round(3 * s), CYAN)
  fillCircle(c, Math.round(10 * s), Math.round(22 * s), Math.round(2.5 * s), CYAN)
  fillCircle(c, Math.round(54 * s), Math.round(22 * s), Math.round(2.5 * s), CYAN)
  return c
}

// ---- PNG encoding ----
function crc32(buf) {
  let crc = ~0
  for (let i = 0; i < buf.length; i++) {
    crc ^= buf[i]
    for (let j = 0; j < 8; j++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1))
  }
  return ~crc >>> 0
}
function chunk(type, data) {
  const typeBuf = Buffer.from(type, 'ascii')
  const body = Buffer.concat([typeBuf, data])
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length)
  const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(body))
  return Buffer.concat([len, body, crc])
}
function encodePNG(c) {
  const { size, buf } = c
  const raw = Buffer.alloc((size * 4 + 1) * size)
  for (let y = 0; y < size; y++) {
    raw[y * (size * 4 + 1)] = 0 // filter: none
    Buffer.from(buf.buffer, y * size * 4, size * 4).copy(raw, y * (size * 4 + 1) + 1)
  }
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])
  const ihdr = Buffer.alloc(13)
  ihdr.writeUInt32BE(size, 0); ihdr.writeUInt32BE(size, 4)
  ihdr[8] = 8; ihdr[9] = 6 // 8-bit, RGBA
  return Buffer.concat([
    sig,
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw)),
    chunk('IEND', Buffer.alloc(0)),
  ])
}

for (const size of [192, 512]) {
  const png = encodePNG(drawIcon(size))
  writeFileSync(join(outDir, `icon-${size}.png`), png)
  console.log(`wrote icons/icon-${size}.png (${png.length} bytes)`)
}
