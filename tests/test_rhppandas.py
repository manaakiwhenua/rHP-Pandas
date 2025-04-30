import pytest

import pandas as pd
import geopandas as gpd

from geopandas.testing import assert_geodataframe_equal
from shapely.geometry import box, Polygon, LineString, MultiLineString

from rhppandas import rhppandas
from rhppandas.util.const import *
from rhealpixdggs import rhp_wrappers as rhp_py

pd.option_context("display.float_format", "{:0.15f}".format)
pd.set_option("display.precision", 15)


# Fixtures
@pytest.fixture
def basic_dataframe():
    """DataFrame with lat and lng columns"""
    return pd.DataFrame({"lat": [50, 51], "lng": [14, 15]})


@pytest.fixture
def basic_dataframe_with_values(basic_dataframe):
    """DataFrame with lat and lng columns and values"""
    return basic_dataframe.assign(val=[2, 5])


@pytest.fixture
def basic_geodataframe(basic_dataframe):
    """GeoDataFrame with POINT geometry"""
    geometry = gpd.points_from_xy(basic_dataframe["lng"], basic_dataframe["lat"])
    return gpd.GeoDataFrame(geometry=geometry, crs="epsg:4326")


@pytest.fixture
def basic_geodataframe_with_values(basic_geodataframe):
    """GeoDataFrame with POINT geometry and values"""
    return basic_geodataframe.assign(val=[2, 5])


@pytest.fixture
def basic_geodataframe_polygon():
    """GeoDataFrame with POLYGON geometry"""
    geom = box(0, 0, 1, 1)
    return gpd.GeoDataFrame(geometry=[geom], crs="epsg:4326")


@pytest.fixture
def basic_geodataframe_polygons():
    """GeoDataFrame with POLYGON geometries"""
    geoms = [box(14, 50, 15, 51), box(14, 50, 15, 52)]
    return gpd.GeoDataFrame(geometry=geoms, crs="epsg:4326")


@pytest.fixture
def basic_geodataframe_linestring():
    geom = LineString([(174.793092, -37.005372), (175.621138, -40.323142)])
    return gpd.GeoDataFrame(geometry=[geom], crs="epsg:4326")


@pytest.fixture
def basic_geodataframe_multilinestring():
    geom = MultiLineString(
        [
            [[174.793092, -37.005372], [175.621138, -40.323142]],
            [
                [-14.793092, -37.005372],
                [-15.621138, -40.323142],
                [-18.333333, -36.483403],
            ],
        ]
    )
    return gpd.GeoDataFrame(geometry=[geom], crs="epsg:4326")


@pytest.fixture
def basic_geodataframe_empty_linestring():
    """GeoDataFrame with Empty geometry"""
    return gpd.GeoDataFrame(geometry=[LineString()], crs="epsg:4326")


@pytest.fixture
def indexed_dataframe(basic_dataframe):
    """DataFrame with lat, lng and resolution 9 rHEALPix index"""
    return basic_dataframe.assign(rhp_09=["N216055611", "N208542111"]).set_index(
        f"{COLUMNS['prefix']}09"
    )


@pytest.fixture
def indexed_dataframe_centre_cells(basic_dataframe):
    """DataFrame with lat, lng and resolution 10 rHEALPix index"""
    return basic_dataframe.assign(rhp_10=["N2160556114", "N2085421114"]).set_index(
        f"{COLUMNS['prefix']}10"
    )


@pytest.fixture
def rhp_dataframe_with_values():
    """DataFrame with resolution 9 rHEALPix index and values"""
    index = ["N216055611", "N216055612", "N216055615"]
    return pd.DataFrame({"val": [1, 2, 5]}, index=index)


@pytest.fixture
def rhp_geodataframe_with_values(rhp_dataframe_with_values):
    """GeoDataFrame with resolution 9 rHEALPix index, values, and cell geometries"""
    geometry = [
        Polygon(rhp_py.rhp_to_geo_boundary(h, True, False))
        for h in rhp_dataframe_with_values.index
    ]
    return gpd.GeoDataFrame(
        rhp_dataframe_with_values, geometry=geometry, crs="epsg:4326"
    )


