"""
6-DOF Robot Name-Writing Demo — Capstone UI (PyQt5)
---------------------------------------------------
Type a name -> render as a simple single-stroke font -> export as [x, y, z]
coordinates (in mm) for the robot to execute.

Output is a 2D list: [[x, y, z], [x, y, z], ...]
  * z = pen_up_z   -> pen raised (travel between strokes)
  * z = pen_down_z -> pen lowered (drawing a stroke)

Designed for a weak 6-DOF robot: uses a skeleton (single-line) plotter font,
no filled shapes, very few pen-up/down transitions, only straight segments.

Run in Spyder (F5) or from a terminal:
    python robot_name_ui.py

Dependencies: PyQt5 (bundled with Spyder/Anaconda; else `pip install PyQt5`).
"""

import sys

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


# ---------------------------------------------------------------------------
# Single-stroke plotter font
# ---------------------------------------------------------------------------
# Each character is a list of strokes. Each stroke is a list of (x, y)
# points in the character's own 0..1 cell, where (0, 0) is the BOTTOM-LEFT
# and (1, 1) is the TOP-RIGHT (standard math orientation — will be flipped
# when rendered onto the screen canvas which has y growing downward).
#
# Curves are approximated by short straight segments so the G-code is
# simple G1 moves (no arcs), which is easy on a weak robot.

