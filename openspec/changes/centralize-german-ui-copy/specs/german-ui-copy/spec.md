## Purpose

Provide consistent German-language text throughout the dashboard from one frontend-owned catalog, without coupling displayed labels to API values.

## ADDED Requirements

### Requirement: Frontend user-facing text comes from the German catalog

All user-facing frontend copy SHALL be provided by the German text catalog, including labels, headings, buttons, placeholders, loading and empty states, error messages, tooltips, accessibility text, and the document title. The document language SHALL be German. A lookup mechanism SHALL provide a safe fallback when a catalog key is missing.

#### Scenario: A dashboard view displays its German copy

- **GIVEN** the shopper opens a dashboard view
- **WHEN** the view renders labels, controls, statuses, or help text
- **THEN** each displayed text is supplied by the German catalog
- **AND** the document declares German as its language

#### Scenario: A catalog entry is unavailable

- **GIVEN** a view requests a missing catalog entry
- **WHEN** the text is displayed
- **THEN** a readable generic fallback is shown instead of an empty value or untranslated key

### Requirement: Display labels do not determine API values

The dashboard SHALL keep language-neutral values used by API requests separate from German display labels. Changing or retrieving a German label SHALL NOT change the value sent to the backend.

#### Scenario: A German filter label is shown

- **GIVEN** a shopper selects a dashboard granularity or ranking view
- **WHEN** the dashboard displays the selected option in German
- **THEN** the API request continues to use its existing language-neutral value
