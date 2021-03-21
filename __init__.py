# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import sale


def register():
    Pool.register(
        sale.AddProductsSelectProducts,
        module='sale_add_products_wizard', type_='model')
    Pool.register(
        sale.AddProducts,
        module='sale_add_products_wizard', type_='wizard')
