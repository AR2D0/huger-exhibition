from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Booth(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    max_groups = models.PositiveIntegerField()
    current_visitors = models.PositiveIntegerField(default=0, verbose_name="تعداد بازدیدکنندگان فعلی")

    class Meta:
        verbose_name = "Booth"
        verbose_name_plural = "Booths"

    def __str__(self) -> str:
        return self.name


class BoothVisit(models.Model):
    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name="visits")
    leader = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="booth_visits"
    )
    entered_at = models.DateTimeField(auto_now_add=True)
    exited_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Booth Visit"
        verbose_name_plural = "Booth Visits"
        constraints = [
            models.UniqueConstraint(
                fields=["booth", "leader"],
                condition=models.Q(is_active=True),
                name="unique_active_visit_per_booth_leader",
            )
        ]

    def __str__(self) -> str:
        return f"{self.leader.username} @ {self.booth.name}"

# exhibition/models.py
class LeaderBoothStatus(models.Model):
    leader = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'groups__name': 'leaders'})
    booth = models.ForeignKey(Booth, on_delete=models.CASCADE)
    is_checked = models.BooleanField(default=False)
    checked_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        unique_together = ('leader', 'booth')  # هر لیدر فقط یک وضعیت برای هر غرفه داشته باشه
        verbose_name = "Leader Booth Status"
        verbose_name_plural = "Leader Booth Statuses"
        
