# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) Brayhan Jaramillo.
#               brayhanjaramillo@hotmail.com


from odoo import api, fields, models, _
import time
from datetime import datetime, timedelta, date
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, AccessError, ValidationError


class SaleMrpProductionInherit(models.Model):

	_inherit = 'sale.mrp.production'


	@api.onchange('product_id')
	def onchange_product(self):
		_logger.info('entramos')
		_logger.info(self.product_id.id)
		_logger.info(self.product_id.product_tmpl_id.id)
		if self.product_id:
			mrp_bom_model= self.env['mrp.bom']
			mrp_bom_id= mrp_bom_model.search([('product_tmpl_id', '=', self.product_id.product_tmpl_id.id), ('list_main', '=', True)])

			_logger.info(mrp_bom_id)
			if mrp_bom_id:

				self.boom_tmp_id= mrp_bom_id.id
				self.bom_id= mrp_bom_id.id
			else:
				raise UserError(_("Verifique que el campo Lista de Materiales Principal, este selecionado en la lista de materiales del producto seleccionado"))




SaleMrpProductionInherit()