@pytest.fixture
def rhp_geodataframe_with_polyline_values(basic_geodataframe_linestring):
    return basic_geodataframe_linestring.assign(val=10)


# Tests: rHEALPix wrapper API
class TestGeoToRhp:
    def test_geo_to_rhp(self, basic_dataframe):
        result = basic_dataframe.rhp.geo_to_rhp(9)
        expected = basic_dataframe.assign(
            rhp_09=["N216055147", "N208518546"]
        ).set_index(f"{COLUMNS['prefix']}09")

        pd.testing.assert_frame_equal(expected, result)

    def test_geo_to_rhp_geo(self, basic_geodataframe):
        result = basic_geodataframe.rhp.geo_to_rhp(9)
        expected = basic_geodataframe.assign(
            rhp_09=["N216055147", "N208518546"]
        ).set_index(f"{COLUMNS['prefix']}09")

        pd.testing.assert_frame_equal(expected, result)

    def test_geo_to_rhp_polygon(self, basic_geodataframe_polygon):
        with pytest.raises(ValueError):
            basic_geodataframe_polygon.rhp.geo_to_rhp(9)


class TestRhpToGeo:
    def test_rhp_to_geo(self, indexed_dataframe):
        lats = [50.06543285982062, 51.06479381112059]
        lngs = [14.000847727642311, 14.998138688394175]
        geometry = gpd.points_from_xy(x=lngs, y=lats, crs="epsg:4326")
        expected = gpd.GeoDataFrame(indexed_dataframe, geometry=geometry)
        result = indexed_dataframe.rhp.rhp_to_geo()

        assert_geodataframe_equal(expected, result, check_less_precise=True)


class TestRhpToGeoBoundary:
    def test_rhp_to_geo_boundary(self, indexed_dataframe):
        c1 = (
            (13.996245382425958, 50.067960668809754),
            (14.0016956337431, 50.067960668809754),
            (14.00544959128063, 50.062905036612165),
            (13.999999999999975, 50.062905036612165),
            (13.996245382425958, 50.067960668809754),
        )
        c2 = (
            (14.993485139914386, 51.06731331121636),
            (14.999069305702065, 51.06731331121636),
            (15.002791736460077, 51.06227429726551),
            (14.997208263539921, 51.06227429726551),
            (14.993485139914386, 51.06731331121636),
        )
        geometry = [Polygon(c1), Polygon(c2)]

        result = indexed_dataframe.rhp.rhp_to_geo_boundary()
        expected = gpd.GeoDataFrame(
            indexed_dataframe, geometry=geometry, crs="epsg:4326"
        )

        assert_geodataframe_equal(expected, result, check_less_precise=True)

    def test_rhp_to_geo_boundary_wrong_index(self, indexed_dataframe):
        c = (
            (13.996245382425958, 50.067960668809754),
            (14.0016956337431, 50.067960668809754),
            (14.00544959128063, 50.062905036612165),
            (13.999999999999975, 50.062905036612165),
            (13.996245382425958, 50.067960668809754),
        )
        geometry = [Polygon(c), Polygon()]
        indexed_dataframe.index = [str(indexed_dataframe.index[0])] + ["invalid"]
        result = indexed_dataframe.rhp.rhp_to_geo_boundary()
        expected = gpd.GeoDataFrame(
            indexed_dataframe, geometry=geometry, crs="epsg:4326"
        )

        assert_geodataframe_equal(expected, result, check_less_precise=True)


class TestRhpGetResolution:
    def test_rhp_get_resolution(self, rhp_dataframe_with_values):
        expected = rhp_dataframe_with_values.assign(rhp_resolution=9)
        result = rhp_dataframe_with_values.rhp.rhp_get_resolution()

        pd.testing.assert_frame_equal(expected, result)

    def test_rhp_get_resolution_index_only(self, rhp_dataframe_with_values):
        del rhp_dataframe_with_values["val"]
        expected = rhp_dataframe_with_values.assign(rhp_resolution=9)
        result = rhp_dataframe_with_values.rhp.rhp_get_resolution()

        pd.testing.assert_frame_equal(expected, result)


