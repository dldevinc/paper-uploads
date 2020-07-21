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
