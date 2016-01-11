# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateTransition, Button

__all__ = ['AddProductsSelectProducts', 'AddProducts']


class AddProductsSelectProducts(ModelView):
    'Add Products to Sale: Select products'
    __name__ = 'sale.add_products.select_products'
    selected_sales = fields.Integer('Selected Sales', readonly=True)
    ignored_sales = fields.Integer('Ignored Sales', readonly=True, states={
            'invisible': Eval('ignored_sales', 0) == 0,
            },
        help="The sales that won't be changed because they are not in a state "
        "that allows it.")
    products = fields.Many2Many('product.product', None, None, 'Products',
        states={
            'readonly': Eval('selected_sales', 0) == 0,
            }, depends=['selected_sales'])

    @classmethod
    def __setup__(cls):
        pool = Pool()
        SaleLine = pool.get('sale.line')
        super(AddProductsSelectProducts, cls).__setup__()
        cls.products.domain = SaleLine.product.domain


class AddProducts(Wizard):
    'Add Products to Sale'
    __name__ = 'sale.add_products'
    start_state = 'select_products'
    select_products = StateView('sale.add_products.select_products',
        'sale_add_products_wizard.add_products_select_products_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Add', 'add_products', 'tryton-ok', default=True),
            ])
    add_products = StateTransition()

    @classmethod
    def __setup__(cls):
        super(AddProducts, cls).__setup__()
        cls._allowed_sale_states = {'draft'}

    def default_select_products(self, fields):
        Sale = Pool().get('sale.sale')

        active_ids = Transaction().context['active_ids']
        selected_sales = Sale.search([
                ('id', 'in', active_ids),
                ('state', 'in', self._allowed_sale_states),
                ], count=True)
        return {
            'selected_sales': selected_sales,
            'ignored_sales': len(active_ids) - selected_sales,
            }

    def transition_add_products(self):
        pool = Pool()
        Sale = pool.get('sale.sale')
        SaleLine = pool.get('sale.line')

        products = self.select_products.products
        if not products:
            return 'end'

        sales = Sale.search([
                ('id', 'in', Transaction().context['active_ids']),
                ('state', 'in', self._allowed_sale_states),
                ])
        if not sales:
            return 'end'

        # It creates lines despite of write sales to don't generate a
        # concurrent edition exception if an user is editing the same sale
        to_create = []
        for sale in sales:
            for product in products:
                line = SaleLine()
                line.sale = sale
                line.type = 'line'
                line.product = product
                line.quantity = 0
                for fname in SaleLine.product.on_change:
                    if (not fname.startswith('_parent_sale')
                            and fname not in ('product', 'quantity')):
                        default_fname = getattr(SaleLine, 'default_%s' % fname,
                            None)
                        if default_fname:
                            setattr(line, fname, default_fname())
                        else:
                            setattr(line, fname, None)

                line_vals = line._save_values
                line_vals.update(line.on_change_product())
                for fname in line_vals.keys():
                    if fname.endswith('.rec_name'):
                        del line_vals[fname]
                        continue
                    if (isinstance(getattr(SaleLine, fname), fields.Many2Many)
                            and line_vals[fname]):
                        line_vals[fname] = [('add', line_vals[fname])]
                to_create.append(line_vals)
        if to_create:
            SaleLine.create(to_create)
        return 'end'
