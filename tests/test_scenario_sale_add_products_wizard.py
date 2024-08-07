import unittest
from decimal import Decimal

from proteus import Model, Wizard
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import (
    create_payment_term, set_fiscalyear_invoice_sequences)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Imports

        # Create database
        config = activate_modules('sale_add_products_wizard')

        # Create company
        _ = create_company()
        company = get_company()

        # Reload the context
        User = Model.get('res.user')
        Group = Model.get('res.group')
        config._context = User.get_preferences(True, config.context)

        # Create sale user
        sale_user = User()
        sale_user.name = 'Sale'
        sale_user.login = 'sale'
        sale_group, = Group.find([('name', '=', 'Sales')])
        sale_user.groups.append(sale_group)
        sale_user.save()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create parties
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        Product = Model.get('product.product')
        product = Product()
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'goods'
        template.salable = True
        template.list_price = Decimal('10')
        template.cost_price = Decimal('5')
        template.cost_price_method = 'fixed'
        template.account_category = account_category
        template.save()
        product, = template.products
        service = Product()
        template = ProductTemplate()
        template.name = 'service'
        template.default_uom = unit
        template.type = 'service'
        template.salable = True
        template.list_price = Decimal('30')
        template.cost_price = Decimal('10')
        template.cost_price_method = 'fixed'
        template.account_category = account_category
        template.save()
        service, = template.products

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Create a sale selling 2 products
        config.user = sale_user.id
        Sale = Model.get('sale.sale')
        sale_product = Sale()
        sale_product.party = customer
        sale_product.payment_term = payment_term
        sale_product.invoice_method = 'order'
        sale_line = sale_product.lines.new()
        sale_line.product = product
        sale_line.quantity = 2.0
        sale_product.save()

        # Create a sale selling 1 service
        sale_service = Sale()
        sale_service.party = customer
        sale_service.payment_term = payment_term
        sale_service.invoice_method = 'order'
        sale_line = sale_service.lines.new()
        sale_line.product = service
        sale_line.quantity = 1.0
        sale_service.save()

        # Confirm product sale
        Sale.quote([sale_product.id], config.context)
        self.assertEqual(sale_product.state, 'quotation')

        # Add product and service products to both sales
        add_products = Wizard('sale.add_products', [sale_product, sale_service])
        add_products.form.products.append(Product(product.id))
        add_products.form.products.append(Product(service.id))
        add_products.execute('add_products')

        # Check draft sale has two new lines
        sale_service = Sale(sale_service.id)
        self.assertEqual(len(sale_service.lines), 3)
        self.assertEqual(sale_service.lines[1].product.template.name, 'product')
        self.assertEqual(sale_service.lines[1].quantity, 0.0)
        self.assertEqual(sale_service.lines[2].product.template.name, 'service')
        self.assertEqual(sale_service.lines[2].quantity, 0.0)

        # Check quoted sale has not been changed
        sale_product.reload()
        self.assertEqual(len(sale_product.lines), 1)
        self.assertEqual(sale_product.lines[0].product.template.name, 'product')
        self.assertEqual(sale_product.lines[0].quantity, 2.0)
