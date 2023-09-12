"""Test the Date class methods."""
import ee
import pytest

import geetools


class TestToDatetime:
    """Test the toDatetime method."""

    def test_to_datetime(self, date_instance):
        datetime = date_instance.geetools.toDatetime()
        assert datetime.year == 2020
        assert datetime.month == 1
        assert datetime.day == 1

    def test_deprecated_method(self, date_instance):
        with pytest.deprecated_call():
            datetime = geetools.tools.date.toDatetime(date_instance)
            assert datetime.year == 2020
            assert datetime.month == 1
            assert datetime.day == 1

    @pytest.fixture
    def date_instance(self):
        """Return a defined date instance."""
        return ee.Date("2020-01-01")


class TestGetUnitSinceEpoch:
    """Test the getUnitSinceEpoch method."""

    def test_unit_since_epoch(self, date_instance):
        unit = date_instance.geetools.getUnitSinceEpoch("year")
        assert unit.getInfo() >= 49  # 2020 - 1970

    def test_wrong_unit(self, date_instance):
        with pytest.raises(ValueError):
            date_instance.geetools.getUnitSinceEpoch("foo")

    def test_deprecated_method(self, date_instance):
        with pytest.deprecated_call():
            unit = geetools.tools.date.unitSinceEpoch(date_instance, "year")
            assert unit.getInfo() >= 49

    @pytest.fixture
    def date_instance(self):
        """Return a defined date instance."""
        return ee.Date("2020-01-01")


class TestFromEpoch:
    """Test the fromEpoch method."""

    def test_from_epoch(self):
        date = ee.Date.geetools.fromEpoch(49, "year")
        assert date.format("YYYY-MM-DD").getInfo() == "2019-01-01"

    def test_wrong_unit(self):
        with pytest.raises(ValueError):
            ee.Date.geetools.fromEpoch(49, "foo")

    def test_deprecated_method(self):
        with pytest.deprecated_call():
            date = geetools.tools.date.dateSinceEpoch(49, "year")
            assert date.format("YYYY-MM-DD").getInfo() == "2019-01-01"
