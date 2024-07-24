import pytest

import pandas as pd
import geopandas as gpd
from geopandas.testing import assert_geodataframe_equal
from shapely.geometry import box

from rhppandas import rhppandas
from rhealpixdggs import rhp_wrappers


# Fixtures
# NOTE: These are the same as those in h3pandas


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
def basic_geodataframe_polygon(basic_geodataframe):
    geom = box(0, 0, 1, 1)
    return gpd.GeoDataFrame(geometry=[geom], crs="epsg:4326")


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
    pass


class TestRhpToGeoBoundary:
    pass  # TODO


class TestRhpGetResolution:
    pass


class TestRhpGetBaseCell:
    pass


class TestRhpIsValid:
    pass


class TestKRing:
    pass


# TODO: placeholder, find out if rhp needs that test class
# class TestHexRing:
#    pass


class TestRhpToParent:
    pass  # TODO


class TestRhpToCenterChild:
    pass


class TestPolyfill:
    pass


class TestCellArea:
    pass


class TestGeoToRhpAggregate:
    pass


class TestRhpToParentAggregate:
    pass


# TODO: placeholder, find out if rhp needs that test class
# class TestKRingSmoothing:
#    pass

# TODO: placeholder, find out if rhp needs that test class
# class TestWeightedHexRing:
#    pass


class TestPolyfillResample:
    pass


class TestLinetrace:
    pass
