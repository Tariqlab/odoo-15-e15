# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class MrpEco(models.Model):
    _inherit = 'mrp.eco'

    @api.depends(
        'bom_id.operation_ids',
        'new_bom_id.operation_ids',
        'bom_id.operation_ids.quality_point_ids',
        'new_bom_id.operation_ids.quality_point_ids',
        'bom_id.operation_ids.quality_point_ids.test_type_id',
        'new_bom_id.operation_ids.quality_point_ids.test_type_id',
    )
    def _compute_routing_change_ids(self):
        return super()._compute_routing_change_ids()

    def _prepare_detailed_change_commands(self, new_op, old_op):
        new_points = list(new_op.quality_point_ids) if new_op else []
        old_points = list(old_op.quality_point_ids) if old_op else []
        commands = []
        for _ in range(min(len(new_points), len(old_points))):
            new_point, old_point = new_points.pop(0), old_points.pop(0)
            if new_point.test_type_id != old_point.test_type_id:
                commands += [(0, 0, {
                    'change_type': 'update',
                    'workcenter_id': new_op.workcenter_id.id,
                    'operation_id': new_op.id,
                    'quality_point_id': new_point.id,
                })]
        if new_points:
            for point in new_points:
                commands += [(0, 0, {
                    'change_type': 'add',
                    'workcenter_id': new_op.workcenter_id.id,
                    'operation_id': new_op.id,
                    'quality_point_id': point.id,
                })]
        if old_points:
            for point in old_points:
                commands += [(0, 0, {
                    'change_type': 'remove',
                    'workcenter_id': old_op.workcenter_id.id,
                    'operation_id': old_op.id,
                    'quality_point_id': point.id,
                })]
        return commands


class MrpEcoRoutingChange(models.Model):
    _inherit = 'mrp.eco.routing.change'

    quality_point_id = fields.Many2one('quality.point', 'operation_id')
    step = fields.Char(related='quality_point_id.name', string='Step')
    test_type = fields.Many2one('quality.point.test_type', related='quality_point_id.test_type_id', string='Step Type')
