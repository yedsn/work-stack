## ADDED Requirements

### Requirement: Responsive Icon Rendering
Launch item cards SHALL display application icons without blocking UI rendering. Icon lookups MUST run asynchronously with caching so that list rebuilds remain interactive even when hundreds of entries refresh simultaneously.

#### Scenario: Placeholder first, icon later
- **WHEN** a tab loads or refreshes with icons enabled
- **THEN** each card initially renders a lightweight placeholder while the icon loader resolves the real pixmap in the background
- **AND** once the pixmap is available, the card updates without freezing the UI thread.

#### Scenario: Icon cache reuse
- **WHEN** multiple cards reference the same executable or path
- **THEN** the loader reuses a cached pixmap instead of re-reading disk for each card
- **AND** bulk refreshes (e.g., "??" tab) finish within the same responsiveness budget as when icons are disabled.

#### Scenario: Graceful degradation
- **WHEN** the loader cannot resolve an icon within a defined timeout or the file is missing
- **THEN** the card keeps showing the placeholder/fallback icon and logs the issue without blocking other load requests.
