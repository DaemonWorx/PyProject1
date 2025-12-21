#!/usr/bin/env python3
"""
Parametric grid STL generator (no external libraries needed).

Generates a tray that:
- Fills a specified outer width/length.
- Has a solid base.
- Has outer walls + internal grid walls, all with configurable thickness.
- Exports as ASCII STL.

UNITS: millimeters (mm)
Example: 21.5cm x 11.5cm -> 215mm x 115mm
"""

import argparse
import sys
from typing import List, Tuple

Vec3 = Tuple[float, float, float]
Triangle = Tuple[Vec3, Vec3, Vec3, Vec3]  # (normal, v1, v2, v3)


def add_box(triangles: List[Triangle],
            x0: float, y0: float, z0: float,
            x1: float, y1: float, z1: float) -> None:
    """
    Add a rectangular box (axis-aligned) defined by two opposite corners.
    The box is closed (6 faces, 12 triangles).
    """
    # Ensure proper ordering
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    if z1 < z0:
        z0, z1 = z1, z0

    # Corners
    # Bottom rectangle (z=z0)
    p000 = (x0, y0, z0)
    p100 = (x1, y0, z0)
    p110 = (x1, y1, z0)
    p010 = (x0, y1, z0)
    # Top rectangle (z=z1)
    p001 = (x0, y0, z1)
    p101 = (x1, y0, z1)
    p111 = (x1, y1, z1)
    p011 = (x0, y1, z1)

    # Helper to add a face as two triangles
    def face(normal: Vec3, a: Vec3, b: Vec3, c: Vec3, d: Vec3):
        # Tri 1: a, b, c
        triangles.append((normal, a, b, c))
        # Tri 2: a, c, d
        triangles.append((normal, a, c, d))

    # Bottom face (z = z0), normal pointing -Z
    face((0.0, 0.0, -1.0), p000, p100, p110, p010)
    # Top face (z = z1), normal pointing +Z
    face((0.0, 0.0, 1.0), p001, p011, p111, p101)

    # -X face
    face((-1.0, 0.0, 0.0), p000, p010, p011, p001)
    # +X face
    face((1.0, 0.0, 0.0), p100, p101, p111, p110)

    # -Y face
    face((0.0, -1.0, 0.0), p000, p001, p101, p100)
    # +Y face
    face((0.0, 1.0, 0.0), p010, p110, p111, p011)


