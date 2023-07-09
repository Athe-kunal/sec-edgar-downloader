from collections import deque
from pathlib import Path
from typing import Any, Dict, List

from ._constants import (
    AMENDS_SUFFIX,
    CIK_LENGTH,
    FILING_FULL_SUBMISSION_FILENAME,
    PRIMARY_DOC_FILENAME_STEM,
    ROOT_SAVE_FOLDER_NAME,
    SUBMISSION_FILE_FORMAT,
    URL_FILING,
    URL_SUBMISSIONS,
)
from ._sec_gateway import (
    download_filing,
    get_list_of_available_filings,
    get_ticker_metadata,
)
from ._types import DownloadMetadata, ToDownload
from ._utils import within_requested_date_range


# TODO: resolve URLs so that images show up in HTML files?
def save_document(
    filing_text: Any,
    download_metadata: DownloadMetadata,
    accession_number: str,
    save_filename: str,
) -> None:
    # Create all parent directories as needed and write content to file
    save_path = (
        download_metadata.download_folder
        / ROOT_SAVE_FOLDER_NAME
        / download_metadata.cik
        / download_metadata.form
        / accession_number
        / save_filename
    )
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(filing_text)


def aggregate_filings_to_download(
    download_metadata: DownloadMetadata, user_agent: str
) -> List[ToDownload]:
    filings_to_download: List[ToDownload] = []
    fetched_count = 0
    filings_available = True
    submissions_uri = URL_SUBMISSIONS.format(
        submission=SUBMISSION_FILE_FORMAT.format(cik=download_metadata.cik)
    )
    additional_submissions = None

    while fetched_count < download_metadata.limit and filings_available:
        resp_json = get_list_of_available_filings(submissions_uri, user_agent)
        # First API response is different from further API responses
        if additional_submissions is None:
            filings_json = resp_json["filings"]["recent"]
            additional_submissions = deque(resp_json["filings"]["files"])
        # On second page or more of API response (for companies with >1000 filings)
        else:
            filings_json = resp_json

        accession_numbers = filings_json["accessionNumber"]
        forms = filings_json["form"]
        documents = filings_json["primaryDocument"]
        filing_dates = filings_json["filingDate"]

        for acc_num, form, doc, f_date in zip(
            accession_numbers, forms, documents, filing_dates, strict=True
        ):
            if (
                form != download_metadata.form
                or (
                    not download_metadata.include_amends
                    and form.endswith(AMENDS_SUFFIX)
                )
                or not within_requested_date_range(download_metadata, f_date)
            ):
                continue

            cik = download_metadata.cik.strip("0")
            acc_num_no_dash = acc_num.replace("-", "")
            raw_filing_uri = URL_FILING.format(
                cik=cik, acc_num_no_dash=acc_num_no_dash, document=f"{acc_num}.txt"
            )
            primary_doc_uri = URL_FILING.format(
                cik=cik, acc_num_no_dash=acc_num_no_dash, document=doc
            )
            primary_doc_suffix = Path(doc).suffix.replace("htm", "html")

            filings_to_download.append(
                ToDownload(
                    raw_filing_uri,
                    primary_doc_uri,
                    acc_num,
                    primary_doc_suffix,
                )
            )

            fetched_count += 1

            # We have reached the requested download limit, so exit early
            if fetched_count == download_metadata.limit:
                return filings_to_download

        if len(additional_submissions) == 0:
            break

        next_page = additional_submissions.popleft()["name"]
        submissions_uri = URL_SUBMISSIONS.format(submission=next_page)

    return filings_to_download


def fetch_and_save_filings(download_metadata: DownloadMetadata, user_agent: str) -> int:
    # TODO: do not download files that already exist
    # TODO: add try/except around failed downloads and continue
    successfully_downloaded = 0
    to_download = aggregate_filings_to_download(download_metadata, user_agent)
    for td in to_download:
        raw_filing = download_filing(td.raw_filing_uri, user_agent)
        save_document(
            raw_filing,
            download_metadata,
            td.accession_number,
            FILING_FULL_SUBMISSION_FILENAME,
        )

        if download_metadata.download_details:
            primary_doc = download_filing(td.primary_doc_uri, user_agent)
            primary_doc_filename = f"{PRIMARY_DOC_FILENAME_STEM}{td.details_doc_suffix}"
            save_document(
                primary_doc,
                download_metadata,
                td.accession_number,
                primary_doc_filename,
            )

        successfully_downloaded += 1

    return successfully_downloaded


def get_ticker_to_cik_mapping(user_agent: str) -> Dict[str, str]:
    ticker_metadata = get_ticker_metadata(user_agent)
    fields = ticker_metadata["fields"]
    ticker_data = ticker_metadata["data"]

    # Find index that corresponds with the CIK and ticker fields
    cik_idx = fields.index("cik")
    ticker_idx = fields.index("ticker")

    return {
        str(td[ticker_idx]).upper(): str(td[cik_idx]).zfill(CIK_LENGTH)
        for td in ticker_data
    }
