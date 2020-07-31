from paper_uploads import utils


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
    assert utils.parse_filesize('8k') == 8 * 1024
    assert utils.parse_filesize('26.5kb') == 26.5 * 1024
    assert utils.parse_filesize('32 mB') == 32 * 1024 * 1024
    assert utils.parse_filesize('9M') == 9 * 1024 * 1024
    assert utils.parse_filesize('2.25 GB') == 2.25 * 1024 * 1024 * 1024