FONT = {
    ' ': [],
    'A': [
        [(0.0, 0.0), (0.5, 1.0), (1.0, 0.0)],
        [(0.2, 0.35), (0.8, 0.35)],
    ],
    'B': [
        [(0.0, 0.0), (0.0, 1.0), (0.7, 1.0), (0.9, 0.85),
         (0.9, 0.65), (0.7, 0.5), (0.0, 0.5)],
        [(0.7, 0.5), (0.9, 0.35), (0.9, 0.15), (0.7, 0.0), (0.0, 0.0)],
    ],
    'C': [
        [(1.0, 0.85), (0.8, 1.0), (0.2, 1.0), (0.0, 0.8),
         (0.0, 0.2), (0.2, 0.0), (0.8, 0.0), (1.0, 0.15)],
    ],
    'D': [
        [(0.0, 0.0), (0.0, 1.0), (0.7, 1.0), (1.0, 0.7),
         (1.0, 0.3), (0.7, 0.0), (0.0, 0.0)],
    ],
    'E': [
        [(1.0, 1.0), (0.0, 1.0), (0.0, 0.0), (1.0, 0.0)],
        [(0.0, 0.5), (0.7, 0.5)],
    ],
    'F': [
        [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0)],
        [(0.0, 0.5), (0.7, 0.5)],
    ],
    'G': [
        [(1.0, 0.85), (0.8, 1.0), (0.2, 1.0), (0.0, 0.8),
         (0.0, 0.2), (0.2, 0.0), (0.8, 0.0), (1.0, 0.2),
         (1.0, 0.5), (0.5, 0.5)],
    ],
    'H': [
        [(0.0, 0.0), (0.0, 1.0)],
        [(0.0, 0.5), (1.0, 0.5)],
        [(1.0, 0.0), (1.0, 1.0)],
    ],
    'I': [
        [(0.5, 0.0), (0.5, 1.0)],
    ],
    'J': [
        [(1.0, 1.0), (1.0, 0.2), (0.8, 0.0), (0.2, 0.0), (0.0, 0.2)],
    ],
    'K': [
        [(0.0, 0.0), (0.0, 1.0)],
        [(1.0, 1.0), (0.0, 0.5), (1.0, 0.0)],
    ],
    'L': [
        [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0)],
    ],
    'M': [
        [(0.0, 0.0), (0.0, 1.0), (0.5, 0.4), (1.0, 1.0), (1.0, 0.0)],
    ],
    'N': [
        [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)],
    ],
    'O': [
        [(0.2, 1.0), (0.8, 1.0), (1.0, 0.8), (1.0, 0.2),
         (0.8, 0.0), (0.2, 0.0), (0.0, 0.2), (0.0, 0.8), (0.2, 1.0)],
    ],
    'P': [
        [(0.0, 0.0), (0.0, 1.0), (0.7, 1.0), (0.95, 0.85),
         (0.95, 0.65), (0.7, 0.5), (0.0, 0.5)],
    ],
    'Q': [
        [(0.2, 1.0), (0.8, 1.0), (1.0, 0.8), (1.0, 0.2),
         (0.8, 0.0), (0.2, 0.0), (0.0, 0.2), (0.0, 0.8), (0.2, 1.0)],
        [(0.6, 0.25), (1.0, -0.1)],
    ],
    'R': [
        [(0.0, 0.0), (0.0, 1.0), (0.7, 1.0), (0.95, 0.85),
         (0.95, 0.65), (0.7, 0.5), (0.0, 0.5)],
        [(0.5, 0.5), (1.0, 0.0)],
    ],
    'S': [
        [(1.0, 0.85), (0.8, 1.0), (0.2, 1.0), (0.0, 0.85),
         (0.0, 0.65), (0.2, 0.5), (0.8, 0.5), (1.0, 0.35),
         (1.0, 0.15), (0.8, 0.0), (0.2, 0.0), (0.0, 0.15)],
    ],
    'T': [
        [(0.0, 1.0), (1.0, 1.0)],
        [(0.5, 1.0), (0.5, 0.0)],
    ],
    'U': [
        [(0.0, 1.0), (0.0, 0.2), (0.2, 0.0), (0.8, 0.0), (1.0, 0.2), (1.0, 1.0)],
    ],
    'V': [
        [(0.0, 1.0), (0.5, 0.0), (1.0, 1.0)],
    ],
    'W': [
        [(0.0, 1.0), (0.2, 0.0), (0.5, 0.6), (0.8, 0.0), (1.0, 1.0)],
    ],
    'X': [
        [(0.0, 0.0), (1.0, 1.0)],
        [(0.0, 1.0), (1.0, 0.0)],
    ],
    'Y': [
        [(0.0, 1.0), (0.5, 0.5), (1.0, 1.0)],
        [(0.5, 0.5), (0.5, 0.0)],
    ],
    'Z': [
        [(0.0, 1.0), (1.0, 1.0), (0.0, 0.0), (1.0, 0.0)],
    ],
    # Numbers
    '0': [
        [(0.2, 1.0), (0.8, 1.0), (1.0, 0.8), (1.0, 0.2),
         (0.8, 0.0), (0.2, 0.0), (0.0, 0.2), (0.0, 0.8), (0.2, 1.0)],
    ],
    '1': [
        [(0.2, 0.8), (0.5, 1.0), (0.5, 0.0)],
        [(0.2, 0.0), (0.8, 0.0)],
    ],
    '2': [
        [(0.0, 0.85), (0.2, 1.0), (0.8, 1.0), (1.0, 0.85),
         (1.0, 0.65), (0.0, 0.0), (1.0, 0.0)],
    ],
    '3': [
        [(0.0, 0.85), (0.2, 1.0), (0.8, 1.0), (1.0, 0.85),
         (1.0, 0.65), (0.8, 0.5), (0.3, 0.5)],
        [(0.8, 0.5), (1.0, 0.35), (1.0, 0.15), (0.8, 0.0),
         (0.2, 0.0), (0.0, 0.15)],
    ],
    '4': [
        [(0.8, 0.0), (0.8, 1.0), (0.0, 0.35), (1.0, 0.35)],
    ],
    '5': [
        [(1.0, 1.0), (0.0, 1.0), (0.0, 0.55), (0.8, 0.55),
         (1.0, 0.4), (1.0, 0.15), (0.8, 0.0), (0.2, 0.0), (0.0, 0.15)],
    ],
    '6': [
        [(1.0, 0.85), (0.8, 1.0), (0.2, 1.0), (0.0, 0.8),
         (0.0, 0.2), (0.2, 0.0), (0.8, 0.0), (1.0, 0.2),
         (1.0, 0.35), (0.8, 0.5), (0.2, 0.5), (0.0, 0.35)],
    ],
    '7': [
        [(0.0, 1.0), (1.0, 1.0), (0.3, 0.0)],
    ],
    '8': [
        [(0.5, 0.5), (0.2, 0.5), (0.0, 0.35), (0.0, 0.15),
         (0.2, 0.0), (0.8, 0.0), (1.0, 0.15), (1.0, 0.35),
         (0.8, 0.5), (0.2, 0.5), (0.0, 0.65), (0.0, 0.85),
         (0.2, 1.0), (0.8, 1.0), (1.0, 0.85), (1.0, 0.65),
         (0.8, 0.5)],
    ],
    '9': [
        [(1.0, 0.5), (0.2, 0.5), (0.0, 0.65), (0.0, 0.85),
         (0.2, 1.0), (0.8, 1.0), (1.0, 0.85), (1.0, 0.2),
         (0.8, 0.0), (0.2, 0.0), (0.0, 0.15)],
    ],
    # Common name punctuation
    '.': [[(0.45, 0.05), (0.5, 0.0), (0.5, 0.05), (0.45, 0.05)]],
    "'": [[(0.5, 1.0), (0.45, 0.75)]],
    '-': [[(0.2, 0.5), (0.8, 0.5)]],
}

