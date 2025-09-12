# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.14] - 2025-09-12

### Fixed

- Serialize caught saves with a lock to prevent stale overwrites.

## [0.1.13] - 2025-09-12

### Fixed

- Guard real store writes with a versioned lock to avoid stale commits.

## [0.1.12] - 2025-09-11

### Fixed

- Prevent stale writes in mock store by guarding updates with a versioned lock.

## [0.1.11] - 2025-09-11

### Added

- RCA diagnostic tooling added; no fix shipped in this release.

## [0.1.10] - 2025-09-11

### Fixed

- Preserve rapid caught selections by updating session state before saving and guarding against concurrent writes.

## [0.1.9] - 2025-09-11

### Fixed

- Prevent quick successive caught selections from unmarking previously chosen Pokémon by diffing full table state instead of relying on ephemeral widget edits.

## [0.1.8] - 2025-09-11

### Added

- Share filtered results via generated links in the Streamlit UI.

## [0.1.7] - 2025-09-11

### Fixed

- Store caught Pokémon progress outside the app directory to prevent selection resets when marking multiple as caught rapidly.

## [0.1.6] - 2025-09-11

### Added

- Persist favorite Pokémon selections and filter by favorites in the Streamlit UI.

## [0.1.5] - 2025-09-11

### Added

- Capture Pokémon types and regional availability from PokeAPI.
- Filter by type and region in Streamlit UI.

## [0.1.4] - 2025-09-11

### Fixed

- Preserve previously selected Pokémon when marking multiple as caught in quick succession.

## [0.1.3] - 2025-09-11

### Fixed

- Prevent checkboxes from resetting when marking multiple Pokémon as caught in quick succession.

## [0.1.2] - 2025-09-11

### Fixed

- Make "Caught" column selectable in the Streamlit UI.

## [0.1.1] - 2025-09-11

### Added

- Track caught Pokémon in the UI.
- Add Pokémon type and region filters.

## [0.1.0] - 2024-09-10

### Added

- Initial release.
