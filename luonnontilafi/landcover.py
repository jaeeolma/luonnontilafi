# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/00_landcover_pct.ipynb (unless otherwise specified).

__all__ = ['conserved_areas_for_year_natura', 'conserved_areas_for_year_cdda']

# Cell

import geopandas as gpd
import rasterio as rio
import rasterio.mask as rio_mask
import os
import pandas as pd
from pathlib import Path
from shapely.geometry import box, Polygon
import numpy as np
import matplotlib.pyplot as plt

# Cell

def conserved_areas_for_year_natura(path_to_raster, path_to_corine, path_to_natura) -> pd.DataFrame:
    """Derive the total area for each CLC class and classwise total areas for Natura data (all polygons in
    `path_to_natura` data). Returns the original `path_to_corine` dataframe with additional columns
    `tot_area_km2` (the full area covered by that class) and `tot_cons_area_km2`."""

    clc_classes = pd.read_excel(path_to_corine) # Corines are xls files, todo fix for csv
    clc_classes.dropna(subset='Value', inplace=True)
    conservation = gpd.read_file(path_to_natura)

    with rio.open(path_to_raster) as src:
        im = src.read()[0]
        res = src.profile['transform'][0]
    uniq, counts = np.unique(im, return_counts=True)
    uniq_dict = {u: c for u, c in zip(uniq, counts)}
    uniq_dict.pop(255, None) # We don't need nodata

    outdf = clc_classes.copy()

    # Area of a single pixel is res**2 m²
    outdf['tot_area_km2'] = outdf.Value.apply(lambda row: uniq_dict[row]*res**2 / 10**6
                                              if row in uniq_dict.keys() else 0)

    with rio.open(path_to_raster) as src:
        im, tfm = rio_mask.mask(src, conservation.geometry, crop=True)

    uniq, counts = np.unique(im, return_counts=True)
    uniq_dict = {u: c for u, c in zip(uniq, counts)}
    uniq_dict.pop(255, None) # We don't need nodata
    outdf['tot_cons_area_km2'] = outdf.Value.apply(lambda row: uniq_dict[row]*res**2 / 10**6
                                                   if row in uniq_dict.keys() else 0)
    return outdf

# Cell

def conserved_areas_for_year_cdda(path_to_raster, path_to_corine, path_to_cdda, year:int) -> pd.DataFrame:
    """Derive the total area for each CLC class and total areas for each IUCN category present in the
    `path_to_cdda` data. Returns the original `path_to_corine` dataframe with additional columns
    `tot_area_km2` (the full area covered by that class) and `cons_area_km2_<iucn_cat>` for each
    IUCN category present. `year` is used to mask only with the areas founded before or during that year.
    """
    clc_classes = pd.read_excel(path_to_corine) # Corines are xls files, todo fix for csv maybe
    clc_classes.dropna(subset='Value', inplace=True)
    conservation = gpd.read_file(path_to_cdda)
    conservation = conservation[conservation.legalFoundationDate <= year]

    with rio.open(path_to_raster) as src:
        im = src.read()[0]
        res = src.profile['transform'][0] # square pixels, this is size in meters
    uniq, counts = np.unique(im, return_counts=True)
    uniq_dict = {u: c for u, c in zip(uniq, counts)}
    uniq_dict.pop(255, None) # We don't need nodata

    outdf = clc_classes.copy()

    # Area of a single pixel is res**2 m²
    outdf['tot_area_km2'] = outdf.Value.apply(lambda row: uniq_dict[row]*res**2 / 10**6
                                              if row in uniq_dict.keys() else 0)

    for iucn_cat in cdda.iucnCategory.unique():
        tempgeom = conservation[conservation.iucnCategory == iucn_cat].copy()
        with rio.open(path_to_raster) as src:
            im, tfm = rio_mask.mask(src, tempgeom.geometry, crop=True)

        uniq, counts = np.unique(im, return_counts=True)
        uniq_dict = {u: c for u, c in zip(uniq, counts)}
        uniq_dict.pop(255, None) # We don't need nodata
        outdf[f'cons_area_km2_{iucn_cat}'] = outdf.Value.apply(lambda row: uniq_dict[row]*res**2 / 10**6
                                                               if row in uniq_dict.keys() else 0)
    return outdf