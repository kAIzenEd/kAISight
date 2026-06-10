# kaiSight

Interactive dashboards and saved reports for any Odoo model, built on the standard ORM (`search_read`, `read_group`, `search_count`).

**Version:** 19.0.1.0.4  
**License:** LGPL-3  
**Author:** [Kaiddons](https://kaizened.in)

## Features

- **Dashboards** — configurable grid of widgets (KPI, chart, record list)
- **Saved reports** — reusable window actions with domain filters for any installed model
- **Sharing** — dashboards and reports can be private or shared with all internal users
- **Extensible** — other addons can ship dashboards/widgets via XML data or Python API

## Requirements

- Odoo **19.0**
- Dependencies: `base`, `web`

## Installation

1. Clone this repository into your Odoo addons path:

   ```bash
   git clone https://github.com/Kaiddons/kaiSight.git
   ```

2. Update the apps list and install **kaiSight** from the Odoo Apps menu.

3. Open **kaiSight → Dashboard** to view the sample dashboard (demo data is loaded on install).

## Usage

| Menu | Description |
|------|-------------|
| kaiSight → Dashboard | Main interactive dashboard view |
| kaiSight → Configuration → Dashboards | Create and edit dashboards and widgets |
| kaiSight → Configuration → Saved reports | Manage saved report shortcuts |

### Widget types

| Type | Description |
|------|-------------|
| **KPI / Count** | Single metric (count, sum, or average) with optional drill-down |
| **Chart** | Bar, line, pie, or doughnut chart via `read_group` |
| **Record list** | Filtered list preview with click-through to records |

## Extending from another addon

Register widgets on a dashboard defined in your module:

```python
self.env["kai.view.dashboard"].register_widgets_from_addon(
    "my_addon.dashboard_sales",
    [
        {
            "name": "Open quotations",
            "widget_type": "kpi",
            "model_id": self.env.ref("sale.model_sale_order").id,
            "domain": "[('state', '=', 'draft')]",
            "aggregate": "count",
            "icon": "fa-file-text-o",
        },
    ],
)
```

## Development

After changing JavaScript or SCSS assets, upgrade the module and hard-refresh the browser:

```bash
./odoo-bin -u kaiSight -d your_database
```

## Contributing

Issues and pull requests are welcome on GitHub.

## License

This module is licensed under [LGPL-3](LICENSE).
