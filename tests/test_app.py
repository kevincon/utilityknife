import pytest

def test_index(selenium, base_url):
    selenium.get(base_url)
    assert 'Utility Knife' == selenium.title