# Character cell widths (relative — most letters are ~0.7 wide of 1.0 cell).
CHAR_WIDTH = {ch: 0.7 for ch in FONT}
for narrow in "I.'":
    CHAR_WIDTH[narrow] = 0.35
for wide in "MW":
    CHAR_WIDTH[wide] = 0.9
CHAR_WIDTH[' '] = 0.5


def text_to_strokes(text, top=0.15, bottom=0.75, left=0.08, right=0.92,
                    letter_spacing=0.15):
    """Lay out `text` as a list of strokes in 0..1 canvas coords.

    Text is scaled to fit inside the rectangle bounded by (left, top) and
    (right, bottom). Output strokes use screen coords: (0,0) = top-left,
    (1,1) = bottom-right.

    Each letter's design uses the full 0..1 range in x, but is rendered into
    a cell of width CHAR_WIDTH[c] so narrow letters like I are actually
    narrow and wide letters like M are actually wide — no overlap.
    """
    if not text:
        return []

    # Measure total width in "em" units
    unit_widths = [CHAR_WIDTH.get(c.upper(), 0.7) for c in text]
    n = len(text)
    total_units = sum(unit_widths) + letter_spacing * max(0, n - 1)
    if total_units <= 0:
        return []

    avail_w = right - left
    avail_h = bottom - top

    # Uniform scale so letters keep their designed aspect ratio
    scale_w = avail_w / total_units
    scale_h = avail_h  # letter design height is 1.0 units
    scale = min(scale_w, scale_h)

    rendered_w = total_units * scale
    rendered_h = scale

    # Center horizontally & vertically in the workspace
    x0 = left + (avail_w - rendered_w) / 2
    y_top = top + (avail_h - rendered_h) / 2

    strokes = []
    cursor_x = x0
    for i, ch in enumerate(text):
        key = ch.upper()
        char_strokes = FONT.get(key)
        cw = CHAR_WIDTH.get(key, 0.7)

        if char_strokes is None:
            # Unknown char: advance cursor, skip drawing
            cursor_x += cw * scale
            if i < n - 1:
                cursor_x += letter_spacing * scale
            continue

        for stroke in char_strokes:
            mapped = []
            for px, py in stroke:
                # px, py are each 0..1 in the letter's design cell.
                # Horizontal axis is scaled by cw so the letter fits its
                # assigned width (no overlap into next letter).
                canvas_x = cursor_x + px * cw * scale
                canvas_y = y_top + (1.0 - py) * scale  # flip y (screen down)
                mapped.append((canvas_x, canvas_y))
            strokes.append(mapped)

        cursor_x += cw * scale
        if i < n - 1:
            cursor_x += letter_spacing * scale

    return strokes


