"""
AL Drones - Population Analysis Tool
Analyzes population density in drone flight areas using IBGE data.
Uses the unified 1km grid (BR1KM_20251002) from IBGE Census 2022.

Performance notes
-----------------
- The ZIP is downloaded once and extracted to BR1KM_DIR on disk.
- Subsequent runs skip the download entirely (_encontrar_shp detects the .shp).
- gpd.read_file(..., bbox=...) lets GDAL spatial-filter at read time, so only
  cells inside the bounding box of the analysis area are loaded into memory.
  No need to cache the full Brazil grid or build an in-memory R-tree index.
"""

import os
import argparse
import requests
import zipfile
import io
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.colors import LinearSegmentedColormap


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COLORS = {
    'Flight Geography': '#00AA00',
    'Contingency Volume': '#FF8C00',
    'Ground Risk Buffer': '#DC143C',
    'Adjacent Area': '#1E90FF',
}

NAMES_PT = {
    'Flight Geography': 'Geografia de Voo',
    'Contingency Volume': 'Volume de Contingência',
    'Ground Risk Buffer': 'Buffer de Risco no Solo',
    'Adjacent Area': 'Área Adjacente',
}

DEFAULT_BUFFER_INFO = {
    'Flight Geography': {'buffer': 0, 'height': None},
    'Contingency Volume': {'buffer': 215, 'height': None},
    'Ground Risk Buffer': {'buffer': 295, 'height': None},
    'Adjacent Area': {'buffer': 5000, 'height': None},
}

