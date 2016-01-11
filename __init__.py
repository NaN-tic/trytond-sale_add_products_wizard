# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .sale import *


def register():
    Pool.register(
        AddProductsSelectProducts,
        module='sale_add_products_wizard', type_='model')
    Pool.register(
        AddProducts,
        module='sale_add_products_wizard', type_='wizard')