def write_ascii_stl(filename: str, solid_name: str, triangles: List[Triangle]) -> None:
    """Write triangles to an ASCII STL file."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"solid {solid_name}\n")
        for normal, v1, v2, v3 in triangles:
            nx, ny, nz = normal
            f.write(f"  facet normal {nx:.6g} {ny:.6g} {nz:.6g}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {v1[0]:.6g} {v1[1]:.6g} {v1[2]:.6g}\n")
            f.write(f"      vertex {v2[0]:.6g} {v2[1]:.6g} {v2[2]:.6g}\n")
            f.write(f"      vertex {v3[0]:.6g} {v3[1]:.6g} {v3[2]:.6g}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write(f"endsolid {solid_name}\n")


def generate_grid(
    outer_width: float,
    outer_length: float,
    base_thickness: float,
    wall_thickness: float,
    wall_height: float,
    cols: int,
    rows: int,
    filename: str = "grid.stl",
) -> None:
    """
    Generate a tray with grid walls.

    Coordinate system:
      - X: width direction [0, outer_width]
      - Y: length direction [0, outer_length]
      - Z: up, base at 0
    """
    if cols < 1 or rows < 1:
        raise ValueError("cols and rows must be >= 1")

    if wall_thickness <= 0 or base_thickness <= 0 or wall_height <= 0:
        raise ValueError("Thicknesses and heights must be > 0")

    # Available inner area inside the outer walls
    inner_width = outer_width - 2.0 * wall_thickness
    inner_length = outer_length - 2.0 * wall_thickness

    if inner_width <= 0 or inner_length <= 0:
        raise ValueError("Outer size is too small for the chosen wall thickness.")

    # Space taken up by internal grid walls
    total_internal_walls_x = (cols - 1) * wall_thickness
    total_internal_walls_y = (rows - 1) * wall_thickness

    # Compute cell sizes (uniform cells)
    cell_width = (inner_width - total_internal_walls_x) / cols
    cell_length = (inner_length - total_internal_walls_y) / rows

    if cell_width <= 0 or cell_length <= 0:
        raise ValueError(
            "Outer size too small for the chosen wall thickness and grid count."
        )

    triangles: List[Triangle] = []
    total_height = base_thickness + wall_height

    # 1) Base slab (solid)
    add_box(triangles, 0.0, 0.0, 0.0, outer_width, outer_length, base_thickness)

    # 2) Outer walls
    # Left wall
    add_box(triangles,
            0.0, 0.0, base_thickness,
            wall_thickness, outer_length, total_height)
    # Right wall
    add_box(triangles,
            outer_width - wall_thickness, 0.0, base_thickness,
            outer_width, outer_length, total_height)
    # Front wall (Y = 0 edge)
    add_box(triangles,
            wall_thickness, 0.0, base_thickness,
            outer_width - wall_thickness, wall_thickness, total_height)
    # Back wall (Y = outer_length edge)
    add_box(triangles,
            wall_thickness, outer_length - wall_thickness, base_thickness,
            outer_width - wall_thickness, outer_length, total_height)

    # 3) Internal grid walls
    # Vertical walls (parallel to Y, between columns)
    x = wall_thickness
    for col in range(cols):
        x_start_cell = x
        x_end_cell = x_start_cell + cell_width
        x = x_end_cell
        if col < cols - 1:
            x_wall_start = x
            x_wall_end = x_wall_start + wall_thickness
            add_box(
                triangles,
                x_wall_start,
                wall_thickness,
                base_thickness,
                x_wall_end,
                outer_length - wall_thickness,
                total_height,
            )
            x = x_wall_end

    # Horizontal walls (parallel to X, between rows)
    y = wall_thickness
    for row in range(rows):
        y_start_cell = y
        y_end_cell = y_start_cell + cell_length
        y = y_end_cell
        if row < rows - 1:
            y_wall_start = y
            y_wall_end = y_wall_start + wall_thickness
            add_box(
                triangles,
                wall_thickness,
                y_wall_start,
                base_thickness,
                outer_width - wall_thickness,
                y_wall_end,
                total_height,
            )
            y = y_wall_end

    solid_name = f"grid_{cols}x{rows}"
    write_ascii_stl(filename, solid_name, triangles)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a parametric grid tray as an ASCII STL."
    )
    parser.add_argument(
        "--outer-width",
        type=float,
        default=215.0,  # 21.5 cm
        help="Outer width in mm (default: 215.0 = 21.5cm)",
    )
    parser.add_argument(
        "--outer-length",
        type=float,
        default=115.0,  # 11.5 cm
        help="Outer length in mm (default: 115.0 = 11.5cm)",
    )
    parser.add_argument(
        "--base-thickness",
        type=float,
        default=2.0,
        help="Base thickness in mm (default: 2.0)",
    )
    parser.add_argument(
        "--wall-thickness",
        type=float,
        default=2.0,
        help="Wall thickness in mm (default: 2.0)",
    )
    parser.add_argument(
        "--wall-height",
        type=float,
        default=20.0,
        help="Wall height above base in mm (default: 20.0)",
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=5,
        help="Number of grid columns (default: 5)",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=3,
        help="Number of grid rows (default: 3)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="grid.stl",
        help="Output STL filename (default: grid.stl)",
    )
    return parser.parse_args()


# ---- Interactive helpers ----

def prompt_float(label: str, default: float) -> float:
    while True:
        s = input(f"{label} [{default}]: ").strip()
        if not s:
            return default
        try:
            return float(s)
        except ValueError:
            print("Invalid number, please try again.")


def prompt_int(label: str, default: int) -> int:
    while True:
        s = input(f"{label} [{default}]: ").strip()
        if not s:
            return default
        try:
            return int(s)
        except ValueError:
            print("Invalid integer, please try again.")


def main():
    if len(sys.argv) == 1:
        # No arguments -> interactive mode
        print("Interactive grid STL generator")
        print("Press Enter to accept the value in [brackets].\n")

        outer_width = prompt_float("Outer width in mm", 215.0)
        outer_length = prompt_float("Outer length in mm", 115.0)
        base_thickness = prompt_float("Base thickness in mm", 2.0)
        wall_thickness = prompt_float("Wall thickness in mm", 2.0)
        wall_height = prompt_float("Wall height in mm", 20.0)
        cols = prompt_int("Number of columns", 5)
        rows = prompt_int("Number of rows", 3)

        output = input("Output STL filename [grid.stl]: ").strip() or "grid.stl"

        generate_grid(
            outer_width=outer_width,
            outer_length=outer_length,
            base_thickness=base_thickness,
            wall_thickness=wall_thickness,
            wall_height=wall_height,
            cols=cols,
            rows=rows,
            filename=output,
        )
        print(f"\nDone. Wrote STL to: {output}")
    else:
        # Arguments provided -> normal argparse mode
        args = parse_args()
        generate_grid(
            outer_width=args.outer_width,
            outer_length=args.outer_length,
            base_thickness=args.base_thickness,
            wall_thickness=args.wall_thickness,
            wall_height=args.wall_height,
            cols=args.cols,
            rows=args.rows,
            filename=args.output,
        )
        print(f"Done. Wrote STL to: {args.output}")


if __name__ == "__main__":
    main()
