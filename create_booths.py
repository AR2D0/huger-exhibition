from exhibition.models import Booth

def run():
    booths = [
        ("فیزیک", "physics", 3),
        ("موسیقی", "music", 6),
        ("رایانه", "computer", 4),
        ("شیمی", "chemistry", 2),
        ("زیست‌شناسی", "biology", 3),
        ("نجوم", "astronomy", 2),
        ("هوافضا", "aerospace", 2),
        ("ریاضی", "math", 3),
    ]

    for name, slug, max_groups in booths:
        Booth.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "max_groups": max_groups},
        )