class TestRhpGetBaseCell:
    def test_rhp_get_base_cell(self, indexed_dataframe):
        expected = indexed_dataframe.assign(rhp_base_cell=["N", "N"])
        result = indexed_dataframe.rhp.rhp_get_base_cell()

        pd.testing.assert_frame_equal(expected, result)


class TestRhpIsValid:
    def test_rhp_is_valid(self, indexed_dataframe):
        indexed_dataframe.index = [str(indexed_dataframe.index[0])] + ["invalid"]
        expected = indexed_dataframe.assign(rhp_is_valid=[True, False])
        result = indexed_dataframe.rhp.rhp_is_valid()

        pd.testing.assert_frame_equal(expected, result)


class TestKRing:
    def test_rhp_0_ring(self, indexed_dataframe_centre_cells):
        expected = indexed_dataframe_centre_cells.assign(
            rhp_k_ring=[[h] for h in indexed_dataframe_centre_cells.index]
        )
        result = indexed_dataframe_centre_cells.rhp.k_ring(0, verbose=False)
        pd.testing.assert_frame_equal(expected, result)

    def test_rhp_k_ring(self, indexed_dataframe_centre_cells):
        expected_indices = [
            {
                "N2160556114",
                "N2160556110",
                "N2160556111",
                "N2160556112",
                "N2160556115",
                "N2160556118",
                "N2160556117",
                "N2160556116",
                "N2160556113",
            },
            {
                "N2085421114",
                "N2085421110",
                "N2085421111",
                "N2085421112",
                "N2085421115",
                "N2085421118",
                "N2085421117",
                "N2085421116",
                "N2085421113",
            },
        ]
        expected = indexed_dataframe_centre_cells.assign(rhp_k_ring=expected_indices)
        result = indexed_dataframe_centre_cells.rhp.k_ring(verbose=False)
        result[COLUMNS["k_ring"]] = result[COLUMNS["k_ring"]].apply(
            set
        )  # Convert to set for testing
        pd.testing.assert_frame_equal(expected, result)

    def test_rhp_k_ring_explode(self, indexed_dataframe_centre_cells):
        expected_indices = set().union(
            *[
                {
                    "N2160556114",
                    "N2160556110",
                    "N2160556111",
                    "N2160556112",
                    "N2160556115",
                    "N2160556118",
                    "N2160556117",
                    "N2160556116",
                    "N2160556113",
                },
                {
                    "N2085421114",
                    "N2085421110",
                    "N2085421111",
                    "N2085421112",
                    "N2085421115",
                    "N2085421118",
                    "N2085421117",
                    "N2085421116",
                    "N2085421113",
                },
            ]
        )
        result = indexed_dataframe_centre_cells.rhp.k_ring(explode=True, verbose=False)
        assert len(result) == len(indexed_dataframe_centre_cells) * 9
        assert set(result[COLUMNS["k_ring"]]) == expected_indices
        assert not result["lat"].isna().any()


class TestCellRing:
    pass


class TestRhpToParent:
    def test_rhp_to_parent_level_1(self, rhp_dataframe_with_values):
        rhp_parent = "N2"
        result = rhp_dataframe_with_values.rhp.rhp_to_parent(1)
        expected = rhp_dataframe_with_values.assign(rhp_01=rhp_parent)

        pd.testing.assert_frame_equal(expected, result)

    def test_rhp_to_direct_parent(self, rhp_dataframe_with_values):
        rhp_parents = ["N21605561", "N21605561", "N21605561"]
        result = rhp_dataframe_with_values.rhp.rhp_to_parent()
        expected = rhp_dataframe_with_values.assign(rhp_parent=rhp_parents)

        pd.testing.assert_frame_equal(expected, result)

    def test_rhp_to_parent_level_0(self, rhp_dataframe_with_values):
        rhp_parent = "N"
        result = rhp_dataframe_with_values.rhp.rhp_to_parent(0)
        expected = rhp_dataframe_with_values.assign(rhp_00=rhp_parent)

        pd.testing.assert_frame_equal(expected, result)


