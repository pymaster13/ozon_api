from django.db import models
from datetime import datetime

class Product(models.Model):
    id_product = models.CharField(max_length = 16, blank = True, null = True, verbose_name='ID')
    available = models.BooleanField(default = False , blank = True, null = True, verbose_name='Доступен') # new_price >= zacup
    new_price = models.FloatField(blank = True, null = True, verbose_name='Новая минимальная цена') # новая цена, рассчитанная по формуле
    note = models.CharField(max_length = 256, blank = True, null = True, verbose_name='Примечание')
    refresh_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата и время последнего обновления')

    def save(self, *args, **kwargs):
        self.refresh_date = datetime.now()
        super(Product, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return 'id: {}, available: {}, new_price: {}, note: {}'.format(self.id_product, self.available, self.new_price, self.note)

