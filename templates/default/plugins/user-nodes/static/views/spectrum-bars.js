// spectrum-bars: a bar chart of the latest spectrum. A starting point for
// your own plugin views (nonoha view SDK 1).
//
// How plugin views work
// - Files in <plugin>/static/ are served by the engine; views live in
//   static/views/ and are listed in static/views/manifest.json (same id,
//   inputs and settings as below, plus "module" and "suits").
// - The browser imports this file directly, so it is a plain ES module with
//   NO imports. The default export is the view definition with `sdk: 1`.
// - The host (editor node, or an app via mountView) calls mount(el, ctx) and
//   pushes port values with ctx.onValues. A value is { dataType, shape, array }:
//   shape[0] is the batch, `array` a typed array the host may reuse after
//   your callback returns, so copy what you keep.
// - Draw only inside ctx.requestFrame(draw): calls within one animation
//   frame coalesce, so fast inputs never draw more often than the screen.
// - Use ctx.theme colors only (background, text, textMuted, grid, accent,
//   series[]) so the view fits dark and light editors.

export default {
  sdk: 1,
  id: "spectrum-bars",
  title: "Spectrum bars",
  description: "Bar chart of the latest spectrum (one bar per bin).",
  inputs: [
    {
      name: "spectrum",
      // "f32": the whole value is one spectrum (SpectrumAnalyzer sends its bins as one batch).
      // "f32[?]": one spectrum per batch row; the last row is shown.
      accepts: ["f32", "f32[?]", "f64[?]"],
      description: "Magnitudes per bin",
    },
  ],
  settings: {
    max: { type: "number", default: 1, description: "Value at full height; 0 = the largest bin" },
  },
  size: { width: 320, height: 180 },

  mount(el, ctx) {
    const canvas = document.createElement("canvas")
    canvas.style.display = "block"
    el.appendChild(canvas)
    const g = canvas.getContext("2d")

    let width = 0
    let height = 0
    let bins = new Float32Array(0) // our own copy of the latest spectrum
    let count = 0

    // Size the canvas in CSS px, with a backing store at device resolution.
    function setSize(w, h) {
      width = w
      height = h
      const dpr = window.devicePixelRatio || 1
      canvas.style.width = `${w}px`
      canvas.style.height = `${h}px`
      canvas.width = Math.max(1, Math.round(w * dpr))
      canvas.height = Math.max(1, Math.round(h * dpr))
    }

    function draw() {
      const { background, accent, textMuted, grid } = ctx.theme
      g.setTransform(canvas.width / Math.max(1, width), 0, 0, canvas.height / Math.max(1, height), 0, 0)
      g.fillStyle = background
      g.fillRect(0, 0, width, height)
      if (count === 0) {
        g.fillStyle = textMuted
        g.textAlign = "center"
        g.textBaseline = "middle"
        g.font = `12px ${ctx.theme.fontFamily}`
        g.fillText("Waiting for a spectrum…", width / 2, height / 2)
        return
      }
      let max = Number(ctx.settings.max)
      if (!(max > 0)) {
        max = 0
        for (let i = 0; i < count; ++i) if (bins[i] > max) max = bins[i]
        if (!(max > 0)) max = 1
      }
      const pad = 8
      const w = width - 2 * pad
      const h = height - 2 * pad
      // Baseline.
      g.fillStyle = grid
      g.fillRect(pad, pad + h, w, 1)
      // One rect per bin, all in one fill call.
      const step = w / count
      const barWidth = Math.max(1, step * 0.8)
      g.fillStyle = accent
      g.beginPath()
      for (let i = 0; i < count; ++i) {
        const v = Math.min(1, Math.max(0, bins[i] / max))
        g.rect(pad + i * step, pad + h * (1 - v), barWidth, h * v)
      }
      g.fill()
    }

    // Values: copy the spectrum we show, then ask for a frame.
    const off = ctx.onValues("spectrum", values => {
      const value = values[0]
      if (!value) return
      const shape = value.shape
      // [N] (plain f32 port): all of it; [B, N]: the last row.
      const n = shape.length >= 2 ? shape[1] : shape[0]
      const offset = shape.length >= 2 ? (shape[0] - 1) * n : 0
      if (!(n > 0) || value.array.length < offset + n) return
      if (bins.length < n) bins = new Float32Array(n) // grow only when the size changes
      for (let i = 0; i < n; ++i) bins[i] = value.array[offset + i]
      count = n
      ctx.requestFrame(draw)
    })

    setSize(ctx.size.width, ctx.size.height)
    ctx.requestFrame(draw)

    // Everything is optional; destroy must undo what mount did.
    return {
      resize(w, h) {
        setSize(w, h)
        ctx.requestFrame(draw)
      },
      settingsChanged() {
        ctx.requestFrame(draw)
      },
      themeChanged() {
        ctx.requestFrame(draw)
      },
      destroy() {
        off()
        canvas.remove()
      },
    }
  },
}
