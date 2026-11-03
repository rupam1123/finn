import pytest
from finn.documents import document_url


def test_reviewed_suzlon_issuer_pdf_host():
    # Official investor financial reports origin, reviewed 1 November 2026.
    url = 'https://www.suzlon.com/pdf/investor/financial-reports-presentations/2026-27/report.pdf'
    assert document_url(url) == url


@pytest.mark.parametrize('url', [
    'http://www.suzlon.com/report.pdf',
    'https://www.suzlon.com.evil.example/report.pdf',
    'https://suzlon.com.evil.example/report.pdf',
    'https://www.suzlon.com@127.0.0.1/report.pdf',
    'https://www.suzlon.com:8443/report.pdf',
    'https://127.0.0.1/report.pdf',
    'https://169.254.169.254/report.pdf',
])
def test_issuer_addition_preserves_url_restrictions(url):
    with pytest.raises(ValueError):
        document_url(url)
