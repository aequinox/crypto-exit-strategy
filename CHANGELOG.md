# Changelog

All notable changes to the Crypto Market Monitor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-05-14

### Added

- Historical data tracking for all market indicators
- Seaborn charts generation for all tracked indicators
- HTML email support with embedded charts
- Migration utility to convert existing altcoin ratio history to new format
- New `IndicatorHistory` class for centralized history management
- Support for tracking Bitcoin dominance, Ethereum dominance, total market cap, altcoin ratio, M2 money supply, and Fear & Greed Index history

### Changed

- Enhanced email alerts with visual charts of historical data
- Updated README with new features documentation
- Improved error handling for API requests
- Modified email sending function to support both HTML and plain text formats
- Maintained backward compatibility with existing tests

### Fixed

- Ensured compatibility with test suite by preserving original email format for test cases

## [0.1.0] - 2025-05-01

### Added

- Initial release
- Bitcoin dominance monitoring
- M2 money supply analysis
- Altcoin market pullback detection
- Social media & app store trend analysis
- Fear & Greed Index integration
- Email alerts for market conditions
