from django.core.files import File

from paper_uploads import utils

from .dummy import *


def test_checksum():
    with open(NATURE_FILEPATH, 'rb') as fp:
        assert utils.checksum(fp) == 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'


def test_checksum_on_closed_file():
    fp = File(None, CALLIPHORA_FILEPATH)
    assert utils.checksum(fp) == 'd4dec03fae591f0c89776c57f8b5d721c930f5f7cb1b32d456f008700a432386'
    fp.close()


def test_remove_dulpicates():
    assert utils.remove_dulpicates(
        ['apple', 'banana', 'apple', 'apple', 'banana', 'orange', 'banana']
    ) == ('apple', 'banana', 'orange')


def test_lowercased_dict_keys():
    assert utils.lowercased_dict_keys({'Fruit': 'banana', 'color': 'Red'}) == {
        'fruit': 'banana',
        'color': 'Red',
    }


def test_parse_filesize():
    assert utils.parse_filesize('45') == 45
    assert utils.parse_filesize('8k') == 8 * 1000
    assert utils.parse_filesize('26.5kb') == 26.5 * 1000
    assert utils.parse_filesize('32 mB') == 32 * 1000 * 1000
    assert utils.parse_filesize('9M') == 9 * 1000 * 1000
    assert utils.parse_filesize('2.25 GB') == 2.25 * 1000 * 1000 * 1000


def test_filesizeformat():
    assert utils.filesizeformat(45) == '45\xa0bytes'
    assert utils.filesizeformat(8 * 1024) == '8.2\xa0KB'
    assert utils.filesizeformat(26.5 * 1000) == '26.5\xa0KB'
    assert utils.filesizeformat(32 * 1024 * 1024) == '33.6\xa0MB'
    assert utils.filesizeformat(9 * 1000 * 1000) == '9.0\xa0MB'
    assert utils.filesizeformat(2.25 * 1000 * 1000 * 1000) == '2.2\xa0GB'
