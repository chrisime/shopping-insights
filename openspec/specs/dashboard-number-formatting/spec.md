# dashboard-number-formatting Specification

## Purpose

Define consistent presentation of monetary amounts, quantities, and percentages across dashboard views.

## Requirements

### Requirement: Monetary amounts use consistent German formatting

The dashboard SHALL display euro amounts using German separators, two decimal places, and a non-breaking space before the currency symbol. Compact chart-axis ticks MAY omit decimal places. Coupon savings SHALL continue to use their supplied currency when available.

#### Scenario: Comparable euro amounts have the same presentation

- **GIVEN** a spending metric, a chart period total, and a receipt total are each 1234.50 euros
- **WHEN** the shopper views those amounts
- **THEN** each amount is displayed as "1.234,50 €"

### Requirement: Quantities retain fractional pieces

The dashboard SHALL preserve fractional piece quantities without adding trailing zeros to whole pieces. Kilogram quantities SHALL use three decimal places.

#### Scenario: Receipt and Top Items quantities use the same precision

- **GIVEN** the receipt and Top Items views each contain quantities of 2.9 pieces, 2 pieces, and 0.5 kilograms
- **WHEN** the shopper views those quantities
- **THEN** both views show the numeric quantities as "2,9", "2", and "0,500", respectively

### Requirement: Savings percentages preserve their magnitude

The dashboard SHALL display savings percentages with German separators and one decimal place without multiplying values already expressed in percent by 100.

#### Scenario: A savings rate is not rescaled

- **GIVEN** a savings rate of 12.5 percent
- **WHEN** the shopper views the savings KPI
- **THEN** the rate is displayed as "12,5 %"
