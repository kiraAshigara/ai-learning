# AI - Learning Path

![Logo](docs/title-logo.png)

This repository contains projects and resources for learning about AI-powered automation and workflow integration.

## Projects

### 1. csv-report

**Purpose:**
Automate the generation and delivery of sales reports from CSV data using AI-powered workflows.

**Summary:**
The `csv-report` project demonstrates how to use workflow automation (with n8n) and AI agents to process sales data, generate analytics, create visual reports, and deliver them via email. It is designed as a learning resource for integrating AI into reporting pipelines.

**Key Features:**
- Extracts sales data from CSV files (see `resources/sales_week.csv`).
- Loads data into a PostgreSQL database.
- Uses AI agents to generate SQL queries for analytics (e.g., sales by product, low stock, daily sales).
- Creates visual charts from report data using Plotly.js.
- Generates HTML reports and serves them via Nginx.
- Sends responsive HTML email reports (using MailHog for testing).
- All steps are orchestrated by n8n workflows (see `workflows/csv_report.json`).

**Documentation and Resources:**
- See [csv-report/README.md](csv-report/README.md) for detailed setup and usage instructions.
- Example workflow and report images are available in `csv-report/docs/`.

---

More projects and learning modules will be added to this repository in the future.

