# Migration Plan: Highcharts for WebOS Dashboards

This plan details the migration of standard dashboard widgets from static placeholders to dynamic, interactive Highcharts.

## User Review Required

> [!IMPORTANT]
> This migration requires installing `nicegui[highcharts]` which may introduce additional client-side JS dependencies.

## Proposed Changes

### [Component] Root & Core

#### [MODIFY] [pyproject.toml](file:///d:/github/webos/pyproject.toml)
- Add `"nicegui[highcharts]"` to the dependencies list (or ensure it's available).

### [Component] Demo Dashboard Module

#### [MODIFY] [ui.py](file:///d:/github/webos/src/modules/demo_dashboard/ui.py)
- Replace `register_dashboard_widget` static content with a `ui.highchart` component.
- Implement a new `register_system_metrics_widget` that shows a pie chart of Task statuses or User roles.
- Add an `Analytics Hub` page (`/demo`) with multiple Highcharts (Line chart for User growth, Bar chart for Storage usage).

### [Component] Data Providers

#### [NEW] [metrics.py](file:///d:/github/webos/src/modules/demo_dashboard/metrics.py)
- Implement functions to fetch data from Beanie models:
    - `get_user_growth()`: Counts users by month.
    - `get_task_stats()`: Distribution of task results (simulated if not in DB).
    - `get_blogger_stats()`: Post counts per category/user.

## Verification Plan

### Automated Tests
- Run `pytest` to ensure module loading still works and no imports are broken.

### Manual Verification
- Navigate to the Dashboard (`/`).
- Verify that the new Highcharts widgets load and display data accurately.
- Interact with chart tooltips and legends to ensure responsiveness.
- Navigate to the `/demo` Analytics Hub and verify all charts are rendered.