class TestRhpToCenterChild:
    def test_rhp_to_center_child(self, indexed_dataframe):
        expected = indexed_dataframe.assign(
            rhp_center_child=["N216055611444", "N208542111444"]
        )
        result = indexed_dataframe.rhp.rhp_to_center_child(13)

        pd.testing.assert_frame_equal(expected, result)

    def test_rhp_to_center_child_one_level(self, indexed_dataframe):
        expected = indexed_dataframe.assign(
            rhp_center_child=["N2160556114", "N2085421114"]
        )
        result = indexed_dataframe.rhp.rhp_to_center_child()

        pd.testing.assert_frame_equal(expected, result)

    def test_rhp_to_center_child_wrong_index(self, indexed_dataframe):
        indexed_dataframe.index = [str(indexed_dataframe.index[0])] + ["invalid"]
        result = indexed_dataframe.rhp.rhp_to_center_child()
        expected = indexed_dataframe.assign(rhp_center_child=["N2160556114", None])

        pd.testing.assert_frame_equal(expected, result)


class TestPolyfill:
    def test_empty_polyfill(self, rhp_geodataframe_with_values):
        expected = rhp_geodataframe_with_values.assign(
            rhp_polyfill=[set(), set(), set()]
        )
        result = rhp_geodataframe_with_values.rhp.polyfill(1)
        assert_geodataframe_equal(expected, result)

    def test_polyfill(self, rhp_geodataframe_with_values):
        expected_cells = [
            {
                "N2160556110",
                "N2160556111",
                "N2160556112",
                "N2160556113",
                "N2160556114",
                "N2160556115",
                "N2160556116",
                "N2160556117",
                "N2160556118",
            },
            {
                "N2160556120",
                "N2160556121",
                "N2160556122",
                "N2160556123",
                "N2160556124",
                "N2160556125",
                "N2160556126",
                "N2160556127",
                "N2160556128",
            },
            {
                "N2160556150",
                "N2160556151",
                "N2160556152",
                "N2160556153",
                "N2160556154",
                "N2160556155",
                "N2160556156",
                "N2160556157",
                "N2160556158",
            },
        ]
        expected = rhp_geodataframe_with_values.assign(rhp_polyfill=expected_cells)
        result = rhp_geodataframe_with_values.rhp.polyfill(10)
        assert_geodataframe_equal(expected, result)

    def test_polyfill_explode(self, rhp_geodataframe_with_values):
        expected_indices = set().union(
            *[
                [
                    "N2160556110",
                    "N2160556111",
                    "N2160556112",
                    "N2160556113",
                    "N2160556114",
                    "N2160556115",
                    "N2160556116",
                    "N2160556117",
                    "N2160556118",
                ],
                [
                    "N2160556120",
                    "N2160556121",
                    "N2160556122",
                    "N2160556123",
                    "N2160556124",
                    "N2160556125",
                    "N2160556126",
                    "N2160556127",
                    "N2160556128",
                ],
                [
                    "N2160556150",
                    "N2160556151",
                    "N2160556152",
                    "N2160556153",
                    "N2160556154",
                    "N2160556155",
                    "N2160556156",
                    "N2160556157",
                    "N2160556158",
                ],
            ]
        )
        result = rhp_geodataframe_with_values.rhp.polyfill(10, explode=True)
        assert len(result) == len(rhp_geodataframe_with_values) * 9
        assert set(result[COLUMNS["polyfill"]]) == expected_indices
        assert not result["val"].isna().any()

    def test_polyfill_explode_unequal_lengths(self, basic_geodataframe_polygons):
        expected_indices = {
            "N2085",
            "N2160",
        }
        result = basic_geodataframe_polygons.rhp.polyfill(4, explode=True)
        assert len(result) == 3
        assert set(result[COLUMNS["polyfill"]]) == expected_indices


class TestCellArea:
    def test_cell_area(self, indexed_dataframe):
        expected = indexed_dataframe.assign(
            rhp_cell_area=[0.258507625363534, 0.258507625363534]
        )
        result = indexed_dataframe.rhp.cell_area()

        pd.testing.assert_frame_equal(expected, result)


