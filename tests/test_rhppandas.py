import pytest

import pandas as pd
import geopandas as gpd
from geopandas.testing import assert_geodataframe_equal
from shapely.geometry import box, Polygon

from rhppandas import rhppandas
from rhealpixdggs import rhp_wrappers as rhp_py


# Fixtures
@pytest.fixture
def basic_dataframe():
    """DataFrame with lat and lng columns"""
    return pd.DataFrame({"lat": [50, 51], "lng": [14, 15]})


@pytest.fixture
def basic_geodataframe(basic_dataframe):
    """GeoDataFrame with POINT geometry"""
    geometry = gpd.points_from_xy(basic_dataframe["lng"], basic_dataframe["lat"])
    return gpd.GeoDataFrame(geometry=geometry, crs="epsg:4326")


@pytest.fixture
def basic_geodataframe_polygon():
    geom = box(0, 0, 1, 1)
    return gpd.GeoDataFrame(geometry=[geom], crs="epsg:4326")


@pytest.fixture
def indexed_dataframe(basic_dataframe):
    """DataFrame with lat, lng and resolution 9 rHEALPix index"""
    return basic_dataframe.assign(rhp_09=["N216055611", "N208542111"]).set_index(
        "rhp_09"
    )


@pytest.fixture
def indexed_dataframe_centre_cells(basic_dataframe):
    """DataFrame with lat, lng and resolution 10 rHEALPix index"""
    return basic_dataframe.assign(rhp_10=["N2160556114", "N2085421114"]).set_index(
        "rhp_10"
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
        Polygon(rhp_py.rhp_to_geo_boundary(h, True))
        for h in rhp_dataframe_with_values.index
    ]
    return gpd.GeoDataFrame(
        rhp_dataframe_with_values, geometry=geometry, crs="epsg:4326"
    )


# Tests: rHEALPix wrapper API
class TestGeoToRhp:
    def test_geo_to_rhp(self, basic_dataframe):
        result = basic_dataframe.rhp.geo_to_rhp(9)
        expected = basic_dataframe.assign(
            rhp_09=["N216055611", "N208542111"]
        ).set_index("rhp_09")

        pd.testing.assert_frame_equal(expected, result)

    def test_geo_to_rhp_geo(self, basic_geodataframe):
        result = basic_geodataframe.rhp.geo_to_rhp(9)
        expected = basic_geodataframe.assign(
            rhp_09=["N216055611", "N208542111"]
        ).set_index("rhp_09")

        pd.testing.assert_frame_equal(expected, result)

    def test_geo_to_rhp_polygon(self, basic_geodataframe_polygon):
        with pytest.raises(ValueError):
            basic_geodataframe_polygon.rhp.geo_to_rhp(9)


class TestRhpToGeo:
    def test_rhp_to_geo(self, indexed_dataframe):
        lats = [50.00206177482531, 51.00185487171624]
        lngs = [14.000847727642356, 14.998138688394192]
        geometry = gpd.points_from_xy(x=lngs, y=lats, crs="epsg:4326")
        expected = gpd.GeoDataFrame(indexed_dataframe, geometry=geometry)
        result = indexed_dataframe.rhp.rhp_to_geo()

        assert_geodataframe_equal(expected, result, check_less_precise=True)


class TestRhpToGeoBoundary:
    def test_rhp_to_geo_boundary(self, indexed_dataframe):
        c1 = (
            (13.996245382425982, 50.004590579705954),
            (14.001695633743132, 50.004590579705954),
            (14.005449591280690, 49.999532956048753),
            (14.000000000000031, 49.999532956048753),
            (13.996245382425982, 50.004590579705954),
        )
        c2 = (
            (14.993485139914398, 51.004375558275498),
            (14.999069305702077, 51.004375558275498),
            (15.002791736460116, 50.999334171715851),
            (14.997208263539958, 50.999334171715851),
            (14.993485139914398, 51.004375558275498),
        )
        geometry = [Polygon(c1), Polygon(c2)]

        result = indexed_dataframe.rhp.rhp_to_geo_boundary()
        expected = gpd.GeoDataFrame(
            indexed_dataframe, geometry=geometry, crs="epsg:4326"
        )

        assert_geodataframe_equal(expected, result, check_less_precise=True)

    def test_rhp_to_geo_boundary_wrong_index(self, indexed_dataframe):
        c = (
            (13.996245382425982, 50.004590579705954),
            (14.001695633743132, 50.004590579705954),
            (14.005449591280690, 49.999532956048753),
            (14.000000000000031, 49.999532956048753),
            (13.996245382425982, 50.004590579705954),
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
        result = indexed_dataframe_centre_cells.rhp.k_ring(0)
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
        result = indexed_dataframe_centre_cells.rhp.k_ring()
        result["rhp_k_ring"] = result["rhp_k_ring"].apply(
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
        result = indexed_dataframe_centre_cells.rhp.k_ring(explode=True)
        assert len(result) == len(indexed_dataframe_centre_cells) * 9
        assert set(result["rhp_k_ring"]) == expected_indices
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
    pass


class TestCellArea:
    def test_cell_area(self, indexed_dataframe):
        expected = indexed_dataframe.assign(
            rhp_cell_area=[0.2587977645498284, 0.2587977645498284]
        )
        result = indexed_dataframe.rhp.cell_area()

        pd.testing.assert_frame_equal(expected, result)


class TestGeoToRhpAggregate:
    pass


class TestRhpToParentAggregate:
    pass


# TODO: placeholder, find out if rhp needs that test class
# class TestKRingSmoothing:
#    pass

# TODO: placeholder, find out if rhp needs that test class
# class TestWeightedCellRing:
#    pass


class TestPolyfillResample:
    pass


class TestLinetrace:
    pass
