import time

from sec_edgar_downloader._constants import MAX_REQUESTS_PER_SECOND


def test_rate_limiting(downloader):
    # Apple has a lot of form 4
    forms = ["4"]
    cik = "0000320193"
    amount = 200

    start_time = time.time()
    downloader.get(
        forms=forms,
        ticker_or_cik=cik,
        amount=amount,
        download_details=False
    )
    end_time = time.time()
    download_time = end_time - start_time

    # Download time should be greater than the amount of filings
    # divided by the max number of requests per second allowed
    # by the SEC. The exact number of requests made to the SEC
    # is a bit larger than the filings amount due to a few API
    # calls to the submissions endpoint, but if rate limiting
    # is working this assertion should be obvious.
    min_time_with_rate_limiting = amount / MAX_REQUESTS_PER_SECOND

    assert download_time > min_time_with_rate_limiting
