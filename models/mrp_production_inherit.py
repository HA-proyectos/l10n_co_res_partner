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


class MrpProductionInherit(models.Model):

	_inherit = 'mrp.production'



	@api.model
	def _get_default_user_id(self):
		return self.env['res.users'].browse(self.env.uid)

	check_po= fields.Boolean(string="Generar Request", default=False)
	
	user_id = fields.Many2one('res.users', 'Proveedor', track_visibility='onchange', default=_get_default_user_id)

	warehouse_quantity = fields.Char(compute='_get_warehouse_quantity', string='Quantity per warehouse')


	def _get_warehouse_quantity(self):
		for record in self:
			warehouse_quantity_text = ''
			product_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', record.id)])
			if product_id:
				quant_ids = self.env['stock.quant'].sudo().search([('product_id','=',product_id[0].id),('location_id.usage','=','internal')])
				t_warehouses = {}
				for quant in quant_ids:
					if quant.location_id:
						if quant.location_id not in t_warehouses:
							t_warehouses.update({quant.location_id:0})
						t_warehouses[quant.location_id] += quant.qty

				tt_warehouses = {}
				for location in t_warehouses:
					warehouse = False
					location1 = location
					while (not warehouse and location1):
						warehouse_id = self.env['stock.warehouse'].sudo().search([('lot_stock_id','=',location1.id)])
						if len(warehouse_id) > 0:
							warehouse = True
						else:
							warehouse = False
						location1 = location1.location_id
					if warehouse_id:
						if warehouse_id.name not in tt_warehouses:
							tt_warehouses.update({warehouse_id.name:0})
						tt_warehouses[warehouse_id.name] += t_warehouses[location]

				for item in tt_warehouses:
					if tt_warehouses[item] != 0:
						warehouse_quantity_text = warehouse_quantity_text + ' ** ' + item + ': ' + str(tt_warehouses[item])
				record.warehouse_quantity = warehouse_quantity_text

	def return_product_request(self, data_product):
		date_current= fields.Datetime.now()
		product_ids=[]
		vals={}
		company_id = self.env.context.get('company_id') or \
		self.env.user.company_id.id
		mrp_bom_model= self.env['mrp.bom']
		mrp_bom_id= mrp_bom_model.search([('product_tmpl_id', 'in', data_product), ('list_main', '=', True)])

		if mrp_bom_id:

			mrp_bom_line_model= self.env['mrp.bom.line']
			data_mrp= []
			for x in mrp_bom_id:
				data_mrp.append(x.id)

			mrp_bom_line_id= mrp_bom_line_model.search([('bom_id', 'in', data_mrp)])

			for x in mrp_bom_line_id:

				product_list = mrp_bom_model.search([('product_tmpl_id', '=', x.product_id.product_tmpl_id.id), ('list_main', '=', True)])
				
				if product_list:
					product_list_line= mrp_bom_line_model.search([('bom_id', '=', product_list.id)])

					for record in product_list_line:
						name = record.product_id.name
						if record.product_id.code:
							name = '[%s] %s' % (name, record.product_id.code)
						if record.product_id.description_purchase:
							name += '\n' + record.product_id.description_purchase

						vals={'company_id': company_id,
						'product_id': x.product_id.id,
						'name': name, 
						'product_qty_actual': x.product_id.qty_available,
						'product_qty_sent': x.product_id.virtual_available,
						'product_uom_id':x.product_id.uom_id.id,
						'date_required': date_current,
						'product_qty':0,

						}
						product_ids.append((0,_, vals))
									
				else:
					name = x.product_id.name
					if x.product_id.code:
						name = '[%s] %s' % (name, x.product_id.code)
					if x.product_id.description_purchase:
						name += '\n' + x.product_id.description_purchase
									
					vals={'company_id': company_id,
						'product_id': x.product_id.id,
						'name': name, 
						'product_qty_actual': x.product_id.qty_available,
						'product_qty_sent': x.product_id.virtual_available,
						'product_uom_id':x.product_id.uom_id.id,
						'date_required': date_current,
						'product_qty':0,

						}

	

					product_ids.append((0,_, vals))

		else:
			_logger.info('sdfsdfdsfdsfdsfdsfdsfsd')
			for x in self.move_raw_ids:
				name = x.product_id.name
				if x.product_id.code:
					name = '[%s] %s' % (name, x.product_id.code)
				if x.product_id.description_purchase:
					name += '\n' + x.product_id.description_purchase
								
				vals={'company_id': company_id,
					'product_id': x.product_id.id,
					'name': name, 
					'product_qty_actual': x.product_id.qty_available,
					'product_qty_sent': x.product_id.virtual_available,
					'product_uom_id':x.product_id.uom_id.id,
					'date_required': date_current,
					'product_qty':0,

					}
				product_ids.append((0,_, vals))			

		return product_ids


	def generate_purchase_request(self):

		data_product=[]
		date_current= fields.Datetime.now()

		currency_id= self.env['res.currency'].search([('name', '=', 'COP')])
		if self.move_raw_ids:
			if self.user_id:
				product_ids_request= []
				for x in self.move_raw_ids:
					if x.quantity_available < x.product_uom_qty:					
						product_ids_request.append(x.product_id.id)
				
				data_product = self.return_product_request(product_ids_request)

				if data_product:
					vals={  'name': self.env['ir.sequence'].next_by_code('purchase.request'),
							'requested_by': self.user_id.id,
							'picking_type_id': self._get_picking_type().id,
							'line_ids': data_product,
							'sale_mrp_id': self.sale_mrp_id.id,
							'mrp_id': self.id
						}
					res= self.env['purchase.request'].create(vals)

					return {
						'name': _('Purchase Request'),
						'res_model':'purchase.request',
						'type':'ir.actions.act_window',
						'view_type':'form',
						'view_mode':'form',
						'target':'new',
						'res_id': res.id,
						'nodestroy': True,
						'domain': [('id', '=', res.id)]
					}

			else:

				raise UserError(_("Debe seleccionar un proveedor para poder generar una Orden de Compra"))

	@api.model
	def _get_picking_type(self):
		type_obj = self.env['stock.picking.type']
		company_id = self.env.context.get('company_id') or \
			self.env.user.company_id.id
		types = type_obj.search([('code', '=', 'incoming'),
								 ('warehouse_id.company_id', '=', company_id)])
		if not types:
			types = type_obj.search([('code', '=', 'incoming'),
									 ('warehouse_id', '=', False)])
		_logger.info(types)
		_logger.info(types[:1])
		return types[:1]


