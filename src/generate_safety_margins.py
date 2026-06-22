"""
AL Drones - Safety Margins Generator
Generates safety layers from input KML for drone operations.
"""

import os
import argparse
from math import sqrt
import simplekml
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon


# KML styling configuration
STYLES = {
    'Flight Geography': {'fill': '3300ff00', 'outline': 'ff00ff00', 'width': 2},
    'Contingency Volume': {'fill': '1a00ffff', 'outline': 'ff00ffff', 'width': 2},
    'Ground Risk Buffer': {'fill': '1a0000ff', 'outline': 'ff0000ff', 'width': 2},
    'Adjacent Area': {'fill': '00ff0000', 'outline': 'ffff0000', 'width': 1},
}


def calculate_grb_size(height):
    """
    Calculate suggested Ground Risk Buffer size based on flight height.
    
    Arguments:
        height (float): Flight height in meters
        
    Returns:
        float: Suggested GRB size in meters
    """
    if height <= 120:
        height_cv = height + 15
        return height_cv
    else:
        height_cv = height + 15
        return 25 * sqrt(2 * height_cv / 9.81) + 1.485


def generate_safety_margins(
    input_kml_path,
    output_kml_path=None,
    fg_size=0,
    height=100,
    cv_size=215,
    grb_size=None,
    adj_size=5000,
    corner_style='square'
):
    """
    Generate safety margin layers from input KML.
    
    Args:
        input_kml_path (str): Path to input KML file
        output_kml_path (str): Path for output KML file (optional)
        fg_size (float): Flight Geography buffer size in meters (0 for polygons)
        height (float): Flight height in meters (used to suggest GRB if grb_size is None)
        cv_size (float): Contingency Volume buffer size in meters
        grb_size (float): Ground Risk Buffer size in meters (calculated from height if None)
        adj_size (float or None): Adjacent Area buffer from CV in meters; pass None to skip
        corner_style (str): 'square' or 'rounded' for buffer corners
        
    Returns:
        str: Path to generated KML file
    """
    
    # Read and reproject to metric CRS (SIRGAS 2000 / UTM zone 23S)
    gdf = gpd.read_file(input_kml_path).to_crs(epsg=31983)
    
    # If input is polygon, no Flight Geography buffer needed
    has_polygon = gdf.geometry.type.isin(['Polygon', 'MultiPolygon']).any()
    if has_polygon:
        fg_size = 0
    
    # Set join/cap style for corners
    join_style = 2 if corner_style == 'square' else 1
    cap_style = 3 if corner_style == 'square' else 1
    
    # Calculate GRB if not provided
    if grb_size is None:
        grb_size = calculate_grb_size(height)
    
    # Build buffer layers
    buffers = {
        'Flight Geography': fg_size,
        'Contingency Volume': cv_size + fg_size,
        'Ground Risk Buffer': grb_size + cv_size + fg_size,
    }
    
    layers = {}
    for name, buffer_size in buffers.items():
        layer = gdf.copy()
        if buffer_size > 0:
            layer["geometry"] = gdf.geometry.buffer(
                buffer_size,
                cap_style=cap_style,
                join_style=join_style
            )
        layers[name] = layer.to_crs(epsg=4326)
    
    # Adjacent Area — optional
    if adj_size is not None:
        adj_layer = layers['Contingency Volume'].copy()
        adj_layer["geometry"] = (
            layers['Contingency Volume']
            .to_crs(epsg=31983)
            .geometry.buffer(adj_size, join_style=1)
        )
        layers['Adjacent Area'] = adj_layer.to_crs(epsg=4326)
    
    # Create KML
    kml = simplekml.Kml()
    folder = kml.newfolder(name="Safety Margins")
    
    for name, layer in layers.items():
        for _, row in layer.iterrows():
            geom = row['geometry']
            polygons = (
                [geom] if isinstance(geom, Polygon)
                else (geom.geoms if isinstance(geom, MultiPolygon) else [])
            )
            
            for poly in polygons:
                if isinstance(poly, Polygon):
                    coords = list(zip(*poly.exterior.coords.xy))
                    pol = folder.newpolygon(name=name, outerboundaryis=coords)
                    pol.style.polystyle.color = STYLES[name]['fill']
                    pol.style.polystyle.fill = 1
                    pol.style.linestyle.color = STYLES[name]['outline']
                    pol.style.linestyle.width = STYLES[name]['width']
    
    # Determine output path
    if output_kml_path is None:
        base_name = os.path.splitext(input_kml_path)[0]
        output_kml_path = f"{base_name}_safety_margins.kml"
    
    kml.save(output_kml_path)
    
    print(f"✓ Safety margins KML generated: {output_kml_path}")
    print(f"  - Flight Geography: {fg_size}m buffer")
    print(f"  - Contingency Volume: {cv_size}m buffer")
    print(f"  - Ground Risk Buffer: {grb_size:.2f}m (height: {height}m)")
    if adj_size is not None:
        print(f"  - Adjacent Area: {adj_size}m buffer")
    else:
        print(f"  - Adjacent Area: skipped")
    
    return output_kml_path


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description='Generate drone safety margin layers from KML'
    )
    parser.add_argument('input_kml', help='Input KML file path')
    parser.add_argument('-o', '--output', help='Output KML file path (optional)', default=None)
    parser.add_argument('--fg-size', type=float, default=0,
                        help='Flight Geography buffer size in meters (default: 0)')
    parser.add_argument('--height', type=float, default=100,
                        help='Flight height in meters (default: 100)')
    parser.add_argument('--cv-size', type=float, default=215,
                        help='Contingency Volume buffer size in meters (default: 215)')
    parser.add_argument('--grb-size', type=float, default=None,
                        help='Ground Risk Buffer size in meters (calculated from height if not provided)')
    parser.add_argument('--adj-size', type=float, default=5000,
                        help='Adjacent Area buffer in meters (default: 5000; use 0 to skip)')
    parser.add_argument('--no-adjacent', action='store_true',
                        help='Skip Adjacent Area generation')
    parser.add_argument('--corner-style', choices=['square', 'rounded'], default='square',
                        help='Corner style for buffers (default: square)')
    
    args = parser.parse_args()
    
    adj_size = None if args.no_adjacent or args.adj_size == 0 else args.adj_size
    
    generate_safety_margins(
        input_kml_path=args.input_kml,
        output_kml_path=args.output,
        fg_size=args.fg_size,
        height=args.height,
        cv_size=args.cv_size,
        grb_size=args.grb_size,
        adj_size=adj_size,
        corner_style=args.corner_style
    )


if __name__ == '__main__':
    main()
