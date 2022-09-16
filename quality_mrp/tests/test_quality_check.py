# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import Form

from .test_common import TestQualityMrpCommon

class TestQualityCheck(TestQualityMrpCommon):

    def test_00_production_quality_check(self):

        """Test quality check on production order."""

        # Create Quality Point for product Laptop Customized with Manufacturing Operation Type.
        self.qality_point_test1 = self.env['quality.point'].create({
            'product_ids': [(4, self.product_id)],
            'picking_type_ids': [(4, self.picking_type_id)],
        })

        # Check that quality point created.
        assert self.qality_point_test1, "First Quality Point not created for Laptop Customized."

        # Create Production Order of Laptop Customized to produce 5.0 Unit.
        production_form = Form(self.env['mrp.production'])
        production_form.product_id = self.env['product.product'].browse(self.product_id)
        production_form.product_qty = 5.0
        self.mrp_production_qc_test1 = production_form.save()

        # Check that Production Order of Laptop Customized to produce 5.0 Unit is created.
        assert self.mrp_production_qc_test1, "Production Order not created."

        # Perform check availability and produce product.
        self.mrp_production_qc_test1.action_confirm()
        self.mrp_production_qc_test1.action_assign()

        mo_form = Form(self.mrp_production_qc_test1)
        mo_form.qty_producing = self.mrp_production_qc_test1.product_qty
        mo_form.lot_producing_id = self.lot_product_27_0
        details_operation_form = Form(self.mrp_production_qc_test1.move_raw_ids[0], view=self.env.ref('stock.view_stock_move_operations'))
        with details_operation_form.move_line_ids.new() as ml:
            ml.qty_done = self.mrp_production_qc_test1.product_qty
        details_operation_form.save()

        self.mrp_production_qc_test1 = mo_form.save()
        # Check Quality Check for Production is created and check it's state is 'none'.
        self.assertEqual(len(self.mrp_production_qc_test1.check_ids), 1)
        self.assertEqual(self.mrp_production_qc_test1.check_ids.quality_state, 'none')

        # 'Pass' Quality Checks of production order.
        self.mrp_production_qc_test1.check_ids.do_pass()

        # Set MO Done.
        self.mrp_production_qc_test1.button_mark_done()

        # Now check state of quality check.
        self.assertEqual(self.mrp_production_qc_test1.check_ids.quality_state, 'pass')

    def test_01_production_quality_check_product(self):
        """ Test quality check on production order with type product for tracked and non-tracked manufactured product
        """

        product_without_tracking = self.env['product.product'].create({
            'name': 'Product not tracked',
            'type': 'product',
            'tracking': 'none',
        })

        # Create Quality Point for product Drawer with Manufacturing Operation Type.
        self.env['quality.point'].create({
            'product_ids': [self.product_id],
            'picking_type_ids': [self.picking_type_id],
            'measure_on': 'product',
            'is_lot_tested_fractionally': True,
            'testing_percentage_within_lot': 50,
        })
        # Create Quality Point for component Drawer Case Black with Manufacturing Operation Type.
        self.env['quality.point'].create({
            'product_ids': [self.product.bom_ids.bom_line_ids[0].product_id.id],
            'picking_type_ids': [self.picking_type_id],
            'measure_on': 'product',
        })
        # Create Quality Point for all products with Manufacturing Operation Type.
        # This should apply for all products but not to the components of a MO
        self.env['quality.point'].create({
            'picking_type_ids': [self.picking_type_id],
            'measure_on': 'product',
        })

        # Create Production Order of Drawer to produce 5.0 Unit.
        production_form = Form(self.env['mrp.production'])
        production_form.product_id = self.product
        production_form.product_qty = 5.0
        production = production_form.save()
        production.action_confirm()
        production.qty_producing = 4.0
        production.action_generate_serial()

        # Check that the Quality Check were created and has correct values
        self.assertEqual(len(production.move_raw_ids[0].move_line_ids.check_ids), 1)
        self.assertEqual(len(production.check_ids), 3)
        self.assertEqual(production.move_finished_ids.move_line_ids.check_ids[0].qty_to_test, 2)

        # Create Production Order of non-tracked product
        production2_form = Form(self.env['mrp.production'])
        production2_form.product_id = product_without_tracking
        production2 = production2_form.save()
        production2.action_confirm()
        production2.qty_producing = 1.0

        # Check that the Quality Check was created
        self.assertEqual(len(production2.check_ids), 1)