class TestLinetrace:
    def test_empty_linetrace(self, basic_geodataframe_empty_linestring):
        result = basic_geodataframe_empty_linestring.rhp.linetrace(2, verbose=False)
        assert result.iloc[0][COLUMNS["linetrace"]] == None

    def test_linetrace(self, basic_geodataframe_linestring):
        result = basic_geodataframe_linestring.rhp.linetrace(3)
        expected_indices = ["R884", "R887"]
        assert len(result.iloc[0][COLUMNS["linetrace"]]) == 2
        assert list(result.iloc[0][COLUMNS["linetrace"]]) == expected_indices

    def test_linetrace_explode(self, basic_geodataframe_linestring):
        result = basic_geodataframe_linestring.rhp.linetrace(3, explode=True)
        expected_indices = ["R884", "R887"]
        assert result.shape == (2, 2)
        assert result.iloc[0][COLUMNS["linetrace"]] == expected_indices[0]
        assert result.iloc[-1][COLUMNS["linetrace"]] == expected_indices[-1]

    def test_linetrace_with_values(self, rhp_geodataframe_with_polyline_values):
        result = rhp_geodataframe_with_polyline_values.rhp.linetrace(3)
        expected_indices = ["R884", "R887"]
        assert result.shape == (1, 3)
        assert "val" in result.columns
        assert result.iloc[0]["val"] == 10
        assert len(result.iloc[0][COLUMNS["linetrace"]]) == 2
        assert list(result.iloc[0][COLUMNS["linetrace"]]) == expected_indices

    def test_linetrace_with_values_explode(self, rhp_geodataframe_with_polyline_values):
        result = rhp_geodataframe_with_polyline_values.rhp.linetrace(3, explode=True)
        expected_indices = ["R884", "R885", "R888", "R887"]
        assert result.shape == (2, 3)
        assert "val" in result.columns
        assert result.iloc[0]["val"] == 10
        assert result.iloc[0][COLUMNS["linetrace"]] == expected_indices[0]
        assert result.iloc[-1][COLUMNS["linetrace"]] == expected_indices[-1]
        assert not result["val"].isna().any()

    def test_linetrace_multiline(self, basic_geodataframe_multilinestring):
        result = basic_geodataframe_multilinestring.rhp.linetrace(3)
        expected_indices = ["R884", "R887", "P874", "P877", "P876", "P873"]
        assert len(result.iloc[0][COLUMNS["linetrace"]]) == 6  # 6 cells total
        assert list(result.iloc[0][COLUMNS["linetrace"]]) == expected_indices

    def test_linetrace_multiline_explode_index_parts(
        self, basic_geodataframe_multilinestring
    ):
        result = basic_geodataframe_multilinestring.explode(
            index_parts=True
        ).rhp.linetrace(3, explode=True)
        expected_indices = [["R884", "R887"], ["P874", "P877", "P876", "P873"]]
        assert len(result[COLUMNS["linetrace"]]) == 6  # 6 cells in total
        assert result.iloc[0][COLUMNS["linetrace"]] == expected_indices[0][0]
        assert result.iloc[-1][COLUMNS["linetrace"]] == expected_indices[-1][-1]

    def test_linetrace_multiline_index_parts_no_explode(
        self, basic_geodataframe_multilinestring
    ):
        result = basic_geodataframe_multilinestring.explode(
            index_parts=True
        ).rhp.linetrace(3, explode=False)
        expected_indices = [["R884", "R887"], ["P874", "P877", "P876", "P873"]]
        assert len(result[COLUMNS["linetrace"]]) == 2  # 2 parts
        assert len(result.iloc[0][COLUMNS["linetrace"]]) == 2  # 2 cells
        assert result.iloc[0][COLUMNS["linetrace"]] == expected_indices[0]
        assert len(result.iloc[-1][COLUMNS["linetrace"]]) == 4  # 4 cells
        assert result.iloc[-1][COLUMNS["linetrace"]] == expected_indices[-1]


