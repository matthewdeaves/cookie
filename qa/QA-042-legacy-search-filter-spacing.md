# QA-042: Legacy Search Results - Source Filters Need More Spacing

## Problem

On the legacy frontend search results page, the source filter buttons/chips are too close together. They appear cramped with insufficient spacing between them.

## Affects

- Legacy frontend only
- Search results page (`/legacy/search/`)

## Current Behavior

Source filter buttons are displayed with minimal or no gap between them, making them:
- Harder to tap accurately on touch devices (iPad)
- Visually cramped and harder to scan

## Expected Behavior

Source filters should have adequate spacing (e.g., 8-12px gap) between each filter chip for:
- Better touch targets on mobile/tablet
- Improved visual hierarchy and readability

## Files to Check

- `apps/legacy/static/legacy/css/components.css` - Filter/chip styling
- `apps/legacy/templates/legacy/search.html` - Search results template

## Priority

Low - Visual polish / UX improvement

## Status

New
