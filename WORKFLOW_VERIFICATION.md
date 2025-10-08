# Complete Workflow Verification

## ✅ SCENARIO 1: Fresh Entity, Manual Mode
1. Select "Dsi Dh Profiles" source
2. Select "Michael Blum" entity
   → scrapeContent() runs automatically
   → loadSavedSuggestions() checks backend (finds nothing)
   → curationStarted = FALSE
   → aiSuggestions = []
3. UI State:
   - Status: "Ready to start" (blue)
   - Button: "Start" 
   - Metadata fields: Show field names only (NO input fields)
4. User clicks "Start"
   → curationStarted = TRUE
   → metadataFields recomputes
   → needsManualEntry = true (for all fields)
5. Manual input fields appear
6. User fills "Department" field → clicks "Save"
   → POST /api/manual-metadata
   → Backend saves
   → Suggestion added to this.aiSuggestions
   → updateCurationProgress() called
   → Status: "1/5 fields curated"
7. ✅ PERSISTS: Switch to another entity, switch back → loads saved data

## ✅ SCENARIO 2: Fresh Entity, AI Mode  
1-3. Same as manual mode
4. User enables "Use AI Suggestions" checkbox
5. User clicks "Start"
   → POST /api/entities/{id}/scrape with use_ai=true
   → AI generates 5 suggestions
   → aiSuggestions populated
   → curationStarted = TRUE
6. AI suggestion cards appear with Accept/Reject/Edit buttons
7. User clicks "Accept" on "Department"
   → POST /api/suggestions/{id}/curate with action='accept'
   → Backend updates suggestion status
   → aiSuggestions[index] updated
   → updateCurationProgress() called
   → Status: "1/5 fields curated"
8. ✅ PERSISTS across entity switches

## ✅ SCENARIO 3: Previously Worked Entity (3/5 complete)
1. Select "Michael Blum" (previously curated 3 fields)
2. loadSavedSuggestions() runs
   → GET /api/suggestions?edition_id=1
   → Returns 5 suggestions (3 accepted, 2 pending)
   → aiSuggestions = [saved data]
   → curationStarted = FALSE (key!)
3. UI State:
   - Status: "3/5 fields curated - Click Resume to continue" (purple)
   - Button: "Resume" (because aiSuggestions.length > 0)
   - Progress info: "📊 Progress: 3/5 fields curated" (below dropdown)
   - Metadata fields: Show field names only (NO interactive yet!)
4. User clicks "Resume"
   → curationStarted = TRUE
   → metadataFields recomputes
   → For 3 accepted: showAISuggestion=true, shows "ACCEPTED" badge
   → For 2 pending: showAISuggestion=true, shows Accept/Reject buttons
5. User continues curating the 2 pending fields
6. ✅ PERSISTS: All actions saved to backend

## ✅ SCENARIO 4: Completed Entity (5/5 complete)
1. Select previously completed entity
2. loadSavedSuggestions() returns 5 accepted/rejected
   → aiSuggestions = [all complete]
   → Status: "✓ All 5 fields complete - Click Resume to view"
   → Progress: "✓ All 5 fields completed"
3. User clicks "Resume" → Shows all 5 fields with status badges
4. User can re-curate if needed (Edit button available)
5. ✅ ALL DATA PRESERVED

## ✅ SCENARIO 5: Switch Between Entities
1. Curate Michael Blum (3/5 fields)
   → Each accept/reject saved to backend immediately
   → DATA["suggestions"] has entries with edition_id=1
2. Switch to "Moritz Mähr"
   → onEntityChange() fires
   → curationStarted = FALSE
   → aiSuggestions = []
   → Scrapes Moritz's content
   → loadSavedSuggestions(entity_id=2)
3. Curate Moritz (2/5 fields)
   → Saved to backend with edition_id=2
4. Switch back to Michael Blum
   → loadSavedSuggestions(entity_id=1)
   → Loads Michael's 3 completed fields
   → Status: "3/5 fields curated - Click Resume"
5. ✅ Michael's data fully preserved!

## 🔒 KEY INVARIANTS (Must Always Be True):

1. ✅ curationStarted = false UNTIL user clicks Start/Resume
2. ✅ NO interactive fields appear before Start/Resume clicked
3. ✅ loadSavedSuggestions() NEVER sets curationStarted=true
4. ✅ All Accept/Reject/Edit actions save to backend immediately
5. ✅ updateCurationProgress() called after every action
6. ✅ Progress shown below dropdown, NOT in dropdown options
7. ✅ Button text: "Start" (fresh) or "Resume" (has saved data)
8. ✅ Data persists in backend until restart (in-memory DATA)

## 📊 Progress Indicators (NO HARDCODING):

- Entity dropdown: Clean, no progress clutter
- Below dropdown: "📊 Progress: 3/5 fields curated" (when has saved data)
- Status pill: Shows current state and progress count
- All calculated dynamically from this.aiSuggestions array

