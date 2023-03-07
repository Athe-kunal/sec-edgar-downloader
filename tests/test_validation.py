import pytest
from sec_edgar_downloader._validation import validate_date_format
from contextlib import ExitStack as does_not_raise


def test_validate_date_format():
    with pytest.raises(TypeError):
        validate_date_format(1234)

    with pytest.raises(ValueError):
        validate_date_format("2021")

    with does_not_raise():
        validate_date_format("2021-01-25")


def test_validate_forms_valid_form():
    pass


def test_validate_dates():
    pass


def test_validate_tiker_or_cik():
    pass
