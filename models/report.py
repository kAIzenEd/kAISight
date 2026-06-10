# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .action_utils import prepare_act_window_action

_LIST_SKIP_TYPES = frozenset({"one2many", "many2many", "binary", "html", "reference"})


class kaiSightReport(models.Model):
    _name = "kai.view.report"
    _description = "kaiSight Saved Report"
    _inherit = ["kai.view.domain.mixin"]
    _order = "sequence, name, id"

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
    )
    model_name = fields.Char(related="model_id.model", store=True, readonly=True)
    res_model_name = fields.Char(
        related="model_id.model",
        string="Target model",
        readonly=True,
    )
    field_ids = fields.Many2many(
        "ir.model.fields",
        "kai_view_report_field_rel",
        "report_id",
        "field_id",
        string="Columns",
        domain="[('model_id', '=', model_id)]",
        help="Fields shown in the list view when opening this report.",
    )
    list_view_id = fields.Many2one(
        "ir.ui.view",
        string="List view",
        copy=False,
        ondelete="set null",
        readonly=True,
    )
    domain = fields.Char(default="[]")
    context = fields.Char(
        default="{}",
        help="Extra context passed to the action (JSON object).",
    )
    view_mode = fields.Char(
        default="list,form",
        help="Comma-separated view types, e.g. list,form,kanban",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Owner",
        default=lambda self: self.env.user,
        index=True,
    )
    is_shared = fields.Boolean(string="Shared with all users")
    is_favorite = fields.Boolean(string="Favorite")

    @api.onchange("model_id")
    def _onchange_model_id(self):
        self.field_ids = False
        self.domain = "[]"

    @api.model_create_multi
    def create(self, vals_list):
        reports = super().create(vals_list)
        reports._sync_list_view()
        return reports

    def write(self, vals):
        res = super().write(vals)
        if {"field_ids", "model_id", "name"} & set(vals):
            self._sync_list_view()
        return res

    def _check_report_access(self, mode="read"):
        self.ensure_one()
        if self.env.su:
            return
        if self.env.user.has_group("kaiSight.group_kai_view_manager"):
            return
        if mode == "read" and self.is_shared:
            return
        if self.user_id == self.env.user:
            return
        raise AccessError(_("You do not have access to this report."))

    @api.constrains("domain", "model_id")
    def _check_domain(self):
        for report in self.filtered("model_id"):
            try:
                report.validate_target_domain(report.model_name, report.domain)
            except ValidationError as exc:
                raise ValidationError(
                    _("Report “%(name)s”: %(error)s")
                    % {"name": report.name, "error": exc.args[0]}
                ) from exc

    def _parse_domain(self):
        self.ensure_one()
        try:
            return self._parse_domain_string(self.domain, _("Filter"))
        except ValidationError as exc:
            raise UserError(_("Invalid domain: %s") % exc.args[0]) from exc

    def _parse_context(self):
        self.ensure_one()
        import ast

        ctx_str = (self.context or "{}").strip()
        if not ctx_str:
            return {}
        try:
            ctx = ast.literal_eval(ctx_str)
        except (SyntaxError, ValueError) as exc:
            raise UserError(_("Invalid context: %s") % exc) from exc
        if not isinstance(ctx, dict):
            raise UserError(_("Context must evaluate to a dict."))
        return ctx

    def _get_list_field_names(self):
        self.ensure_one()
        names = []
        model = self.env[self.model_name] if self.model_name in self.env else None
        for field in self.field_ids.sorted("name"):
            if field.ttype in _LIST_SKIP_TYPES:
                continue
            if model and field.name not in model._fields:
                continue
            names.append(field.name)
        return names

    def _build_list_arch(self):
        self.ensure_one()
        field_names = self._get_list_field_names()
        if not field_names:
            field_names = ["name"] if "name" in self.env[self.model_name]._fields else []
        if not field_names:
            raise UserError(
                _("Select at least one column, or pick a model with a “name” field.")
            )
        parts = ["<list>"]
        for fname in field_names:
            parts.append('<field name="%s"/>' % fname)
        parts.append("</list>")
        return "".join(parts)

    def _sync_list_view(self):
        for report in self.filtered("model_id"):
            if not report.field_ids:
                if report.list_view_id:
                    report.list_view_id.unlink()
                    report.list_view_id = False
                continue
            arch = report._build_list_arch()
            if report.list_view_id:
                report.list_view_id.write({"arch": arch, "model": report.model_name})
            else:
                view = self.env["ir.ui.view"].sudo().create(
                    {
                        "name": "kaiSight report %s" % report.id,
                        "type": "list",
                        "model": report.model_name,
                        "arch": arch,
                        "mode": "primary",
                    }
                )
                report.list_view_id = view.id

    @api.model
    def get_report_list(self):
        domain = [
            "|",
            ("is_shared", "=", True),
            ("user_id", "=", self.env.uid),
        ]
        if self.env.user.has_group("kaiSight.group_kai_view_manager"):
            domain = []
        reports = self.search(domain, order="sequence, name")
        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description or "",
                "model": r.model_name,
                "is_shared": r.is_shared,
                "is_favorite": r.is_favorite,
            }
            for r in reports
        ]

    def action_open_report(self):
        self.ensure_one()
        self._check_report_access("read")
        if self.model_name not in self.env:
            raise UserError(
                _("Model “%s” is not available.") % self.model_name
            )
        self._sync_list_view()
        view_modes = (self.view_mode or "list,form").split(",")
        view_modes = [m.strip() for m in view_modes if m.strip()]
        views = []
        for mode in view_modes:
            if mode == "list" and self.list_view_id:
                views.append((self.list_view_id.id, "list"))
            else:
                views.append((False, mode))

        action = {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": self.model_name,
            "view_mode": ",".join(view_modes),
            "views": views,
            "domain": self._parse_domain(),
            "context": dict(self.env.context, **self._parse_context()),
            "target": "current",
        }
        return prepare_act_window_action(action)