# Tests: Aggregate functions
class TestGeoToRhpAggregate:
    def test_geo_to_rhp_aggregate(self, basic_dataframe_with_values):
        result = basic_dataframe_with_values.rhp.geo_to_rhp_aggregate(
            1, return_geometry=False
        )
        expected = pd.DataFrame(
            {f"{COLUMNS['prefix']}01": ["N2"], "val": [2 + 5]}
        ).set_index(f"{COLUMNS['prefix']}01")

        pd.testing.assert_frame_equal(expected, result)

    def test_geo_to_rhp_aggregate_geo(self, basic_geodataframe_with_values):
        result = basic_geodataframe_with_values.rhp.geo_to_rhp_aggregate(
            1, return_geometry=False
        )
        expected = pd.DataFrame(
            {f"{COLUMNS['prefix']}01": ["N2"], "val": [2 + 5]}
        ).set_index(f"{COLUMNS['prefix']}01")

        pd.testing.assert_frame_equal(expected, result)

    def test_geo_to_rhp_aggregate_with_geometry(self, basic_dataframe_with_values):
        result = basic_dataframe_with_values.rhp.geo_to_rhp_aggregate(1)
        indexed = pd.DataFrame(
            {f"{COLUMNS['prefix']}01": ["N2"], "val": [2 + 5]}
        ).set_index(f"{COLUMNS['prefix']}01")
        geometry = [
            Polygon(rhp_py.rhp_to_geo_boundary(h, True, False)) for h in indexed.index
        ]
        expected = gpd.GeoDataFrame(indexed, geometry=geometry, crs="epsg:4326")

        assert_geodataframe_equal(expected, result)


class TestRhpToParentAggregate:
    def test_rhp_to_parent_aggregate(self, rhp_geodataframe_with_values):
        result = rhp_geodataframe_with_values.rhp.rhp_to_parent_aggregate(8)

        index = pd.Index(["N21605561"], name=f"{COLUMNS['prefix']}08")
        geometry = [Polygon(rhp_py.rhp_to_geo_boundary(h, True, False)) for h in index]
        expected = gpd.GeoDataFrame(
            {"val": [1 + 2 + 5]}, geometry=geometry, index=index, crs="epsg:4326"
        )

        assert_geodataframe_equal(expected, result)

    def test_rhp_to_parent_aggregate_no_geometry(self, rhp_dataframe_with_values):
        result = rhp_dataframe_with_values.rhp.rhp_to_parent_aggregate(
            8, return_geometry=False
        )
        index = pd.Index(["N21605561"], name=f"{COLUMNS['prefix']}08")
        expected = pd.DataFrame({"val": [1 + 2 + 5]}, index=index)

        pd.testing.assert_frame_equal(expected, result)


class TestPolyfillResample:
    def test_polyfill_resample(self, rhp_geodataframe_with_values):
        expected_indices = set().union(
            *[
                [
                    "N2160556110",
                    "N2160556111",
                    "N2160556112",
                    "N2160556113",
                    "N2160556114",
                    "N2160556115",
                    "N2160556116",
                    "N2160556117",
                    "N2160556118",
                ],
                [
                    "N2160556120",
                    "N2160556121",
                    "N2160556122",
                    "N2160556123",
                    "N2160556124",
                    "N2160556125",
                    "N2160556126",
                    "N2160556127",
                    "N2160556128",
                ],
                [
                    "N2160556150",
                    "N2160556151",
                    "N2160556152",
                    "N2160556153",
                    "N2160556154",
                    "N2160556155",
                    "N2160556156",
                    "N2160556157",
                    "N2160556158",
                ],
            ]
        )
        expected_values = set([1, 2, 5])
        result = rhp_geodataframe_with_values.rhp.polyfill_resample(
            10, return_geometry=False
        )
        assert len(result) == len(rhp_geodataframe_with_values) * 9
        assert set(result.index) == expected_indices
        assert set(result["val"]) == expected_values
        assert not result["val"].isna().any()

    def test_polyfill_resample_uncovered_rows(self, basic_geodataframe_polygons):
        basic_geodataframe_polygons.iloc[1] = box(14, 50, 15, 53)
        with pytest.warns(UserWarning):
            result = basic_geodataframe_polygons.rhp.polyfill_resample(2)

        assert len(result) == 0
