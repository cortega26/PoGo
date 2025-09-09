from pogorarity.helpers import slugify_name


def test_slugify_handles_regional_forms_and_punctuation():
    assert slugify_name("Alolan Rattata") == "rattata"
    assert slugify_name("Galarian Farfetch'd") == "farfetchd"
    assert slugify_name("Type: Null") == "type-null"
