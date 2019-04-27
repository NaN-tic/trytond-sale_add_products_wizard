=================================
Sale Add Products Wizard Scenario
=================================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()

Create database::

    >>> config = activate_modules('sale_add_products_wizard')


Create company::

    >>> _ = create_company()
    >>> company = get_company()
    >>> party = company.party

Reload the context::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> config._context = User.get_preferences(True, config.context)

Create sale user::

    >>> sale_user = User()
    >>> sale_user.name = 'Sale'
    >>> sale_user.login = 'sale'
    >>> sale_user.main_company = company
    >>> sale_group, = Group.find([('name', '=', 'Sales')])
    >>> sale_user.groups.append(sale_group)
    >>> sale_user.save()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> receivable = accounts['receivable']
    >>> payable = accounts['payable']
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']
    >>> account_tax = accounts['tax']
    >>> account_cash = accounts['cash']

Create journals::

    >>> Journal = Model.get('account.journal')
    >>> cash_journal, = Journal.find([('type', '=', 'cash')])
    >>> cash_journal.credit_account = account_cash
    >>> cash_journal.debit_account = account_cash
    >>> cash_journal.save()

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> template.cost_price = Decimal('5')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> product.template = template
    >>> product.save()

    >>> service = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'service'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.salable = True
    >>> template.list_price = Decimal('30')
    >>> template.cost_price = Decimal('10')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> service.template = template
    >>> service.save()

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Create a sale selling 2 products::

    >>> config.user = sale_user.id
    >>> Sale = Model.get('sale.sale')
    >>> sale_product = Sale()
    >>> sale_product.party = customer
    >>> sale_product.payment_term = payment_term
    >>> sale_product.invoice_method = 'order'
    >>> sale_line = sale_product.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 2.0
    >>> sale_product.save()

Create a sale selling 1 service::

    >>> sale_service = Sale()
    >>> sale_service.party = customer
    >>> sale_service.payment_term = payment_term
    >>> sale_service.invoice_method = 'order'
    >>> sale_line = sale_service.lines.new()
    >>> sale_line.product = service
    >>> sale_line.quantity = 1.0
    >>> sale_service.save()

Confirm product sale::

    >>> Sale.quote([sale_product.id], config.context)
    >>> sale_product.state
    'quotation'

Add product and service products to both sales::

    >>> add_products = Wizard('sale.add_products',
    ...     [sale_product, sale_service])
    >>> add_products.form.products.append(product)
    >>> add_products.form.products.append(service)
    >>> add_products.execute('add_products')

Check draft sale has two new lines::

    >>> sale_service = Sale(sale_service.id)
    >>> len(sale_service.lines)
    3
    >>> sale_service.lines[1].product.template.name
    'product'
    >>> sale_service.lines[1].quantity
    0.0
    >>> sale_service.lines[2].product.template.name
    'service'
    >>> sale_service.lines[2].quantity
    0.0

Check quoted sale has not been changed::

    >>> sale_product.reload()
    >>> len(sale_product.lines)
    1
    >>> sale_product.lines[0].product.template.name
    'product'
    >>> sale_product.lines[0].quantity
    2.0
