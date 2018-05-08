import pytest

@pytest.fixture
def chrome_options(chrome_options):
    # See https://docs.travis-ci.com/user/chrome#Sandboxing
    chrome_options.add_argument('--no-sandbox')
    return chrome_options

def test_index(selenium, base_url):
    selenium.get(base_url)
    assert 'Utility Knife' == selenium.title
