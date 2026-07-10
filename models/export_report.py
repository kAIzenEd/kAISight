# -*- coding: utf-8 -*-
from odoo import api, models


class ReportKaiSightExportTable(models.AbstractModel):
    _name = "report.kaisight.export_table"
    _description = "kaiSight tabular export PDF"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        return {
            "doc_ids": docids,
            "doc_model": "kai.view.report.builder",
            "docs": self.env["kai.view.report.builder"].browse(docids),
            "headers": data.get("headers", []),
            "rows": data.get("rows", []),
            "report_title": data.get("report_title", "Export"),
            "record_count": data.get("record_count", 0),
            "generated_on": data.get("generated_on", ""),
        }
