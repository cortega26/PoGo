from PoGo_rarity import EnhancedRarityScraper

def test_slugify_handles_regional_forms_and_punctuation():
    scraper = EnhancedRarityScraper()
    assert scraper.slugify_name("Alolan Rattata") == "rattata"
    assert scraper.slugify_name("Galarian Farfetch'd") == "farfetchd"
    assert scraper.slugify_name("Type: Null") == "type-null"