ALBERS_BR = (
    "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 "
    "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)

BR1KM_URL = (
    "https://geoftp.ibge.gov.br/recortes_para_fins_estatisticos/"
    "grade_estatistica/censo_2022/grade_1km/BR1KM_20251002.zip"
)
BR1KM_DIR = "dados_ibge/grade_1km"


# ---------------------------------------------------------------------------
# Grid helpers
# ---------------------------------------------------------------------------

def _encontrar_shp(pasta: str) -> str | None:
    """Return the first .shp file found inside *pasta*, or None."""
    if not os.path.isdir(pasta):
        return None
    for fname in os.listdir(pasta):
        if fname.lower().endswith('.shp'):
            return os.path.join(pasta, fname)
    return None


def garantir_grid_disponivel() -> str | None:
    """
    Ensure the BR1KM shapefile is present on disk, downloading and extracting
    the ZIP if necessary.  Returns the path to the .shp file, or None on error.

    No data is loaded into memory here — callers use gpd.read_file(..., bbox=)
    to load only the slice they need.
    """
    shp_path = _encontrar_shp(BR1KM_DIR)
    if shp_path is not None:
        return shp_path  # already on disk, nothing to do

    os.makedirs(BR1KM_DIR, exist_ok=True)
    print("⬇ Downloading BR1KM grid (one-time operation, ~large file)...")
    try:
        resp = requests.get(BR1KM_URL, timeout=300, stream=True)
        resp.raise_for_status()
        raw = b"".join(resp.iter_content(chunk_size=1 << 20))
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            z.extractall(BR1KM_DIR)
        print("✓ BR1KM grid downloaded and extracted.")
    except Exception as exc:
        print(f"✗ Error downloading BR1KM grid: {exc}")
        return None

    shp_path = _encontrar_shp(BR1KM_DIR)
    if shp_path is None:
        print("✗ No .shp file found after extraction — check the ZIP contents.")
    return shp_path


def carregar_celulas_area(shp_path: str, area_geom) -> gpd.GeoDataFrame | None:
    """
    Read only the grid cells that fall within the bounding box of *area_geom*
    using GDAL's native spatial filter (bbox parameter).  Fast even for the
    full-Brazil shapefile because GDAL uses the .shx/.qix spatial index.

    Returns a GeoDataFrame in EPSG:4326, or None if no cells are found.
    """
    minx, miny, maxx, maxy = area_geom.bounds
    dados = gpd.read_file(shp_path, bbox=(minx, miny, maxx, maxy))

    if dados.crs is None:
        dados = dados.set_crs(epsg=4326)
    else:
        dados = dados.to_crs(epsg=4326)

    if dados.empty:
        return None
    return dados


# ---------------------------------------------------------------------------
# KML helpers
# ---------------------------------------------------------------------------

def extrair_layers_kml(kml_filename: str, layer_names: list) -> dict:
    """Extract and union geometries from KML layers."""
    gdf = gpd.read_file(kml_filename, driver='KML')
    layers_poligonos = {}

    for name in layer_names:
        sel = gdf[gdf['Name'] == name]
        if sel.empty:
            print(f"⚠ Layer '{name}' not found in KML.")
            continue

        sel = sel[sel.geometry.type.isin(['Polygon', 'MultiPolygon'])]
        if sel.empty:
            print(f"⚠ Layer '{name}' has no polygons.")
            continue

        layers_poligonos[name] = sel.geometry.union_all()
        print(f"✓ Layer '{name}' extracted.")

    return layers_poligonos


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def desenhar_contornos(ax, layers_poligonos: dict, layer_order: list):
    """Draw layer boundaries with consistent styling."""
    for name in layer_order:
        if name in layers_poligonos:
            gpd.GeoSeries([layers_poligonos[name]]).boundary.plot(
                ax=ax, color=COLORS[name], linewidth=2.5, linestyle='-', zorder=10
            )


def criar_legenda_areas(layers_poligonos: dict, layers_para_mostrar: list,
                        buffer_info: dict = None) -> list:
    """Create legend elements with buffer/height info in Portuguese."""
    if buffer_info is None:
        buffer_info = DEFAULT_BUFFER_INFO

    legend_elements = []
    for name in layers_para_mostrar:
        if name in layers_poligonos:
            name_pt = NAMES_PT.get(name, name)
            info = buffer_info.get(name, {})
            buffer_m = info.get('buffer', 0)
            height_m = info.get('height')

            if buffer_m == 0 and height_m:
                label = f"{name_pt}\n(Altura: {height_m}m)"
            elif buffer_m > 0 and height_m:
                label = f"{name_pt}\n(Buffer: {buffer_m}m, Altura: {height_m}m)"
            elif buffer_m > 0:
                label = f"{name_pt}\n(Buffer: {buffer_m}m)"
            else:
                label = name_pt

            legend_elements.append(
                Patch(facecolor='none', edgecolor=COLORS[name],
                      linewidth=2.5, label=label)
            )

    return legend_elements


def criar_colormap_melhorado():
    """White -> yellow -> red colormap for population density."""
    colors = [
        '#FFFFFF', '#FFF9E6', '#FFF3CC', '#FFECB3', '#FFE599',
        '#FFDB80', '#FFD166', '#FFC14D', '#FFB133', '#FFA31A',
        '#FF9500', '#FF8700', '#FF7A00', '#FF6D00', '#FF5500',
        '#FF3D00', '#FF2500', '#FF0D00', '#E60000', '#CC0000',
    ]
    return LinearSegmentedColormap.from_list('population', colors, N=100)


def determinar_zoom_adequado(area_km2: float) -> int:
    """Return an appropriate basemap zoom level for the given area."""
    if area_km2 < 1:
        return 16
    elif area_km2 < 5:
        return 15
    elif area_km2 < 20:
        return 14
    elif area_km2 < 100:
        return 13
    elif area_km2 < 500:
        return 12
    return 11


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def calcular_area_km2(geom) -> float:
    """Return area in km² for a WGS84 geometry."""
    proj = gpd.GeoSeries([geom], crs='EPSG:4326').to_crs(ALBERS_BR)
    return float(proj.area.iloc[0] / 1e6)


def calcular_estatisticas(dados_proj: gpd.GeoDataFrame, area_geom=None) -> tuple:
    """
    Compute summary statistics from a projected (Albers) GeoDataFrame.

    Uses TOTAL_POND (area-weighted population) when present; falls back to
    raw TOTAL otherwise.

    Returns:
        (total_pessoas, area_km2, densidade_media, densidade_maxima)
    """
    if dados_proj.empty:
        return 0, 0.0, 0.0, 0.0

    pop_col = 'TOTAL_POND' if 'TOTAL_POND' in dados_proj.columns else 'TOTAL'
    total_pessoas = float(dados_proj[pop_col].sum())

    if area_geom is not None:
        proj = gpd.GeoSeries([area_geom], crs='EPSG:4326').to_crs(ALBERS_BR)
        area_km2 = float(proj.area.iloc[0] / 1e6)
    else:
        area_km2 = float(dados_proj.geometry.area.sum() / 1e6)

    densidade_media = (total_pessoas / area_km2) if area_km2 > 0 else 0.0
    densidade_maxima = (
        float(dados_proj['densidade_pop_km2'].max())
        if 'densidade_pop_km2' in dados_proj.columns else 0.0
    )

    return total_pessoas, area_km2, densidade_media, densidade_maxima


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

def processar_grid(area_geom, titulo: str, layers_poligonos: dict,
                   layers_para_mostrar: list, shp_path: str,
                   buffer_info: dict = None,
                   output_path: str = None) -> dict | None:
    """
    Load grid cells for *area_geom* from *shp_path* using a bbox spatial
    filter, apply weighted intersection, compute density, and render a map.

    Weighted intersection
    ---------------------
        frac_area  = clipped_cell_area / original_cell_area
        TOTAL_POND = TOTAL * frac_area

    Parameters
    ----------
    area_geom           : shapely geometry (WGS84)
    titulo              : map title
    layers_poligonos    : dict of layer geometries for boundary drawing
    layers_para_mostrar : ordered list of layer names to draw
    shp_path            : path to the BR1KM .shp file on disk
    buffer_info         : display metadata per layer
    output_path         : if given, save the PNG to this path

    Returns
    -------
    dict with total_pessoas, area_km2, densidade_media, densidade_maxima
    or None on failure.
    """
    print(f"\n{'='*60}")
    print(f"Processing: {titulo}")
    print(f"{'='*60}")

    # --- Step 1: bbox-filtered read (GDAL spatial filter, very fast) ---
    possible_matches = carregar_celulas_area(shp_path, area_geom)
    if possible_matches is None:
        print("⚠ No grid cells found in bounding box.")
        return None

    print(f"✓ {len(possible_matches):,} cells in bounding box")

    # --- Step 2: Weighted intersection ---
    area_gdf = gpd.GeoDataFrame(geometry=[area_geom], crs=possible_matches.crs)
    intersec = gpd.overlay(possible_matches, area_gdf, how='intersection')

    if intersec.empty:
        print("⚠ No grid cells intersect the analysis area.")
        return None

    # Original cell areas in Albers BR (stable m²)
    orig_proj = possible_matches.to_crs(ALBERS_BR)
    orig_proj.index = possible_matches.index
    orig_areas = orig_proj.geometry.area  # indexed by possible_matches.index

    intersec_proj = intersec.to_crs(ALBERS_BR)
    intersec_proj['area_intersec'] = intersec_proj.geometry.area

    # gpd.overlay resets index — map original areas positionally
    intersec_proj['area_original'] = orig_areas.reindex(
        possible_matches.index
    ).values[:len(intersec_proj)]

    intersec_proj['frac_area'] = (
        intersec_proj['area_intersec'] / intersec_proj['area_original']
    ).clip(0, 1)

    intersec_proj['TOTAL_POND'] = intersec_proj['TOTAL'] * intersec_proj['frac_area']
    intersec_proj['area_km2'] = intersec_proj['area_intersec'] / 1e6
    intersec_proj['densidade_pop_km2'] = (
        intersec_proj['TOTAL_POND'] / intersec_proj['area_km2']
    )

    dados = intersec.copy()
    dados['densidade_pop_km2'] = intersec_proj['densidade_pop_km2'].values
    dados['TOTAL_POND'] = intersec_proj['TOTAL_POND'].values

    print(f"✓ {len(dados):,} clipped cells (weighted intersection)")

    # --- Figure ---
    area_analise_km2 = calcular_area_km2(area_geom)
    fig_size = min(30, max(20, area_analise_km2 * 0.5))

    fig, ax = plt.subplots(figsize=(fig_size, fig_size), dpi=150)

    dados.plot(
        column='densidade_pop_km2',
        ax=ax,
        legend=True,
        cmap=criar_colormap_melhorado(),
        alpha=0.7,
        edgecolor='gray',
        linewidth=0.15,
        legend_kwds={
            'shrink': 0.5,
            'label': 'Densidade Populacional (hab/km²)',
            'orientation': 'vertical',
            'pad': 0.02,
        },
        vmin=0,
    )

    desenhar_contornos(ax, layers_poligonos, layers_para_mostrar)

    legend_elements = criar_legenda_areas(layers_poligonos, layers_para_mostrar, buffer_info)
    if legend_elements:
        ax.legend(
            handles=legend_elements,
            loc='upper left',
            fontsize=14,
            framealpha=0.95,
            edgecolor='black',
            title='Áreas Analisadas',
            title_fontsize=15,
        )

    ax.set_title(titulo, fontsize=24, fontweight='bold', pad=20)
    ax.set_xlabel("Longitude [°]", fontsize=16, fontweight='bold')
    ax.set_ylabel("Latitude [°]", fontsize=16, fontweight='bold')

    zoom_level = determinar_zoom_adequado(area_analise_km2)
    try:
        cx.add_basemap(
            ax,
            crs=dados.crs.to_string(),
            source=cx.providers.OpenStreetMap.Mapnik,
            alpha=0.5,
            zoom=zoom_level + 1,
        )
    except Exception as exc:
        print(f"⚠ Could not add basemap: {exc}")

    total_pessoas, area_km2, densidade_media, densidade_maxima = calcular_estatisticas(
        intersec_proj, area_geom
    )

    info_texto = (
        f"ESTATÍSTICAS\n"
        f"População Total: {int(total_pessoas):,} habitantes\n"
        f"Área do Polígono: {area_km2:.2f} km²\n"
        f"Densidade Média: {densidade_media:.2f} hab/km²\n"
        f"Densidade Máxima: {densidade_maxima:.2f} hab/km²"
    ).replace(",", ".")

    ax.text(
        0.02, 0.02,
        info_texto,
        transform=ax.transAxes,
        fontsize=13,
        verticalalignment='bottom',
        bbox=dict(facecolor='white', alpha=0.95, edgecolor='black', boxstyle='round,pad=0.8'),
        family='Segoe UI',
    )

    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.tick_params(labelsize=12)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✓ Map saved: {output_path}")

    plt.close()

    return {
        'total_pessoas': total_pessoas,
        'area_km2': area_km2,
        'densidade_media': densidade_media,
        'densidade_maxima': densidade_maxima,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_population(kml_file: str, output_dir: str = 'results',
                       buffer_info: dict = None, height: float = None,
                       include_adjacent: bool = True) -> dict | None:
    """
    Analyze population density from a safety-margins KML file.

    Parameters
    ----------
    kml_file        : path to KML with layer names matching NAMES_PT keys
    output_dir      : directory where PNG maps are saved
    buffer_info     : optional dict with keys fg_size, cv_size, grb_size, adj_size
    height          : optional flight height in metres (displayed in legend)
    include_adjacent: whether to generate the Adjacent Area map

    Returns
    -------
    dict keyed by layer name, each value a statistics dict, or None on error.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Ensure the shapefile is on disk (downloads once if needed)
    shp_path = garantir_grid_disponivel()
    if shp_path is None:
        return None

    if buffer_info is None:
        buffer_info_display = DEFAULT_BUFFER_INFO
    else:
        buffer_info_display = {
            'Flight Geography': {'buffer': buffer_info.get('fg_size', 0), 'height': height},
            'Contingency Volume': {'buffer': buffer_info.get('cv_size', 215), 'height': None},
            'Ground Risk Buffer': {'buffer': buffer_info.get('grb_size', 0), 'height': None},
            'Adjacent Area': {'buffer': buffer_info.get('adj_size', 5000), 'height': None},
        }

    layers_kml = ['Flight Geography', 'Contingency Volume', 'Ground Risk Buffer']
    if include_adjacent:
        layers_kml.append('Adjacent Area')

    print("=" * 60)
    print("AL DRONES - Population Analysis Tool")
    print("=" * 60)

    layers_poligonos = extrair_layers_kml(kml_file, layers_kml)
    if not layers_poligonos:
        print("✗ No valid layers found in KML")
        return None

    # Shared kwargs to avoid repetition
    grid_kwargs = dict(
        layers_poligonos=layers_poligonos,
        shp_path=shp_path,
        buffer_info=buffer_info_display,
    )

    results = {}

    # Map 1 — Flight Geography
    if 'Flight Geography' in layers_poligonos:
        stats = processar_grid(
            area_geom=layers_poligonos['Flight Geography'],
            titulo="Densidade Populacional - Geografia de Voo",
            layers_para_mostrar=['Flight Geography'],
            output_path=os.path.join(output_dir, 'map_flight_geography.png'),
            **grid_kwargs,
        )
        if stats:
            results['Flight Geography'] = stats

    # Map 2 — Ground Risk Buffer (shows FG + CV + GRB)
    if 'Ground Risk Buffer' in layers_poligonos:
        stats = processar_grid(
            area_geom=layers_poligonos['Ground Risk Buffer'],
            titulo="Densidade Populacional - Distância de Segurança no Solo",
            layers_para_mostrar=[
                l for l in ['Flight Geography', 'Contingency Volume', 'Ground Risk Buffer']
                if l in layers_poligonos
            ],
            output_path=os.path.join(output_dir, 'map_ground_risk_buffer.png'),
            **grid_kwargs,
        )
        if stats:
            results['Ground Risk Buffer'] = stats

    # Map 3 — Adjacent Area ring
    if include_adjacent:
        if 'Adjacent Area' in layers_poligonos and 'Ground Risk Buffer' in layers_poligonos:
            area_anel = layers_poligonos['Adjacent Area'].difference(
                layers_poligonos['Ground Risk Buffer']
            )
            stats = processar_grid(
                area_geom=area_anel,
                titulo="Densidade Populacional - Área Adjacente",
                layers_para_mostrar=[
                    l for l in ['Flight Geography', 'Contingency Volume',
                                 'Ground Risk Buffer', 'Adjacent Area']
                    if l in layers_poligonos
                ],
                output_path=os.path.join(output_dir, 'map_adjacent_area.png'),
                **grid_kwargs,
            )
            if stats:
                results['Adjacent Area'] = stats
        else:
            print("⚠ Cannot generate Adjacent Area map: missing required layers.")

    print("\n" + "=" * 60)
    print("✓ Analysis complete!")
    print("=" * 60)

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Analyze population density in drone flight areas (BR1KM grid)'
    )
    parser.add_argument('kml_file', help='KML file with safety margins')
    parser.add_argument('-o', '--output-dir', default='results',
                        help='Output directory for maps (default: results/)')
    parser.add_argument('--height', type=float,
                        help='Flight height in metres (optional, shown in legend)')
    parser.add_argument('--no-adjacent', action='store_true',
                        help='Skip Adjacent Area analysis')
    parser.add_argument('--fg-size', type=float, default=0,
                        help='Flight Geography buffer in metres (default: 0)')
    parser.add_argument('--cv-size', type=float, default=215,
                        help='Contingency Volume buffer in metres (default: 215)')
    parser.add_argument('--grb-size', type=float, default=295,
                        help='Ground Risk Buffer size in metres (default: 295)')
    parser.add_argument('--adj-size', type=float, default=5000,
                        help='Adjacent Area buffer in metres (default: 5000)')

    args = parser.parse_args()

    analyze_population(
        kml_file=args.kml_file,
        output_dir=args.output_dir,
        buffer_info={
            'fg_size': args.fg_size,
            'cv_size': args.cv_size,
            'grb_size': args.grb_size,
            'adj_size': args.adj_size,
        },
        height=args.height,
        include_adjacent=not args.no_adjacent,
    )


if __name__ == '__main__':
    main()
