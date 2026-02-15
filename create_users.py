from django.contrib.auth.models import Group, User


def run():
    leaders_group, _ = Group.objects.get_or_create(name="leaders")
    admins_group, _ = Group.objects.get_or_create(name="exhibition_admins")

    # نمونه لیدر
    leader1, created = User.objects.get_or_create(username="leader1")
    if created:
        leader1.set_password("test1234")
        leader1.save()
    leader1.groups.add(leaders_group)

    # نمونه ادمین
    admin1, created = User.objects.get_or_create(username="admin1")
    if created:
        admin1.set_password("test1234")
        admin1.is_staff = True
        admin1.save()
    admin1.groups.add(admins_group)