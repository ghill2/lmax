# Changelog

## [1.9.0.7]

- Add openingOrderId to Order.  This references the opening order for stop loss and take profit orders.

## [1.9.0.6]

- Added public accessors for cash and credit on AccountStateEvent

## [1.9.0.3]

- Added EncodedExceutionId to Execution.

## [1.9.0.2]

- Fixed Tutorial documentation

## [1.9.0.1]

- Fix the issue where Net Open Position values could sometimes be applied to other wallets
- Report Net Margin Open Positions in Account State Events
- Fix a bug where a HTTP response could be used after it has been disposed

## [1.8.4]

- Revert addition of openingOrderId from OrderBuilder

## [1.8.2]

- Include openingOrderId in the OrderBuilder

