/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";

export class KaiSightSaveReportDialog extends Component {
    static template = "kaisight.SaveReportDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        onSave: Function,
        defaultName: { type: String, optional: true },
    };

    setup() {
        this.state = useState({
            name: this.props.defaultName || "",
            isShared: false,
            saving: false,
            error: null,
        });
    }

    async onConfirm() {
        if (!this.state.name.trim()) {
            this.state.error = _t("Enter a report name.");
            return;
        }
        this.state.saving = true;
        this.state.error = null;
        try {
            await this.props.onSave(this.state.name.trim(), this.state.isShared);
            this.props.close();
        } catch (e) {
            this.state.error = e.message || _t("Could not save report.");
            this.state.saving = false;
        }
    }
}

export class KaiSightReportBuilderAction extends Component {
    static template = "kaisight.ReportBuilder";
    static components = { KaiSightSaveReportDialog };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.dialog = useService("dialog");
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            sources: [],
            selectedSource: null,
            fieldGroups: [],
            filterCatalog: [],
            selectedFields: {},
            fieldSearch: "",
            quickFilters: {},
            domain: "[]",
            showFiltersPanel: true,
            recordCount: null,
            exporting: false,
            showSaveDialog: false,
            error: null,
        });

        onWillStart(async () => {
            await this.loadSources();
        });
    }

    async loadSources() {
        this.state.loading = true;
        this.state.error = null;
        try {
            const sources = await this.orm.call(
                "kai.view.report.builder",
                "get_source_catalog",
                []
            );
            this.state.sources = sources;
            if (sources.length === 1) {
                await this.selectSource(sources[0]);
            }
        } catch (e) {
            this.state.error = e.message || _t("Could not load data sources.");
        } finally {
            this.state.loading = false;
        }
    }

    async selectSource(source) {
        this.state.selectedSource = source;
        this.state.fieldSearch = "";
        this.state.domain = "[]";
        this.state.quickFilters = {};
        this.state.recordCount = null;
        try {
            const catalog = await this.orm.call(
                "kai.view.report.builder",
                "get_field_catalog",
                [source.model]
            );
            this.state.fieldGroups = catalog.groups || [];
            try {
                const filterCatalog = await this.orm.call(
                    "kai.view.report.builder",
                    "get_filter_catalog",
                    [source.model]
                );
                this.state.filterCatalog = filterCatalog.filters || [];
            } catch (filterError) {
                console.warn("Could not load quick filters", filterError);
                this.state.filterCatalog = [];
            }
            const defaults = source.default_fields || [];
            if (defaults.length) {
                this.state.selectedFields = Object.fromEntries(defaults.map((n) => [n, true]));
            } else {
                const firstGroup = this.state.fieldGroups[0];
                const pick = (firstGroup?.fields || []).slice(0, 6).map((f) => f.name);
                this.state.selectedFields = Object.fromEntries(pick.map((n) => [n, true]));
            }
            await this.refreshCount();
        } catch (e) {
            this.state.error = e.message || _t("Could not load fields.");
        }
    }

    get filteredGroups() {
        const q = (this.state.fieldSearch || "").trim().toLowerCase();
        if (!q) {
            return this.state.fieldGroups;
        }
        return this.state.fieldGroups
            .map((group) => ({
                ...group,
                fields: group.fields.filter(
                    (f) =>
                        f.label.toLowerCase().includes(q) ||
                        f.name.toLowerCase().includes(q)
                ),
            }))
            .filter((g) => g.fields.length);
    }

    get selectedCount() {
        return Object.keys(this.state.selectedFields).length;
    }

    get selectedFieldList() {
        return Object.keys(this.state.selectedFields);
    }

    isFieldSelected(name) {
        return !!this.state.selectedFields[name];
    }

    toggleField(name) {
        if (this.state.selectedFields[name]) {
            const next = { ...this.state.selectedFields };
            delete next[name];
            this.state.selectedFields = next;
        } else {
            this.state.selectedFields = { ...this.state.selectedFields, [name]: true };
        }
    }

    selectRecommended() {
        const defaults = this.state.selectedSource?.default_fields || [];
        if (defaults.length) {
            this.state.selectedFields = Object.fromEntries(defaults.map((n) => [n, true]));
        } else {
            this.selectAllVisible();
        }
    }

    selectAllVisible() {
        const names = [];
        for (const group of this.state.fieldGroups) {
            for (const field of group.fields) {
                names.push(field.name);
            }
        }
        this.state.selectedFields = Object.fromEntries(names.map((n) => [n, true]));
    }

    clearSelection() {
        this.state.selectedFields = {};
    }

    toggleFiltersPanel() {
        this.state.showFiltersPanel = !this.state.showFiltersPanel;
    }

    get hasActiveFilters() {
        const quick = Object.values(this.state.quickFilters).some(
            (v) => v !== undefined && v !== null && v !== ""
        );
        const advanced = (this.state.domain || "[]").trim() !== "[]";
        return quick || advanced;
    }

    get activeFilterCount() {
        let count = Object.values(this.state.quickFilters).filter(
            (v) => v !== undefined && v !== null && v !== ""
        ).length;
        if ((this.state.domain || "[]").trim() !== "[]") {
            count += 1;
        }
        return count;
    }

    async onQuickFilterChange(fieldName, value) {
        const next = { ...this.state.quickFilters };
        if (value === "" || value === null || value === undefined) {
            delete next[fieldName];
        } else {
            next[fieldName] = value;
        }
        this.state.quickFilters = next;
        await this.refreshCount();
    }

    async clearAllFilters() {
        this.state.quickFilters = {};
        this.state.domain = "[]";
        await this.refreshCount();
    }

    filterSelectValue(fieldName) {
        const value = this.state.quickFilters[fieldName];
        return value === undefined || value === null ? "" : String(value);
    }

    filterTextValue(fieldName) {
        return this.state.quickFilters[fieldName] || "";
    }

    async onQuickFilterText(fieldName, ev) {
        await this.onQuickFilterChange(fieldName, ev.target.value.trim());
    }

    async refreshCount() {
        if (!this.state.selectedSource) {
            return;
        }
        this.state.recordCount = await this.orm.call(
            "kai.view.report.builder",
            "preview_record_count",
            [this.state.selectedSource.model, this.state.domain],
            { quick_filters: this.state.quickFilters }
        );
    }

    async openFilters() {
        const builderId = await this.orm.call(
            "kai.view.report.builder",
            "create_filter_wizard",
            [this.state.selectedSource.model, this.state.domain]
        );
        const [, filterViewId] = await this.orm.call(
            "ir.model.data",
            "check_object_reference",
            ["kaisight", "view_kai_view_report_builder_filter_form"]
        );
        this.actionService.doAction(
            {
                type: "ir.actions.act_window",
                name: _t("Report filters"),
                res_model: "kai.view.report.builder",
                res_id: builderId,
                views: [[filterViewId, "form"]],
                target: "new",
            },
            {
                onClose: async () => {
                    const record = await this.orm.read(
                        "kai.view.report.builder",
                        [builderId],
                        ["domain"]
                    );
                    if (record.length) {
                        this.state.domain = record[0].domain || "[]";
                        await this.refreshCount();
                    }
                    await this.orm.unlink("kai.view.report.builder", [builderId]);
                },
            }
        );
    }

    async exportReport(format) {
        if (!this.selectedCount) {
            this.notification.add(_t("Select at least one column."), { type: "warning" });
            return;
        }
        this.state.exporting = true;
        try {
            const action = await this.orm.call(
                "kai.view.report.builder",
                "export_report",
                [
                    this.state.selectedSource.model,
                    this.selectedFieldList,
                    this.state.domain,
                    format,
                ],
                {
                    quick_filters: this.state.quickFilters,
                    report_title: this.state.selectedSource.name,
                }
            );
            await this.actionService.doAction(action);
            this.notification.add(_t("Export started."), { type: "success" });
        } catch (e) {
            this.notification.add(e.message || _t("Export failed."), { type: "danger" });
        } finally {
            this.state.exporting = false;
        }
    }

    async openInOdoo() {
        if (!this.selectedCount) {
            this.notification.add(_t("Select at least one column."), { type: "warning" });
            return;
        }
        try {
            const action = await this.orm.call(
                "kai.view.report.builder",
                "action_open_in_odoo",
                [
                    this.state.selectedSource.model,
                    this.selectedFieldList,
                    this.state.domain,
                    this.state.selectedSource.name,
                ],
                { quick_filters: this.state.quickFilters }
            );
            await this.actionService.doAction(action);
        } catch (e) {
            this.notification.add(e.message || _t("Could not open report."), { type: "danger" });
        }
    }

    openSaveDialog() {
        if (!this.selectedCount) {
            this.notification.add(_t("Select at least one column."), { type: "warning" });
            return;
        }
        this.dialog.add(KaiSightSaveReportDialog, {
            defaultName: this.state.selectedSource?.name || "",
            onSave: this.saveReport.bind(this),
        });
    }

    async saveReport(name, isShared) {
        await this.orm.call("kai.view.report.builder", "save_report", [], {
            name,
            model_name: this.state.selectedSource.model,
            field_names: this.selectedFieldList,
            domain_str: this.state.domain,
            is_shared: isShared,
            quick_filters: this.state.quickFilters,
        });
        this.notification.add(_t("Report saved."), { type: "success" });
    }

    async openSavedReports() {
        const [, actionId] = await this.orm.call(
            "ir.model.data",
            "check_object_reference",
            ["kaisight", "action_kai_view_reports"]
        );
        const action = await this.actionService.loadAction(actionId);
        await this.actionService.doAction(action);
    }
}

registry.category("actions").add("kai_view_report_builder", KaiSightReportBuilderAction);
