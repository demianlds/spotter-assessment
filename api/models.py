from django.db import models


class FuelStation(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    lat = models.FloatField()
    lon = models.FloatField()
    price_per_gallon = models.FloatField()

    class Meta:
        indexes = [
            models.Index(fields=["lat", "lon"]),
        ]

    def __str__(self):
        return f"{self.name} — {self.city}, {self.state} (${self.price_per_gallon:.3f})"
