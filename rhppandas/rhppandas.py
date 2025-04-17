from typing import Union, Literal, Callable, Any
from warnings import warn

import shapely
import pandas as pd
import geopandas as gpd

import rhealpixdggs.rhp_wrappers as rhp_py

from .util.const import *
from .util.functools import wrapped_partial

AnyDataFrame = Union[pd.DataFrame, gpd.GeoDataFrame]


@pd.api.extensions.register_dataframe_accessor("rhp")
class rHPAccessor:
    """
    Shamelessly appropriated from equivalent class in h3pandas package

    The h3pandas repo is found here: https://github.com/DahnJ/H3-Pandas

    TODO: - Support both plane and sphere (currently hardwired to sphere)
          - Support user defined instance of underlying dggs (currently hardwired to WGS84_003)
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    # RHP wrapper API
    def geo_to_rhp(
        self,
        resolution: int,
        lat_col: str = "lat",
        lng_col: str = "lng",
        set_index: bool = True,
    ) -> AnyDataFrame:
        """
        Adds rHEALPix index to (Geo)DataFrame

        pd.DataFrame: uses `lat_col` and `lng_col` (default `lat` and `lng`)
        gpd.GeoDataFrame: uses `geometry`

        resolution : int
            rHEALPix resolution
        lat_col : str
            Name of the latitude column (if used), default 'lat'
        lng_col : str
            Name of the longitude column (if used), default 'lng'
        set_index : bool
            If True, the columns with rHEALPix addresses is set as index, default 'True'

        Returns
        -------
        (Geo)DataFrame with rHEALPix addresses added
        """

        # DataFrame wrangling
        if isinstance(self._df, gpd.GeoDataFrame):
            lngs = self._df.geometry.x
            lats = self._df.geometry.y
        else:
            lngs = self._df[lng_col]
            lats = self._df[lat_col]

        # Index conversion
        rhpaddresses = [
            rhp_py.geo_to_rhp(lat, lng, resolution, False)
            for lat, lng in zip(lats, lngs)
        ]

        # Add results to DataFrame
        colname = f"{COLUMNS['prefix']}{resolution:02}"
        assign_arg = {colname: rhpaddresses}
        df = self._df.assign(**assign_arg)
        if set_index:
            return df.set_index(colname)
        return df

    def rhp_to_geo(self) -> gpd.GeoDataFrame:
        """Add `geometry` with centroid of each rHEALPix address to the DataFrame.
        Assumes rHEALPix index.

        Returns
        -------
        GeoDataFrame with Point geometry

        See Also
        --------
        rhp_to_geo_boundary : Adds an rHEALPix cell
        """
        return self._apply_index_assign(
            wrapped_partial(rhp_py.rhp_to_geo, geo_json=True, plane=False),
            COLUMNS["geometry"],
            lambda x: shapely.geometry.Point(x),
            lambda x: gpd.GeoDataFrame(
                x, crs="epsg:4326"
            ),  # TODO: add correct coordinate system?
        )

    def rhp_to_geo_boundary(self) -> AnyDataFrame:
        """Add `geometry` with rHEALPix squares to the DataFrame. Assumes rHEALPix index.

        Returns
        -------
        GeoDataFrame with rHEALPix geometry
        """
        return self._apply_index_assign(
            wrapped_partial(rhp_py.rhp_to_geo_boundary, geo_json=True, plane=False),
            COLUMNS["geometry"],
            lambda x: shapely.geometry.Polygon(x),
            lambda x: gpd.GeoDataFrame(
                x, crs="epsg:4326"
            ),  # TODO: add correct coordinate system?
        )

    def rhp_get_resolution(self) -> AnyDataFrame:
        """
        Adds a column 'rhp_resolution' with the resolution of each cell to the dataframe.
        """
        return self._apply_index_assign(
            rhp_py.rhp_get_resolution, COLUMNS["resolution"]
        )

    def rhp_get_base_cell(self) -> AnyDataFrame:
        """
        Adds a column 'rhp_base_cell' with the resolution 0 parent cell to the dataframe.
        """
        return self._apply_index_assign(rhp_py.rhp_get_base_cell, COLUMNS["base_cell"])

    def rhp_is_valid(self) -> AnyDataFrame:
        """
        Adds a column 'rhp_is_valid' indicating if the cell addresses are valid rHEALPix
        addresses or not.
        """
        return self._apply_index_assign(rhp_py.rhp_is_valid, COLUMNS["is_valid"])

    def k_ring(
        self, k: int = 1, explode: bool = False, verbose: bool = True
    ) -> AnyDataFrame:
        """
        Parameters
        ----------
        k : int
            the distance from the origin rHEALPix address. Default k = 1
        explode : bool
            If True, will explode the resulting list vertically.
            All other columns' values are copied.
            Default: False

        TODO: find out if rhp needs the following note (and the referenced function)
        See Also
        --------
        k_ring_smoothing : Extended API method that distributes numeric values
            to the k-ring cells
        """
        if verbose:
            warn(str.format(rhp_py.CELL_RING_WARNING, "k"))

        func = wrapped_partial(rhp_py.k_ring, k=k, verbose=False)
        column_name = COLUMNS["k_ring"]
        if explode:
            return self._apply_index_explode(func, column_name, list)
        return self._apply_index_assign(func, column_name, list)

    def cell_ring(
        self, k: int = 1, explode: bool = False, verbose: bool = True
    ) -> AnyDataFrame:
        """
        Adds a column 'rhp_cell_ring' of cells at distance k from the existing entries
        to the dataframe.

        explode = False will add the cell ring as a list associated with the existing
        entry.

        explode = True will add the cell ring one cell at a time (repeating existing
        entries).
        """
        if verbose:
            warn(str.format(rhp_py.CELL_RING_WARNING, "cell"))

        func = wrapped_partial(rhp_py.cell_ring, k=k, verbose=False)
        column_name = COLUMNS["cell_ring"]
        if explode:
            return self._apply_index_explode(func, column_name, list)
        return self._apply_index_assign(func, column_name, list)

    def rhp_to_parent(self, resolution: int = None) -> AnyDataFrame:
        """
        Adds a column 'rhp_parent' with the parent cell at the requested resolution to the
        dataframe.
        ----------
        Parameters
        ----------
        resolution : int or None
            rHEALPix resolution. If None, then returns the direct parent of each rHEALPix cell.
        """
        column = (
            f"{COLUMNS['prefix']}{resolution:02}"
            if resolution is not None
            else COLUMNS["parent"]
        )

        return self._apply_index_assign(
            wrapped_partial(rhp_py.rhp_to_parent, res=resolution), column
        )

    def rhp_to_center_child(self, resolution: int = None) -> AnyDataFrame:
        """
        Adds a column 'rhp_center_child' with the address of the central child cell at the
        requested resolution to the dataframe.
        ----------
        Parameters
        ----------
        resolution : int or None
            rHEALPix resolution. If none, then returns the child of resolution directly
            below that of each rHEALPix cell
        """
        return self._apply_index_assign(
            wrapped_partial(rhp_py.rhp_to_center_child, res=resolution),
            COLUMNS["center_child"],
        )

    def polyfill(
        self,
        resolution: int,
        explode: bool = False,
        compress: bool = False,
        verbose: bool = True,
    ) -> AnyDataFrame:
        """
        Adds a column 'rhp_polyfill' listing the cells where the cell centroid is
        contained within the input (multi)polygon geometry.
        Relies on the dataframe having a 'geometry' column with shapely Polygon or
        MultiPolygon entries.
        ----------
        Parameters
        ----------
        resolution : int
            rHEALPix resolution
        explode : bool
            If True, will explode the resulting list vertically.
            All other columns' values are copied.
            Default: False
        compress : bool
            If True, will group cells making up a parent cell and use the address of the
            parent cell instead of the individual child addresses.
            Default: False
        """

        # Need to wrap polyfill for each dataframe row so we can call it with geometry
        def func(row):
            if not COLUMNS["geometry"] in row.keys():
                return None
            else:
                return rhp_py.polyfill(
                    row[COLUMNS["geometry"]], resolution, False, compress, verbose
                )

        # Polyfill cell sets for each row
        result = self._df.apply(func, axis=1)

        if not explode:
            assign_args = {COLUMNS["polyfill"]: result}
            return self._df.assign(**assign_args)

        result = result.explode().to_frame(COLUMNS["polyfill"])

        return self._df.join(result)

    def cell_area(self, unit: Literal["km^2", "m^2"] = "km^2") -> AnyDataFrame:
        """
        Adds a column 'rhp_cell_area' to the dataframe of cells addresses.
        ----------
        Parameters
        ----------
        unit : str, options: 'km^2' or 'm^2'
            Unit for area result. Default: 'km^2`

        TODO: find out the meaning of unit "rads^2" that appears in h3pandas
        """
        return self._apply_index_assign(
            wrapped_partial(rhp_py.cell_area, unit=unit), COLUMNS["cell_area"]
        )

    def linetrace(
        self, resolution: int, explode: bool = False, verbose: bool = True
    ) -> AnyDataFrame:
        """Experimental. An rHEALPix cell representation of a (Multi)LineString,
        which permits repeated cells, but not if they are repeated in immediate
        sequence.

        Parameters
        ----------
        resolution : int
            rHEALPix resolution
        explode : bool
            If True, will explode the resulting list vertically.
            All other columns' values are copied.
            Default: False

        Returns
        -------
        (Geo)DataFrame with rHEALPix cells with centroids within the input polygons.
        """

        # Need to wrap linetrace for each dataframe row so we can call it with geometry
        def func(row):
            if not COLUMNS["geometry"] in row.keys():
                return None
            else:
                return rhp_py.linetrace(
                    row[COLUMNS["geometry"]], resolution, plane=False, verbose=verbose
                )

        df = self._df

        # Linetrace cell sets for each row
        result = df.apply(func, axis=1)
        if not explode:
            assign_args = {COLUMNS["linetrace"]: result}
            return df.assign(**assign_args)

        result = result.explode().to_frame(COLUMNS["linetrace"])
        return df.join(result)

    # Aggregate functions
    def geo_to_rhp_aggregate(
        self,
        resolution: int,
        operation: Union[dict, str, Callable] = "sum",
        lat_col: str = "lat",
        lng_col: str = "lng",
        return_geometry: bool = True,
    ) -> pd.DataFrame:
        """Adds rHEALPix index to DataFrame, groups points with the same index
        and performs `operation`.

        pd.DataFrame: uses `lat_col` and `lng_col` (default `lat` and `lng`)
        gpd.GeoDataFrame: uses `geometry`

        Parameters
        ----------
        resolution : int
            rHEALPix resolution
        operation : Union[dict, str, Callable]
            Argument passed to DataFrame's `agg` method, default 'sum'
        lat_col : str
            Name of the latitude column (if used), default 'lat'
        lng_col : str
            Name of the longitude column (if used), default 'lng'
        return_geometry: bool
            (Optional) Whether to add a `geometry` column with the square cells.
            Default = True

        Returns
        -------
        (Geo)DataFrame aggregated by rHEALPix address into which each row's point falls

        See Also
        --------
        geo_to_rhp : rHEALPix API method upon which this function builds

        """
        colname = (
            f"{COLUMNS['prefix']}{resolution:02}"
            if resolution is not None
            else COLUMNS["parent"]
        )
        grouped = pd.DataFrame(
            self.geo_to_rhp(resolution, lat_col, lng_col, False)
            .drop(columns=[lat_col, lng_col, COLUMNS["geometry"]], errors="ignore")
            .groupby(colname)
            .agg(operation)
        )

        return grouped.rhp.rhp_to_geo_boundary() if return_geometry else grouped

    def rhp_to_parent_aggregate(
        self,
        resolution: int,
        operation: Union[dict, str, Callable] = "sum",
        return_geometry: bool = True,
    ) -> gpd.GeoDataFrame:
        """Assigns parent cell to each row, groups by it and performs `operation`.
        Assumes rHEALPix index.

        Parameters
        ----------
        resolution : int
            rHEALPix resolution
        operation : Union[dict, str, Callable]
            Argument passed to DataFrame's `agg` method, default 'sum'
        return_geometry: bool
            (Optional) Whether to add a `geometry` column with the square cells.
            Default = True

        Returns
        -------
        (Geo)DataFrame aggregated by the parent of each rHEALPix address

        See Also
        --------
        rhp_to_parent : rHEALPix API method upon which this function builds

        """
        parent_rhpaddresses = [
            rhp_py.rhp_to_parent(rhpaddress, resolution)
            for rhpaddress in self._df.index
        ]
        rhp_parent_column = (
            f"{COLUMNS['prefix']}{resolution:02}"
            if resolution is not None
            else COLUMNS["parent"]
        )
        kwargs_assign = {rhp_parent_column: parent_rhpaddresses}
        grouped = (
            self._df.assign(**kwargs_assign)
            .groupby(rhp_parent_column)[
                [c for c in self._df.columns if c != COLUMNS["geometry"]]
            ]
            .agg(operation)
        )

        return grouped.rhp.rhp_to_geo_boundary() if return_geometry else grouped

    def polyfill_resample(
        self,
        resolution: int,
        return_geometry: bool = True,
        compress: bool = False,
        verbose: bool = True,
    ) -> AnyDataFrame:
        """Experimental as stated in h3pandas, where this function comes from.
        Currently essentially polyfill(..., explode=True) that sets the rHEALPix
        index and adds the rHEALPix cell geometry if requested by return_geometry.

        Parameters
        ----------
        resolution : int
            rHEALPix resolution
        return_geometry: bool
            (Optional) Whether to add a `geometry` column with the hexagonal cells.
            Default = True
        compress : bool
            (Optional) Whether to compress cell groups that make up a parent cell
            into the parent, returning 1 id instead of 9.
            Default = False

        Returns
        -------
        (Geo)DataFrame with rHEALPix cells with centroids within the input polygons.

        See Also
        --------
        polyfill : rHEALPix API method upon which this method builds
        """
        result = self._df.rhp.polyfill(
            resolution, explode=True, compress=compress, verbose=verbose
        )
        uncovered_rows = result[COLUMNS["polyfill"]].isna()
        n_uncovered_rows = uncovered_rows.sum()
        if verbose and (n_uncovered_rows > 0):
            warn(
                f"{n_uncovered_rows} rows did not generate a cell."
                "Consider using a finer resolution."
            )
            result = result.loc[~uncovered_rows]

        result = result.reset_index().set_index(COLUMNS["polyfill"])

        return result.rhp.rhp_to_geo_boundary() if return_geometry else result

    # Helper functions
    def _apply_index_assign(
        self,
        func: Callable,
        column_name: str,
        processor: Callable = lambda x: x,
        finalizer: Callable = lambda x: x,
    ) -> Any:
        """
        Helper method. Applies `func` to index and assigns the result to `column`.

        Parameters
        ----------
        func : Callable
            single-argument function to be applied to each rHEALPix address
        column_name : str
            name of the resulting column
        processor : Callable
            (Optional) further processes the result of func. Default: identity
        finalizer : Callable
            (Optional) further processes the resulting dataframe. Default: identity

        Returns
        -------
        Dataframe with column `column` containing the result of `func`.
        If using `finalizer`, can return anything the `finalizer` returns.
        """
        result = [processor(func(rhpaddress)) for rhpaddress in self._df.index]
        assign_args = {column_name: result}

        return finalizer(self._df.assign(**assign_args))

    def _apply_index_explode(
        self,
        func: Callable,
        column_name: str,
        processor: Callable = lambda x: x,
        finalizer: Callable = lambda x: x,
    ) -> Any:
        """Helper method. Applies a list-making `func` to index and performs
        a vertical explode.
        Any additional values are simply copied to all the rows.

        Parameters
        ----------
        func : Callable
            single-argument function to be applied to each H3 address
        column_name : str
            name of the resulting column
        processor : Callable
            (Optional) further processes the result of func. Default: identity
        finalizer : Callable
            (Optional) further processes the resulting dataframe. Default: identity

        Returns
        -------
        Dataframe with column `column` containing the result of `func`.
        If using `finalizer`, can return anything the `finalizer` returns.
        """
        result = (
            pd.DataFrame.from_dict(
                {
                    rhpaddress: processor(func(rhpaddress))
                    for rhpaddress in self._df.index
                },
                orient="index",
            )
            .stack()
            .to_frame(column_name)
            .reset_index(level=1, drop=True)
        )
        result = self._df.join(result)
        return finalizer(result)
