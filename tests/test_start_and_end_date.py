"""Tests after_date and before_date download bounds."""

from datetime import datetime, timedelta

from sec_edgar_downloader._constants import DATE_FORMAT_TOKENS


def test_date_bounds(downloader):
    filing_type = "8-K"
    cik = "0000320193"
    start_date = datetime(2017, 9, 12)
    end_date = datetime(2019, 11, 15)
    include_amends = False

    # filings available on start_date and end_date
    filings_to_download = downloader.get(
        forms=filing_type,
        ticker_or_cik=cik,
        start_date=start_date.strftime(DATE_FORMAT_TOKENS),
        end_date=end_date.strftime(DATE_FORMAT_TOKENS),
        include_amends=include_amends,
        only_dataframe=True,
    )
    assert len(filings_to_download) == 20

    start_date += timedelta(days=1)
    filings_to_download = downloader.get(
        forms=filing_type,
        ticker_or_cik=cik,
        start_date=start_date.strftime(DATE_FORMAT_TOKENS),
        end_date=end_date.strftime(DATE_FORMAT_TOKENS),
        include_amends=include_amends,
        only_dataframe=True,
    )
    assert len(filings_to_download) == 19

    end_date -= timedelta(days=1)
    filings_to_download = downloader.get(
        forms=filing_type,
        ticker_or_cik=cik,
        start_date=start_date.strftime(DATE_FORMAT_TOKENS),
        end_date=end_date.strftime(DATE_FORMAT_TOKENS),
        include_amends=include_amends,
        only_dataframe=True,
    )
    assert len(filings_to_download) == 18

    # num_filings_to_download < number of filings available
    num_filings_to_download = 5
    filings_to_download = downloader.get(
        forms=filing_type,
        ticker_or_cik=cik,
        amount=num_filings_to_download,
        start_date=start_date.strftime(DATE_FORMAT_TOKENS),
        end_date=end_date.strftime(DATE_FORMAT_TOKENS),
        include_amends=include_amends,
        only_dataframe=True,
    )
    assert len(filings_to_download) == 5
