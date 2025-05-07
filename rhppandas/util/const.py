WARNING_NO_CRS = "WARNING: No CRS information found in dataframe. Assuming EPSG:4326."
WARNING_CRS_NOT_SET = "WARNING: CRS not set in GeoDataFrame. Assuming EPSG:4326."
WARNING_UNSUPPORTED_CRS = "WARNING: GeoDataframe uses coordinate system {0} while rhppandas only supports EPSG:4326. Results will be inaccurate at best and unusable at worst."

COLUMNS = {
    "prefix": "rhp_",
    "is_valid": "rhp_is_valid",
    "resolution": "rhp_resolution",
    "base_cell": "rhp_base_cell",
    "parent": "rhp_parent",
    "center_child": "rhp_center_child",
    "cell_area": "rhp_cell_area",
    "cell_ring": "rhp_cell_ring",
    "k_ring": "rhp_k_ring",
    "polyfill": "rhp_polyfill",
    "linetrace": "rhp_linetrace",
    "geometry": "geometry",
}
