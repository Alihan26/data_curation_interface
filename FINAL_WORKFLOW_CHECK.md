# ✅ FINAL WORKFLOW VERIFICATION - ALL SCENARIOS

## 🎯 SCENARIO 1: Manual Curation (Fresh Entity)

**Steps:**
1. Select "Michael Blum"
   - ✅ Content scrapes automatically
   - ✅ Status: "Ready to start"
   - ✅ Button: "Start"
   - ✅ Fields: Just names, NO input forms yet

2. Click "Start"
   - ✅ Manual entry forms appear
   - ✅ No AI elements visible (no reasoning, no confidence badges)

3. Fill "Department" → Select "Department of Informatics" → Click "Save"
   - ✅ POST /api/manual-metadata
   - ✅ Backend saves: {ai_generated: false, status: "accepted"}
   - ✅ Frontend shows:
     * Header: "Department" (NO 🤖 badge)
     * Label: "Manual Entry:"
     * Value: "Department of Informatics" (purple border)
     * Badge: "✓ SAVED"
     * NO AI Reasoning section ✅
     * NO Accept/Reject buttons ✅
   - ✅ Progress: "1/5 fields curated"

4. Fill other fields manually
   - ✅ All show as "✓ SAVED" with NO AI elements

5. Switch to "Moritz Mähr" → Switch back
   - ✅ All manual entries still show "✓ SAVED"
   - ✅ NO AI elements appear ✅

## 🤖 SCENARIO 2: AI Curation (Fresh Entity)

**Steps:**
1. Enable "Use AI Suggestions"
2. Select "Jürgen Bernard"
3. Click "Start"
   - ✅ AI generates 5 suggestions
   - ✅ High confidence (≥70%) fields show:
     * Header: "Department 🤖 85%"
     * Label: "AI Suggested:"
     * Value: "Department of Informatics"
     * "AI Reasoning:" with full text
     * Buttons: Accept | Reject | Edit

4. Click "Accept"
   - ✅ Backend updates: status: "accepted"
   - ✅ Buttons disappear
   - ✅ Shows: "✓ ACCEPTED" badge
   - ✅ Reasoning still visible
   - ✅ Progress: "1/5 fields curated"

5. Low confidence field (<70%)
   - ✅ Shows manual entry form (not AI suggestion)
   - ✅ Fill manually → saves as manual entry
   - ✅ Shows "✓ SAVED" with NO AI elements

## 🔄 SCENARIO 3: Resume Previous Work

**Steps:**
1. Select "Michael Blum" (previously worked on)
   - ✅ loadSavedSuggestions() fetches data
   - ✅ curationStarted = FALSE (key!)
   - ✅ Status: "3/5 fields curated - Click Resume"
   - ✅ Progress info: "📊 Progress: 3/5 fields curated" (below dropdown)
   - ✅ Button: "Resume"
   - ✅ Fields: Just names, NO interactive elements yet

2. Click "Resume"
   - ✅ curationStarted = TRUE
   - ✅ Completed manual entries show: "Manual Entry:" + "✓ SAVED"
   - ✅ Completed AI suggestions show: "AI Suggested:" + "✓ ACCEPTED"
   - ✅ Pending fields show: Input forms or AI suggestions
   - ✅ NO confusion between manual and AI ✅

## ✓ CHECKLIST - All Must Be True:

□ Manual entries show "Manual Entry:" label (not "AI Suggested:")
□ Manual entries show NO AI reasoning section
□ Manual entries show NO 🤖 confidence badge in header
□ Manual entries show "✓ SAVED" badge (not Accept/Reject buttons)
□ Manual entries have purple border (not AI blue)
□ AI suggestions show "AI Suggested:" label
□ AI suggestions show AI reasoning
□ AI suggestions show 🤖 confidence badge
□ AI pending suggestions show Accept/Reject/Edit buttons
□ AI accepted suggestions show "✓ ACCEPTED" (no buttons)
□ Cannot curate before clicking Start/Resume
□ Progress shown below dropdown (not inside dropdown)
□ Progress counts: manual + accepted + rejected + edited
□ Entity switch preserves all data
□ Button text: "Start" (fresh) or "Resume" (has data)

