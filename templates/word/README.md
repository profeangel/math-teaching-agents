# Microsoft Word Templates (`docxtpl`)

This directory contains the specifications for rendering assessments and lesson worksheets in editable `.docx` format using the `docxtpl` Python library (powered by Jinja2 syntax for Word).

## Standard Jinja2 Variables Injected by `universal-format-engine`

| Jinja2 Variable | Type | Description |
| :--- | :--- | :--- |
| `{{ title }}` | String | Title of the assessment or worksheet |
| `{{ target_grade }}` | String | Target grade level or cohort |
| `{{ total_points }}` | Number | Total available points |
| `{{ instructions }}` | String | General instructions paragraph |
| `{% for item in items %}` | Loop | Iterator across questions and problems |
| `{{ item.number }}` | Integer | Question sequence number |
| `{{ item.stem }}` | String | Question stem or problem formulation |
| `{{ item.points }}` | Number | Point value for the item |
| `{{ item.options }}` | List | Multiple-choice options (if applicable) |
| `{{ item.rubric }}` | Dict | Qualitative scoring rubric matrix (for open-ended items) |
| `{% endfor %}` | - | Loop termination |

## How to Customize Your School's Word Template
1. Open Microsoft Word and create a document with your school's logo, header, fonts, and branding.
2. Insert the Jinja2 tags above into the designated sections.
3. Save the document as `templates/school.docx` in your working directory.
4. The `universal-format-engine` will auto-detect it and populate your assessments conforming strictly to your institutional layout.
