from typing import Union, Literal, Callable, Any

import shapely
import pandas as pd
import geopandas as gpd

import rhealpixdggs.rhp_wrappers as rhp_py

from .util.functools import wrapped_partial

AnyDataFrame = Union[pd.DataFrame, gpd.GeoDataFrame]


@pd.api.extensions.register_dataframe_accessor("rhp")
class rHPAccessor:
    """
    Shamelessly appropriated from equivalent class in h3pandas package

    The h3pandas repo is found here: https://github.com/DahnJ/H3-Pandas
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

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
        colname = f"rhp_{resolution:02}"
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
            "geometry",
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
            "geometry",
            lambda x: shapely.geometry.Polygon(x),
            lambda x: gpd.GeoDataFrame(
                x, crs="epsg:4326"
            ),  # TODO: add correct coordinate system?
        )

    def rhp_get_resolution(self) -> AnyDataFrame:
        """
        Adds a column 'rhp_resolution' with the resolution of each cell to the dataframe.
        """
        return self._apply_index_assign(rhp_py.rhp_get_resolution, "rhp_resolution")

    def rhp_get_base_cell(self) -> AnyDataFrame:
        """
        Adds a column 'rhp_base_cell' with the resolution 0 parent cell to the dataframe.
        """
        return self._apply_index_assign(rhp_py.rhp_get_base_cell, "rhp_base_cell")

    def rhp_is_valid(self) -> AnyDataFrame:
        """
        Adds a column 'rhp_is_valid' indicating if the cell addresses are valid rHEALPix
        addresses or not.
        """
        return self._apply_index_assign(rhp_py.rhp_is_valid, "rhp_is_valid")

    def k_ring(self, k: int = 1, explode: bool = False) -> AnyDataFrame:
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
        func = wrapped_partial(rhp_py.k_ring, k=k)
        column_name = "rhp_k_ring"
        if explode:
            return self._apply_index_explode(func, column_name, list)
        return self._apply_index_assign(func, column_name, list)

    def cell_ring(self, k: int = 1, explode: bool = False) -> AnyDataFrame:
        """
        Adds a column 'rhp_cell_ring' of cells at distance k from the existing entries
        to the dataframe.

        explode = False will add the cell ring as a list associated with the existing
        entry.

        explode = True will add the cell ring one cell at a time (repeating existing
        entries).
        """
        func = wrapped_partial(rhp_py.cell_ring, k=k)
        column_name = "rhp_cell_ring"
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
        column = f"rhp_{resolution:02}" if resolution is not None else "rhp_parent"

        return self._apply_index_assign(
            wrapped_partial(rhp_py.rhp_to_parent, res=resolution), column
        )

    def rhp_to_center_child(self, resolution: int = None) -> AnyDataFrame:
        """
        Adds a column 'rhp_center_child' with the address of the central child
        cell at the requested resolution to the dataframe.
        ----------
        Parameters
        ----------
        resolution : int or None
            rHEALPix resolution. If none, then returns the child of resolution
            directly below that of each rHEALPix cell
        """
        return self._apply_index_assign(
            wrapped_partial(rhp_py.rhp_to_center_child, res=resolution),
            "rhp_center_child",
        )

    def polyfill(self) -> AnyDataFrame:
        raise NotImplementedError()

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
            wrapped_partial(rhp_py.cell_area, unit=unit), "rhp_cell_area"
        )

    def geo_to_rhp_aggregate(self) -> pd.DataFrame:
        raise NotImplementedError()

    def rhp_to_parent_aggregate(self) -> gpd.GeoDataFrame:
        raise NotImplementedError()

    # TODO: placeholder, find out if rhp needs that function
    # def k_ring_smoothing(self) -> AnyDataFrame:
    #    pass

    # TODO: placeholder, find out if rhp needs that function
    # def weighted_square_ring(self):
    #    pass

    def polyfill_resample(self) -> AnyDataFrame:
        raise NotImplementedError()

    def linetrace(self) -> AnyDataFrame:
        raise NotImplementedError()

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

    def _multiply_numeric(self):
        raise NotImplementedError()
