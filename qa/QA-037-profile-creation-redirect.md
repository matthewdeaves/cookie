# QA-037: Auto-Navigate to Home After Profile Creation

## Issue
After creating a new profile, the user stays on the profile selector screen. They should automatically be taken to the home/search page.

## Current Behavior
1. User opens app
2. User clicks "Create Profile"
3. User enters name and creates profile
4. User stays on profile selector screen
5. User must manually select the new profile to proceed

## Expected Behavior
1. User opens app
2. User clicks "Create Profile"
3. User enters name and creates profile
4. User is automatically logged in as the new profile and taken to home/search page

## Affected Components
- **React**: `ProfileSelector.tsx` - profile creation flow
- **Legacy**: Profile creation in legacy templates/JS

## Priority
Low - UX improvement, minor friction

## Phase
TBD