# ---------------------------------------------------------------------------
# Canvas (display only — no mouse drawing)
# ---------------------------------------------------------------------------
class DrawingCanvas(QWidget):
    """Displays rendered strokes plus the ArUco corner markers.

    Strokes are stored as dicts: {'points': [QPointF, ...], 'color', 'width'}
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 600)

        self.strokes = []
        self.pen_color = QColor("#00ff88")
        self.pen_width = 2
        self.show_aruco_markers = True

    # --- painting ----------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor("#161616"))
        self._draw_grid(painter)
        if self.show_aruco_markers:
            self._draw_aruco_corners(painter)

        for stroke in self.strokes:
            self._draw_stroke(painter, stroke["points"], stroke["color"], stroke["width"])

        if not self.strokes:
            painter.setPen(QColor(90, 90, 90))
            font = QFont()
            font.setPointSize(11)
            painter.setFont(font)
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                "Type a name and click Render\nThe robot will write it inside the ArUco workspace",
            )

    @staticmethod
    def _draw_stroke(painter, points, color, width):
        pen = QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        path = QPainterPath()
        path.moveTo(points[0])
        for p in points[1:]:
            path.lineTo(p)
        painter.drawPath(path)

    def _draw_grid(self, painter):
        painter.setPen(QPen(QColor(40, 40, 40), 1, Qt.DotLine))
        step = 40
        for x in range(0, self.width(), step):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            painter.drawLine(0, y, self.width(), y)

    def _draw_aruco_corners(self, painter):
        margin = 24
        size = 36
        w, h = self.width(), self.height()
        corners = [
            (margin, margin, "ID:0"),
            (w - margin - size, margin, "ID:1"),
            (margin, h - margin - size, "ID:2"),
            (w - margin - size, h - margin - size, "ID:3"),
        ]
        font = QFont()
        font.setPointSize(7)
        painter.setFont(font)
        for x, y, label in corners:
            painter.setPen(QPen(QColor("#ff5555"), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(x, y, size, size)
            painter.setPen(QColor("#ff5555"))
            painter.drawText(x + 3, y + 12, label)

        painter.setPen(QPen(QColor(255, 85, 85, 80), 1, Qt.DashLine))
        painter.drawRect(
            margin + size // 2,
            margin + size // 2,
            w - 2 * margin - size,
            h - 2 * margin - size,
        )

    # --- public API --------------------------------------------------------
    def clear_canvas(self):
        self.strokes = []
        self.update()

    def set_strokes_normalized(self, normalized_strokes):
        """Replace canvas strokes with strokes given in 0..1 coords."""
        w = max(1, self.width())
        h = max(1, self.height())
        self.strokes = []
        for stroke in normalized_strokes:
            if len(stroke) < 2:
                continue
            pts = [QPointF(nx * w, ny * h) for nx, ny in stroke]
            self.strokes.append(
                {"points": pts, "color": QColor(self.pen_color), "width": self.pen_width}
            )
        self.update()

    def get_strokes_normalized(self):
        w = max(1, self.width())
        h = max(1, self.height())
        return [
            [(p.x() / w, p.y() / h) for p in stroke["points"]]
            for stroke in self.strokes
        ]


# ---------------------------------------------------------------------------
# Coordinate generation
# ---------------------------------------------------------------------------
class CoordsGenerator:
    """Convert normalized (0..1) strokes into a flat list of [x, y, z] mm points.

    The robot iterates through the list in order. Z encodes pen state:
        z = pen_up_z    -> pen raised (travel move)
        z = pen_down_z  -> pen lowered (drawing)

    For every stroke the generator emits:
        1. [x_start, y_start, pen_up_z]    # travel above start point
        2. [x_start, y_start, pen_down_z]  # lower pen
        3. [x_i, y_i, pen_down_z] ...      # draw through each point
        4. [x_end, y_end, pen_up_z]        # raise pen
    """

    def __init__(
        self,
        width_mm=200.0,
        height_mm=200.0,
        origin_x=0.0,
        origin_y=0.0,
        pen_up_z=5.0,
        pen_down_z=0.0,
        flip_y=True,
        min_point_distance_mm=0.5,
    ):
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.pen_up_z = pen_up_z
        self.pen_down_z = pen_down_z
        self.flip_y = flip_y
        self.min_point_distance_mm = max(0.0, float(min_point_distance_mm))

    def _norm_to_mm(self, nx, ny):
        x = self.origin_x + nx * self.width_mm
        y = self.origin_y + ((1.0 - ny) if self.flip_y else ny) * self.height_mm
        return x, y

    def _downsample(self, pts_mm):
        if self.min_point_distance_mm <= 0 or len(pts_mm) < 3:
            return pts_mm
        kept = [pts_mm[0]]
        for p in pts_mm[1:-1]:
            dx = p[0] - kept[-1][0]
            dy = p[1] - kept[-1][1]
            if (dx * dx + dy * dy) ** 0.5 >= self.min_point_distance_mm:
                kept.append(p)
        kept.append(pts_mm[-1])
        return kept

    def generate(self, normalized_strokes):
        """Return a list of [x, y, z] points in millimeters."""
        coords = []
        for stroke in normalized_strokes:
            if len(stroke) < 2:
                continue
            pts_mm = [self._norm_to_mm(nx, ny) for nx, ny in stroke]
            pts_mm = self._downsample(pts_mm)

            x0, y0 = pts_mm[0]
            coords.append([round(x0, 3), round(y0, 3), self.pen_up_z])     # travel
            coords.append([round(x0, 3), round(y0, 3), self.pen_down_z])   # pen down
            for x, y in pts_mm[1:]:
                coords.append([round(x, 3), round(y, 3), self.pen_down_z]) # draw
            xn, yn = pts_mm[-1]
            coords.append([round(xn, 3), round(yn, 3), self.pen_up_z])     # pen up
        return coords

    @staticmethod
    def format_python(coords):
        """Format as a Python list literal, one point per line."""
        lines = ["coords = ["]
        for x, y, z in coords:
            lines.append(f"    [{x:7.3f}, {y:7.3f}, {z:6.3f}],")
        lines.append("]")
        return "\n".join(lines)

    @staticmethod
    def format_csv(coords):
        lines = ["x_mm,y_mm,z_mm"]
        for x, y, z in coords:
            lines.append(f"{x:.3f},{y:.3f},{z:.3f}")
        return "\n".join(lines)

    @staticmethod
    def format_plain(coords):
        """Space-separated x y z, one point per line."""
        return "\n".join(f"{x:.3f} {y:.3f} {z:.3f}" for x, y, z in coords)


# ---------------------------------------------------------------------------
# Coordinates preview / export dialog
# ---------------------------------------------------------------------------
class CoordsDialog(QDialog):
    def __init__(self, strokes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Coordinates")
        self.resize(740, 620)
        self.strokes = strokes
        self.coords = []

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        settings_box = QGroupBox("Settings")
        grid = QGridLayout(settings_box)
        grid.setHorizontalSpacing(12)

        def make_dspin(val, rng, suffix, decimals=2):
            s = QDoubleSpinBox()
            s.setRange(*rng)
            s.setDecimals(decimals)
            s.setValue(val)
            s.setSuffix(f" {suffix}")
            return s

        self.width_spin = make_dspin(200.0, (10, 2000), "mm")
        self.height_spin = make_dspin(200.0, (10, 2000), "mm")
        self.origin_x_spin = make_dspin(0.0, (-1000, 1000), "mm")
        self.origin_y_spin = make_dspin(0.0, (-1000, 1000), "mm")
        self.pen_up_spin = make_dspin(5.0, (-50, 100), "mm")
        self.pen_down_spin = make_dspin(0.0, (-50, 100), "mm")
        self.min_pt_spin = make_dspin(0.5, (0, 10), "mm")
        self.flip_y_check = QCheckBox("Flip Y (screen → robot coordinates)")
        self.flip_y_check.setChecked(True)

        r = 0
        grid.addWidget(QLabel("Workspace width:"), r, 0); grid.addWidget(self.width_spin, r, 1)
        grid.addWidget(QLabel("Workspace height:"), r, 2); grid.addWidget(self.height_spin, r, 3)
        r += 1
        grid.addWidget(QLabel("Origin X:"), r, 0); grid.addWidget(self.origin_x_spin, r, 1)
        grid.addWidget(QLabel("Origin Y:"), r, 2); grid.addWidget(self.origin_y_spin, r, 3)
        r += 1
        grid.addWidget(QLabel("Pen up Z:"), r, 0); grid.addWidget(self.pen_up_spin, r, 1)
        grid.addWidget(QLabel("Pen down Z:"), r, 2); grid.addWidget(self.pen_down_spin, r, 3)
        r += 1
        grid.addWidget(QLabel("Min pt. spacing:"), r, 0); grid.addWidget(self.min_pt_spin, r, 1)
        grid.addWidget(self.flip_y_check, r, 2, 1, 2)

        layout.addWidget(settings_box)

        # Format selector + regenerate + info
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Python list", "CSV", "Plain (x y z)"])
        self.format_combo.currentIndexChanged.connect(self._refresh_preview)
        top_row.addWidget(self.format_combo)
        top_row.addSpacing(10)

        self.regen_btn = QPushButton("⟳  Regenerate")
        self.regen_btn.clicked.connect(self._regenerate)
        top_row.addWidget(self.regen_btn)

        self.info_label = QLabel("")
        top_row.addSpacing(10)
        top_row.addWidget(self.info_label)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        mono = QFont("Courier New")
        mono.setStyleHint(QFont.Monospace)
        mono.setPointSize(9)
        self.preview.setFont(mono)
        self.preview.setStyleSheet(
            "background-color: #121212; color: #cfe8cf; border: 1px solid #333;"
        )
        layout.addWidget(self.preview, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self._copy)
        self.save_btn = QPushButton("Save…")
        self.save_btn.setObjectName("primary")
        self.save_btn.clicked.connect(self._save)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self.setStyleSheet(parent.styleSheet() if parent else "")
        self._regenerate()

    def _build_generator(self):
        return CoordsGenerator(
            width_mm=self.width_spin.value(),
            height_mm=self.height_spin.value(),
            origin_x=self.origin_x_spin.value(),
            origin_y=self.origin_y_spin.value(),
            pen_up_z=self.pen_up_spin.value(),
            pen_down_z=self.pen_down_spin.value(),
            flip_y=self.flip_y_check.isChecked(),
            min_point_distance_mm=self.min_pt_spin.value(),
        )

    def _regenerate(self):
        gen = self._build_generator()
        self.coords = gen.generate(self.strokes)
        self._refresh_preview()
        raw_pts = sum(len(s) for s in self.strokes)
        self.info_label.setText(
            f"{len(self.strokes)} strokes · {raw_pts} raw pts → {len(self.coords)} output pts"
        )

    def _refresh_preview(self):
        fmt = self.format_combo.currentText()
        if fmt == "Python list":
            text = CoordsGenerator.format_python(self.coords)
        elif fmt == "CSV":
            text = CoordsGenerator.format_csv(self.coords)
        else:
            text = CoordsGenerator.format_plain(self.coords)
        self.preview.setPlainText(text)

    def _copy(self):
        QApplication.clipboard().setText(self.preview.toPlainText())

    def _save(self):
        fmt = self.format_combo.currentText()
        if fmt == "CSV":
            default_name = "coords.csv"
            filter_ = "CSV (*.csv);;All files (*)"
        elif fmt == "Python list":
            default_name = "coords.py"
            filter_ = "Python (*.py);;Text (*.txt);;All files (*)"
        else:
            default_name = "coords.txt"
            filter_ = "Text (*.txt);;All files (*)"

        path, _ = QFileDialog.getSaveFileName(self, "Save Coordinates", default_name, filter_)
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.preview.toPlainText())
        except OSError as e:
            self.info_label.setText(f"Save failed: {e}")
        else:
            self.info_label.setText(f"Saved: {path}")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
class StatusDot(QWidget):
    """Tiny colored circle used as a status indicator."""

    def __init__(self, color="#888", parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(12, 12)

    def set_color(self, color):
        self._color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(self._color)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(1, 1, 10, 10)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("6-DOF Robot Name-Writing Demo")
        self.resize(1250, 780)

        self._apply_dark_theme()
        self._build_ui()

    def _apply_dark_theme(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #222; color: #e0e0e0; }
            QGroupBox {
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                margin-top: 12px;
                padding: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: #00ff88;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 7px 12px;
                min-height: 20px;
            }
            QPushButton:hover { background-color: #484848; border-color: #00ff88; }
            QPushButton:pressed { background-color: #2c2c2c; }
            QPushButton#primary {
                background-color: #009959;
                border: 1px solid #00ff88;
                color: white;
                font-weight: bold;
            }
            QPushButton#primary:hover { background-color: #00b36b; }
            QPushButton#danger {
                background-color: #7a2f2f;
                border: 1px solid #994040;
            }
            QPushButton#danger:hover { background-color: #994040; }
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 6px 8px;
                color: #e0e0e0;
                selection-background-color: #00ff88;
                selection-color: #000;
            }
            QLineEdit:focus { border-color: #00ff88; }
            QComboBox {
                background-color: #3a3a3a; border: 1px solid #4a4a4a;
                border-radius: 4px; padding: 5px; min-height: 20px;
            }
            QStatusBar { background-color: #1a1a1a; }
            """
        )

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        left = QVBoxLayout()
        left.setSpacing(6)
        left.addLayout(self._build_toolbar())

        self.canvas = DrawingCanvas()
        left.addWidget(self.canvas, 1)
        root.addLayout(left, 2)

        root.addWidget(self._build_right_panel(), 1)

        sb = QStatusBar()
        sb.showMessage("Ready — type a name, click Render, then send to robot")
        self.setStatusBar(sb)

        # Re-render after the window shows (once the canvas has a real size)
        self._pending_text = ""

    def _build_toolbar(self):
        bar = QHBoxLayout()

        bar.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Type a name…")
        self.name_input.setMaxLength(20)
        self.name_input.returnPressed.connect(self._render_text)
        self.name_input.textChanged.connect(self._render_text)
        bar.addWidget(self.name_input, 1)

        self.btn_render = QPushButton("Render")
        self.btn_render.clicked.connect(self._render_text)
        bar.addWidget(self.btn_render)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setObjectName("danger")
        self.btn_clear.clicked.connect(self._clear)
        bar.addWidget(self.btn_clear)

        return bar

    def _build_right_panel(self):
        panel = QWidget()
        panel.setMaximumWidth(360)
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # ArUco
        aruco_group = QGroupBox("ArUco Workspace Lock")
        al = QVBoxLayout(aruco_group)

        row = QHBoxLayout()
        self.aruco_dot = StatusDot("#ff5555")
        row.addWidget(self.aruco_dot)
        self.aruco_label = QLabel("Not detected")
        row.addWidget(self.aruco_label)
        row.addStretch()
        al.addLayout(row)

        self.camera_preview = QLabel("Camera feed\n(OpenCV / ArUco detection goes here)")
        self.camera_preview.setAlignment(Qt.AlignCenter)
        self.camera_preview.setStyleSheet(
            "background-color: #121212; border: 1px dashed #444; color: #777;"
        )
        self.camera_preview.setMinimumHeight(170)
        al.addWidget(self.camera_preview)

        btn_detect = QPushButton("Detect Markers")
        btn_detect.clicked.connect(self._simulate_detection)
        al.addWidget(btn_detect)

        layout.addWidget(aruco_group)

        # Robot
        robot_group = QGroupBox("Robot Status")
        rl = QVBoxLayout(robot_group)

        r_row = QHBoxLayout()
        self.robot_dot = StatusDot("#ffaa00")
        r_row.addWidget(self.robot_dot)
        self.robot_label = QLabel("Disconnected")
        r_row.addWidget(self.robot_label)
        r_row.addStretch()
        rl.addLayout(r_row)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Simulation", "Real Robot", "Playback"])
        mode_row.addWidget(self.mode_combo, 1)
        rl.addLayout(mode_row)

        btn_connect = QPushButton("Connect")
        btn_connect.clicked.connect(self._simulate_connect)
        rl.addWidget(btn_connect)

        layout.addWidget(robot_group)

        # Execute
        exec_group = QGroupBox("Execute")
        el = QVBoxLayout(exec_group)

        self.info_label = QLabel("0 strokes  ·  0 points")
        el.addWidget(self.info_label)

        self.btn_gcode = QPushButton("Get Coordinates…")
        self.btn_gcode.clicked.connect(self._on_get_coords)

        self.btn_execute = QPushButton("Send to Robot")
        self.btn_execute.setObjectName("primary")
        self.btn_execute.clicked.connect(self._on_execute)

        el.addWidget(self.btn_gcode)
        el.addWidget(self.btn_execute)

        layout.addWidget(exec_group)
        layout.addStretch()
        return panel

    # --- handlers ----------------------------------------------------------
    def _render_text(self):
        text = self.name_input.text()
        strokes = text_to_strokes(text)
        self.canvas.set_strokes_normalized(strokes)
        self._refresh_stroke_info()

    def _clear(self):
        self.name_input.clear()
        self.canvas.clear_canvas()
        self._refresh_stroke_info()

    def _refresh_stroke_info(self):
        n = len(self.canvas.strokes)
        total = sum(len(s["points"]) for s in self.canvas.strokes)
        self.info_label.setText(f"{n} strokes  ·  {total} points")

    def resizeEvent(self, event):
        # Re-layout text when canvas size changes so it stays inside workspace
        super().resizeEvent(event)
        if hasattr(self, "name_input") and self.name_input.text():
            self._render_text()

    def _simulate_detection(self):
        self.aruco_dot.set_color("#00ff88")
        self.aruco_label.setText("4 markers locked")
        self.statusBar().showMessage("ArUco markers detected — workspace locked")

    def _simulate_connect(self):
        self.robot_dot.set_color("#00ff88")
        self.robot_label.setText(f"Connected ({self.mode_combo.currentText()})")
        self.statusBar().showMessage(f"Robot connected in {self.mode_combo.currentText()} mode")

    def _on_get_coords(self):
        strokes = self.canvas.get_strokes_normalized()
        if not strokes:
            self.statusBar().showMessage("Nothing to export — type a name first")
            return
        dlg = CoordsDialog(strokes, parent=self)
        dlg.exec_()

    def _on_execute(self):
        strokes = self.canvas.get_strokes_normalized()
        if not strokes:
            self.statusBar().showMessage("Nothing to send — type a name first")
            return

        gen = CoordsGenerator()
        coords = gen.generate(strokes)

        self.statusBar().showMessage(
            f"Sending '{self.name_input.text()}' — {len(coords)} XYZ points to robot…"
        )

        print(f"[execute] '{self.name_input.text()}' -> {len(coords)} XYZ points")
        print("[execute] first 10 points:")
        for i, pt in enumerate(coords[:10]):
            print(f"  [{i:3d}] x={pt[0]:7.3f}  y={pt[1]:7.3f}  z={pt[2]:6.3f}")
        if len(coords) > 10:
            print(f"  ... ({len(coords) - 10} more)")

        # Hook: hand `coords` to your robot controller. E.g.:
        #   for x, y, z in coords:
        #       self.robot.move_to(x, y, z)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.show()
    main.window = win
    app.exec_()
    return win


if __name__ == "__main__":
    main()