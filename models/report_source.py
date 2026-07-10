# -*- coding: utf-8 -*-
from odoo import fields, models


class KaiSightReportSource(models.Model):
    _name = "kai.view.report.source"
    _description = "kaiSight Exportable Data Source"
    _order = "sequence, name, id"

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    icon = fields.Char(default="fa-table", help="Font Awesome icon class, e.g. fa-users")
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
    )
    model_name = fields.Char(related="model_id.model", store=True, readonly=True)
    group_ids = fields.Many2many(
        "res.groups",
        string="Allowed groups",
        help="Leave empty to allow all kaiSight users who can read the model.",
    )
    default_field_ids = fields.Many2many(
        "ir.model.fields",
        string="Recommended columns",
        domain="[('model_id', '=', model_id)]",
        help="Pre-selected when opening this data source in the report builder.",
    )
