from django.db import models

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    ton_wallet = models.CharField(max_length=255, null=True, blank=True)
    stars_balance = models.IntegerField(default=0)
    ton_balance = models.FloatField(default=0.0)
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name or self.username} ({self.telegram_id})"

class Gift(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='gifts/', null=True, blank=True)
    display_price = models.IntegerField(help_text="Price displayed in UI (Stars)")
    sell_price = models.IntegerField(help_text="Stars credited when selling")

    def __str__(self):
        return self.name

class Roulette(models.Model):
    name = models.CharField(max_length=255)
    spin_cost = models.IntegerField(help_text="Cost to spin in Stars")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class RouletteGift(models.Model):
    roulette = models.ForeignKey(Roulette, related_name='gifts', on_delete=models.CASCADE)
    gift = models.ForeignKey(Gift, on_delete=models.CASCADE)
    chance = models.FloatField(help_text="Percentage chance (e.g., 10.5)")

    def __str__(self):
        return f"{self.gift.name} in {self.roulette.name} ({self.chance}%)"

class Lottery(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='lotteries/', null=True, blank=True)
    total_tickets = models.IntegerField()
    sold_tickets = models.IntegerField(default=0)
    ticket_cost = models.IntegerField(help_text="Cost per ticket in Stars")
    prize = models.ForeignKey(Gift, on_delete=models.CASCADE)
    is_finished = models.BooleanField(default=False)
    winners_count = models.IntegerField(default=1)

    def __str__(self):
        return self.name

class LotteryTicket(models.Model):
    lottery = models.ForeignKey(Lottery, related_name='tickets', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='lottery_tickets', on_delete=models.CASCADE)
    ticket_number = models.IntegerField()

    def __str__(self):
        return f"Ticket {self.ticket_number} for {self.lottery.name} - {self.user.username}"

class InventoryItem(models.Model):
    STATUS_CHOICES = [
        ('in_inventory', 'In Inventory'),
        ('withdraw_pending', 'Withdraw Pending'),
        ('withdrawn', 'Withdrawn'),
    ]
    user = models.ForeignKey(User, related_name='inventory', on_delete=models.CASCADE)
    gift = models.ForeignKey(Gift, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_inventory')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gift.name} - {self.user.username} ({self.status})"

class Setting(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.key}: {self.value}"
