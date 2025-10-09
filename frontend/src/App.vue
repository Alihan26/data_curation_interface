<template>
  <div id="app">
    <!-- Header -->
    <header class="app-header">
      <div class="header-container">
        <div class="header-left">
          <div class="logo-section">
            <h1 class="app-title">Metadata Curation Interface</h1>
            <span class="version-badge">v2.0</span>
          </div>
        </div>

        <div class="header-right">
          <div class="user-profile">
            <div class="user-avatar">AK</div>
            <div class="user-info">
              <div class="user-greeting">Hello, Alihan Karataşlı</div>
              <div class="user-role">Data Curator</div>
            </div>
            <button @click="showUserMenu = !showUserMenu" class="user-menu-btn">
              <img src="/src/assets/icons/setting.png" alt="Settings" class="icon-img">
            </button>
          </div>

          <div v-if="showUserMenu" class="user-dropdown" @click.stop>
            <div class="dropdown-item" @click="showSettings">
              <img src="/src/assets/icons/setting.png" alt="Settings" class="icon-img">
              Settings
            </div>
            <div class="dropdown-item" @click="showHelp">
              <span class="icon">❓</span>
              Help & Documentation
            </div>
            <div class="dropdown-divider"></div>
            <div class="dropdown-item logout" @click="logout">
              <span class="icon">🚪</span>
              Logout
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Control Panel - Fixed Layout -->
    <div class="control-panel">
      <div class="control-grid">
        <!-- Column 1: Source and Entity Selection (stacked) -->
        <div class="control-col col-selection">
          <label>Select Source/Catalog:</label>
          <select 
            v-model="selectedSourceId" 
            @change="onSourceChange"
            :disabled="isLoading"
            class="source-select"
          >
            <option value="">Choose a catalog...</option>
            <option 
              v-for="source in sources" 
              :key="source.id" 
              :value="source.id"
            >
              {{ source.name }} ({{ source.editions_count }} entities)
            </option>
          </select>
          
          <label style="margin-top: 10px;">Select Entity:</label>
          <select 
            v-model="selectedEntityId" 
            @change="onEntityChange"
            :disabled="isLoading || !selectedSourceId"
            class="entity-select"
          >
            <option value="">{{ selectedSourceId ? 'Choose an entity...' : 'Select source first' }}</option>
            <option 
              v-for="edition in filteredEditions" 
              :key="edition.id" 
              :value="edition.id"
            >
              {{ edition.entity_name || edition.source_internal_id || `Entity ${edition.id}` }}
            </option>
          </select>
          
          <!-- Show progress for selected entity below dropdown -->
          <div v-if="selectedEntityId && aiSuggestions.length > 0 && !curationStarted" class="entity-progress-info">
            {{ getEntityProgressText() }}
          </div>
        </div>
        
        <!-- Column 2: AI Toggle -->
        <div class="control-col col-ai">
          <label class="ai-label">
            <input 
              type="checkbox" 
              v-model="useAI" 
              :disabled="isLoading || !selectedEntityId || curationStarted"
              @change="onAIToggleChange"
              class="ai-checkbox"
            >
              Use AI Suggestions
            </label>
          <div class="ai-desc">{{ useAI ? 'AI enabled' : 'AI disabled' }}</div>
          </div>
          
        <!-- Column 3: Confidence -->
        <div class="control-col col-confidence">
          <label>Confidence: {{ confidenceThreshold }}%</label>
            <input 
              type="range" 
              min="0" 
              max="100" 
              step="5" 
            v-model.number="confidenceThreshold" 
            :disabled="isLoading || curationStarted || !useAI"
            class="confidence-slider"
            >
          <small>{{ useAI ? `≥ ${confidenceThreshold}% threshold` : 'AI disabled' }}</small>
          </div>
          
        <!-- Column 4: Action -->
        <div class="control-col col-action">
          <button 
            v-if="selectedEntityId && scrapedContent.pages.length > 0"
            @click="startCuration" 
            :disabled="isLoading || curationStarted"
            class="start-btn"
            :class="{ 'ai-mode': useAI, 'manual-mode': !useAI }"
          >
            {{ curationStarted ? 'Active' : (aiSuggestions.length > 0 ? 'Resume' : 'Start') }}
          </button>
          <div v-else class="start-placeholder">Select entity</div>
          </div>
          
        <!-- Column 5: Status -->
        <div class="control-col col-status">
          <div class="status-pill" :class="statusClass">
            <span class="status-dot"></span>
            <span>{{ statusText }}</span>
          </div>
        </div>
            </div>
            </div>
          
    <!-- Loading Indicator -->
    <div v-if="isLoading" class="loading-indicator">
      <div class="loading-spinner"></div>
      <div class="loading-text">
        {{ useAI ? 'Scraping content and generating AI suggestions...' : 'Scraping content for manual curation...' }}
            </div>
          </div>
          
    <!-- Main Content Area -->
    <div class="main-content">
      <!-- Left Side: Scraped Content -->
      <div class="content-panel">
        <div class="panel-header">
          <h2>Scraped Content</h2>
          <div v-if="scrapedContent.pages && scrapedContent.pages.length > 0" class="content-stats">
            {{ scrapedContent.pages.length }} page{{ scrapedContent.pages.length > 1 ? 's' : '' }} scraped
            <span v-if="scrapedContent.scraped_at" class="scraped-time">
              {{ formatTime(scrapedContent.scraped_at) }}
            </span>
              </div>
            </div>
            
        <div v-if="!selectedEntityId" class="empty-state">
          <div class="empty-icon">
            <img src="/src/assets/icons/paper.png" alt="Document" class="icon-img">
          </div>
          <h3>Select an Entity to Begin</h3>
          <p>Choose an entity from the dropdown above to start scraping content and curating metadata.</p>
    </div>

        <div v-else-if="!scrapedContent.pages || scrapedContent.pages.length === 0" class="empty-state">
          <div class="empty-icon">⏳</div>
          <h3>No Content Yet</h3>
          <p>Content will appear here after scraping begins.</p>
        </div>
        
        <div v-else class="content-display">
          <!-- Page Navigation -->
          <div v-if="scrapedContent.pages.length > 1" class="page-navigation">
          <button 
            @click="previousPage" 
            :disabled="currentPageIndex === 0"
              class="nav-btn"
          >
              ← Previous
          </button>
          <span class="page-counter">
              Page {{ currentPageIndex + 1 }} of {{ scrapedContent.pages.length }}
          </span>
          <button 
            @click="nextPage" 
              :disabled="currentPageIndex === scrapedContent.pages.length - 1"
              class="nav-btn"
          >
              Next →
          </button>
        </div>
        
          <!-- Current Page Content -->
          <div v-if="currentPage" class="page-content">
            <h3 class="page-title">{{ currentPage.title }}</h3>
            <div class="page-url">{{ currentPage.url }}</div>
            
            <!-- Structured Content Display -->
            <div v-if="currentPage.structured_content" class="structured-page">
              <!-- Navigation Bar -->
              <div v-if="currentPage.structured_content.navigation" class="page-navigation-bar">
                <div class="nav-label">🧭 Navigation:</div>
                <div class="nav-content">{{ currentPage.structured_content.navigation }}</div>
              </div>
              
              <!-- Page Headers -->
              <div v-if="currentPage.structured_content.header && currentPage.structured_content.header.length" class="page-headers">
                <h1 v-for="(header, idx) in currentPage.structured_content.header.filter(h => h.level === 'h1')" :key="'h1-' + idx" class="main-header" v-html="highlightText(header.text)"></h1>
                <h2 v-for="(header, idx) in currentPage.structured_content.header.filter(h => h.level === 'h2')" :key="'h2-' + idx" class="sub-header" v-html="highlightText(header.text)"></h2>
              </div>
              
              <!-- Main Content Sections -->
              <div v-if="currentPage.structured_content.main_sections && currentPage.structured_content.main_sections.length" class="main-content-sections">
                <div v-for="(section, idx) in currentPage.structured_content.main_sections" :key="'section-' + idx" class="content-section">
                  <h3 v-if="section.title" class="section-title" v-html="highlightText(section.title)"></h3>
                  
                  <div v-if="section.paragraphs && section.paragraphs.length" class="section-paragraphs">
                    <p v-for="(para, pIdx) in section.paragraphs" :key="'p-' + pIdx" class="section-paragraph" v-html="highlightText(para)"></p>
                  </div>
                  
                  <div v-if="section.lists && section.lists.length" class="section-lists">
                    <ul v-for="(list, lIdx) in section.lists" :key="'list-' + lIdx" class="section-list">
                      <li v-for="(item, iIdx) in list" :key="'item-' + iIdx" v-html="highlightText(item)"></li>
                    </ul>
                  </div>
                </div>
              </div>
              
              <!-- Footer -->
              <div v-if="currentPage.structured_content.footer" class="page-footer">
                <div class="footer-label">Footer:</div>
                <div class="footer-content">{{ currentPage.structured_content.footer }}</div>
              </div>
            </div>
            
            <!-- Fallback: Plain text with highlighting (when no structured content) -->
            <div v-else class="content-text" v-html="highlightedContent"></div>
          </div>
            </div>
          </div>
          
      <!-- Right Side: Metadata Fields (Always Visible) -->
      <div class="metadata-panel">
        <div class="panel-header">
          <h2>Metadata Fields</h2>
          <div v-if="selectedSource" class="metadata-stats">
            {{ selectedSource.name }}
            <span class="field-count">{{ metadataFields.length }} fields</span>
            </div>
          </div>
          
        <div v-if="!selectedEntityId" class="empty-state">
          <div class="empty-icon">
            <img src="/src/assets/icons/checklist.png" alt="Checklist" class="icon-img">
                          </div>
          <h3>Metadata Fields</h3>
          <p>Select an entity to see metadata fields for curation.</p>
                  </div>
                  
        <div v-else class="metadata-content">
          <!-- Mode Indicator -->
          <div v-if="curationStarted" class="mode-indicator" :class="useAI ? 'ai-mode' : 'manual-mode'">
            <span class="mode-icon">{{ useAI ? '🤖' : '✍️' }}</span>
            <span class="mode-text">{{ useAI ? 'AI Suggestion Mode' : 'Manual Curation Mode' }}</span>
            <span v-if="useAI" class="threshold-info">Threshold: {{ confidenceThreshold }}%</span>
                </div>

          <!-- Pre-Curation Info -->
          <div v-else-if="scrapedContent.pages.length > 0" class="pre-curation-info">
            <img src="/src/assets/icons/checklist.png" alt="Info" class="info-icon-img">
            <span class="info-text">Content scraped. Click "Start Curation" to begin metadata entry.</span>
                </div>

          <!-- Fully Curated Read-Only View -->
          <div v-if="isEntityFullyCurated && !curationStarted" class="curated-view">
            <div class="curated-header">
              <div class="curated-title">
                <span class="check-icon">✓</span>
                <h3>Fully Curated Entity</h3>
              </div>
              <p class="curated-subtitle">All metadata fields have been completed for this entity</p>
            </div>

            <div class="curated-actions">
              <button @click="resumeEditing" class="btn-resume">
                <span class="btn-icon">✏️</span>
                Edit Metadata
              </button>
              <button @click="useAI = true; startCuration()" class="btn-ai-recurate" v-if="!useAI">
                <span class="btn-icon">🤖</span>
                Re-curate with AI
              </button>
            </div>

            <div class="curated-metadata">
              <div 
                v-for="field in curatedMetadata" 
                :key="field.id"
                class="curated-field"
                :class="{ 'is-required': field.is_required }"
              >
                <div class="curated-field-header">
                  <h4 class="curated-field-name">
                    {{ field.name }}
                    <span v-if="field.is_required" class="required-indicator">*</span>
                  </h4>
                  <div class="curated-field-badges">
                    <span class="field-type-badge-small">{{ field.type.replace('_', ' ').toLowerCase() }}</span>
                    <span v-if="field.isManual" class="manual-badge-small">✍️ Manual</span>
                    <span v-else-if="field.confidence" class="ai-badge-small">🤖 AI {{ field.confidence }}%</span>
                  </div>
                </div>
                <div class="curated-field-value">
                  {{ field.value }}
                </div>
              </div>
            </div>
          </div>

          <!-- Metadata Fields List (hide if fully curated and not editing) -->
          <div v-if="!isEntityFullyCurated || curationStarted" class="metadata-fields">
            <div 
              v-for="field in metadataFields" 
              :key="field.id" 
              class="metadata-field-card"
              :class="{ 
                'has-ai-suggestion': field.aiSuggestion,
                'has-manual-value': field.manualValue,
                'is-required': field.is_required,
                'active-highlight': activeHighlightId === field.aiSuggestion?.id
              }"
              @click="field.aiSuggestion && activateHighlight(field.aiSuggestion.id)"
            >
              <!-- Field Header -->
              <div class="field-header">
                <div class="field-header-left">
                  <h3 class="field-name">{{ field.name }}</h3>
                  <span v-if="field.is_required" class="required-indicator">*</span>
                </div>
                <div class="field-header-right">
                  <span class="field-type-label">{{ field.type.replace('_', ' ').toLowerCase() }}</span>
                  <!-- Only show AI confidence badge for AI-generated suggestions -->
                  <span v-if="field.showAISuggestion && field.aiSuggestion && field.aiSuggestion.ai_generated !== false && field.aiSuggestion.confidence" class="ai-confidence-badge">
                    🤖 {{ Math.round(field.aiSuggestion.confidence * 100) }}%
                  </span>
                  <span v-if="!curationStarted" class="preview-label">PREVIEW</span>
                </div>
              </div>
                  
              <!-- Pre-Curation Preview (just show field names and types) -->
              <div v-if="!curationStarted" class="field-preview">
                <div class="preview-info">
                  <span class="field-description">{{ field.type.replace('_', ' ').toLowerCase() }} field</span>
                  <span v-if="field.property_options && field.property_options.length" class="options-count">
                    {{ field.property_options.length }} options available
                  </span>
                    </div>
                  </div>

              <!-- Manual Entry Saved (simple display, NO AI elements) -->
              <div v-else-if="curationStarted && field.showAISuggestion && field.aiSuggestion.ai_generated === false" class="manual-saved-section">
                <div class="suggestion-value-container">
                  <div class="suggestion-label">Manual Entry:</div>
                  <div class="suggested-value-display manual-value">{{ renderSuggestionValue(field.aiSuggestion) }}</div>
                </div>
                
                <div class="suggestion-actions">
                  <div class="status-display status-manual">
                    ✓ SAVED
                  </div>
                  <button
                    @click.stop="editSuggestion(field.aiSuggestion)"
                    class="action-btn edit-btn-secondary" 
                  >
                    <span class="btn-icon">✎</span>
                    <span class="btn-text">Edit</span>
                  </button>
                </div>
              </div>
              
              <!-- AI Suggestion Section (ONLY for AI-generated suggestions) -->
              <div v-else-if="curationStarted && field.showAISuggestion && field.aiSuggestion.ai_generated !== false" class="ai-suggestion-section">
                <!-- AI Suggested Value -->
                <div class="suggestion-value-container">
                  <div class="suggestion-label">AI Suggested:</div>
                  <div class="suggested-value-display">{{ renderSuggestionValue(field.aiSuggestion) }}</div>
                </div>

                <!-- AI Reasoning (ONLY for AI suggestions) -->
                <div v-if="field.aiSuggestion.reasoning" class="ai-reasoning">
                  <div class="reasoning-label">AI Reasoning:</div>
                  <div class="reasoning-text">
                    <span v-if="!field.reasoningExpanded && field.aiSuggestion.reasoning.length > 500">
                      {{ field.aiSuggestion.reasoning.substring(0, 500) }}
                      <span class="expand-link" @click.stop="toggleReasoning(field)">... read more</span>
                    </span>
                    <span v-else>
                      {{ field.aiSuggestion.reasoning }}
                      <span v-if="field.reasoningExpanded" class="collapse-link" @click.stop="toggleReasoning(field)"> show less</span>
                    </span>
                  </div>
                </div>

                <!-- AI Actions: Accept/Reject/Edit or Status Badge -->
                <div class="suggestion-actions">
                  <!-- Pending AI Suggestion: Show action buttons -->
                  <template v-if="field.aiSuggestion.status === 'pending'">
                    <button 
                      @click.stop="acceptSuggestion(field.aiSuggestion)"
                      class="action-btn accept-btn" 
                    >
                      <span class="btn-icon">✓</span>
                      <span class="btn-text">Accept</span>
                    </button>
                    <button 
                      @click.stop="rejectSuggestion(field.aiSuggestion)"
                      class="action-btn reject-btn" 
                    >
                      <span class="btn-icon">✕</span>
                      <span class="btn-text">Reject</span>
                    </button>
                    <button
                      @click.stop="editSuggestion(field.aiSuggestion)"
                      class="action-btn edit-btn" 
                    >
                      <span class="btn-icon">✎</span>
                      <span class="btn-text">Edit</span>
                    </button>
                  </template>
                  
                  <!-- Curated AI Suggestion: Show status badge + Edit button -->
                  <template v-else>
                    <div class="status-display" :class="getStatusClass(field.aiSuggestion)">
                      {{ field.aiSuggestion.status === 'accepted' ? '✓ ACCEPTED' : field.aiSuggestion.status.toUpperCase() }}
                    </div>
                    <button
                      @click.stop="editSuggestion(field.aiSuggestion)"
                      class="action-btn edit-btn-secondary" 
                    >
                      <span class="btn-icon">✎</span>
                      <span class="btn-text">Edit</span>
                    </button>
                  </template>
              </div>
          </div>
          
              <!-- Manual Entry Section (only when curation started and field needs manual entry) -->
              <div v-else-if="curationStarted && field.needsManualEntry" class="manual-entry-section">
                <!-- Choice-based fields -->
                <div v-if="isChoiceField(field)" class="field-input">
                  <label>Select Value:</label>
                  <select 
                    v-model="field.manualValue" 
                    @change="onManualValueChange(field)"
                    class="form-select"
                  >
                    <option value="">Choose an option...</option>
                    <option 
                      v-for="option in field.property_options" 
                      :key="option.id" 
                      :value="option.id"
                    >
                      {{ option.name }}
                    </option>
                  </select>
                </div>
                
                <!-- Text and numerical fields -->
                <div v-else class="field-input">
                  <label>Value:</label>
                  <input 
                    v-if="field.type === 'NUMERICAL'"
                    v-model="field.manualValue"
                    @input="onManualValueChange(field)"
                    type="number" 
                    class="form-input"
                    :placeholder="`Enter ${field.name.toLowerCase()}`"
                  >
                  <textarea 
                    v-else
                    v-model="field.manualValue"
                    @input="onManualValueChange(field)"
                    class="form-textarea"
                    rows="3"
                    :placeholder="`Enter ${field.name.toLowerCase()}`"
                  ></textarea>
                </div>
                
                <!-- Manual Entry Actions -->
                <div class="manual-actions">
                  <button 
                    @click="saveManualField(field)"
                    :disabled="!field.manualValue"
                    class="save-btn"
                  >
                    Save
                  </button>
                  <button 
                    @click="clearManualField(field)"
                    :disabled="!field.manualValue"
                    class="clear-btn"
                  >
                    Clear
                  </button>
                </div>
              </div>
                </div>
              </div>
              
            <!-- Bulk Actions (only when curation started and AI suggestions exist) -->
          <div v-if="curationStarted && useAI && aiSuggestions.length > 0" class="bulk-actions">
                <button 
              @click="bulkAcceptAll"
              :disabled="!hasPendingSuggestions"
              class="bulk-btn accept-all-btn"
            >
              Accept All Pending ({{ pendingSuggestionsCount }})
                </button>
                <button 
              @click="bulkRejectAll"
              :disabled="!hasPendingSuggestions"
              class="bulk-btn reject-all-btn"
            >
              Reject All Pending ({{ pendingSuggestionsCount }})
                </button>
              </div>
            </div>
          </div>
    </div>

    <!-- Edit Suggestion Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Edit Metadata Suggestion</h3>
          <button class="modal-close" @click="closeEditModal">&times;</button>
        </div>
        
        <div class="modal-body" v-if="editingSuggestion">
          <div class="edit-field">
            <label>Property: {{ getPropertyName(editingSuggestion.property_id) }}</label>
            <p class="field-type">{{ getPropertyType(editingSuggestion.property_id) }}</p>
          </div>
          
          <!-- Dynamic input based on property type -->
          <div class="edit-input">
            <div v-if="isChoiceProperty(editingSuggestion.property_id)" class="field-input">
              <label>Select Value:</label>
              <select v-model="editingSuggestion.property_option_id" class="form-input">
                <option value="">Select an option...</option>
                <option v-for="opt in getPropertyOptions(editingSuggestion.property_id)" :key="opt.id" :value="opt.id">
                  {{ opt.name }}
                </option>
              </select>
            </div>
            
            <div v-else class="field-input">
              <label>Value:</label>
              <input 
                v-if="isNumericalProperty(editingSuggestion.property_id)"
                v-model="editingSuggestion.custom_value" 
                type="number" 
                class="form-input"
              >
              <textarea 
                v-else
                v-model="editingSuggestion.custom_value" 
                class="form-input" 
                rows="3"
              ></textarea>
            </div>
          </div>
          
          <div class="edit-notes">
            <label>Curator Notes:</label>
            <textarea 
              v-model="editingSuggestion.curator_note" 
              class="form-input" 
              rows="2"
              placeholder="Add notes about this edit..."
            ></textarea>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeEditModal">Cancel</button>
          <button class="btn btn-primary" @click="saveEditedSuggestion" :disabled="!isEditValid">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { getSources, getProperties } from './api'

export default {
  name: 'App',
  data() {
    return {
      // Core data
      sources: [],
      properties: [],
      selectedSourceId: null,
      selectedEntityId: null,
      selectedEntity: null,
      selectedSource: null,
      
      // UI state
      useAI: false,
      isLoading: false,
      showUserMenu: false,
      confidenceThreshold: 70,
      curationStarted: false,
      
      // Content data
      scrapedContent: {
        pages: [],
        total_pages: 0,
        scraped_at: null
      },
      currentPageIndex: 0,
      
      // Suggestions and manual data
      aiSuggestions: [],
      manualValues: {},
      activeHighlightId: null,
      
      // Edit modal
      showEditModal: false,
      editingSuggestion: null,
      
      // Status tracking
      statusText: 'Ready',
      statusClass: 'status-ready'
    }
  },
  
  computed: {
    // Filtered editions based on selected source
    filteredEditions() {
      if (!this.selectedSourceId) {
        return []
      }
      const source = this.sources.find(s => s.id === this.selectedSourceId)
      return source ? source.editions : []
    },
    
    currentPage() {
      return this.scrapedContent.pages[this.currentPageIndex] || null
    },
    
    metadataFields() {
      if (!this.properties.length) return []
      
      const fields = this.properties.map(property => {
        // Find suggestion for this property (could be AI-generated or manual)
        const suggestion = this.aiSuggestions.find(s => s.property_id === property.id)
        
        // Determine if this field should show AI suggestion or manual entry
        let showAISuggestion = false
        let needsManualEntry = false
        
        if (!this.curationStarted) {
          // BEFORE Start is clicked: show nothing interactive
          showAISuggestion = false
          needsManualEntry = false
        } else if (suggestion) {
          // AFTER Start is clicked AND has saved/generated suggestion
          
          // Manual entries (ai_generated=false) are always accepted and finalized
          if (suggestion.ai_generated === false) {
            showAISuggestion = true
            needsManualEntry = false
          } 
          // AI suggestions with pending status: show if confidence high enough
          else if (suggestion.status === 'pending') {
            const confidence = (suggestion.confidence || 0) * 100
            showAISuggestion = confidence >= this.confidenceThreshold
            needsManualEntry = !showAISuggestion
          } 
          // AI suggestions that have been curated: show with status
          else {
            showAISuggestion = true
            needsManualEntry = false
          }
        } else {
          // AFTER Start, no suggestion exists: show manual entry
          needsManualEntry = true
          showAISuggestion = false
        }
        
        return {
          ...property,
          aiSuggestion: showAISuggestion ? suggestion : null,
          manualValue: this.manualValues[property.id] || '',
          showAISuggestion,
          needsManualEntry,
          isInteractive: this.curationStarted,
          reasoningExpanded: false  // For expand/collapse functionality
        }
      })
      
      // Sort fields: AI suggestions first, then manual fields, then empty fields
      return fields.sort((a, b) => {
        // AI suggestions first (highest priority)
        if (a.showAISuggestion && !b.showAISuggestion) return -1
        if (!a.showAISuggestion && b.showAISuggestion) return 1
        
        // Manual values second
        if (a.manualValue && !b.manualValue) return -1
        if (!a.manualValue && b.manualValue) return 1
        
        // Required fields before optional
        if (a.is_required && !b.is_required) return -1
        if (!a.is_required && b.is_required) return 1
        
        // Finally, sort by property ID for consistency
            return a.id - b.id
      })
    },
    
    hasPendingSuggestions() {
      return this.pendingSuggestionsCount > 0
    },
    
    pendingSuggestionsCount() {
      if (!this.curationStarted || !this.useAI) return 0
      
      // Only count suggestions that meet the confidence threshold
      return this.aiSuggestions.filter(s => {
        const confidence = (s.confidence || 0) * 100
        return s.status === 'pending' && confidence >= this.confidenceThreshold
      }).length
    },
    
    // Check if entity is fully curated (all fields have accepted/saved values)
    isEntityFullyCurated() {
      if (!this.selectedEntityId || !this.properties.length) return false
      
      // Check if we have a suggestion (accepted/saved) for every property
      const completedFields = this.aiSuggestions.filter(s => 
        s.ai_generated === false ||  // Manual entries are always complete
        s.status === 'accepted' || 
        s.status === 'edited'
      ).length
      
      return completedFields === this.properties.length && completedFields > 0
    },
    
    // Get curated data for read-only view
    curatedMetadata() {
      if (!this.isEntityFullyCurated) return []
      
      return this.properties.map(property => {
        const suggestion = this.aiSuggestions.find(s => s.property_id === property.id)
        
        // Get the display value
        let displayValue = 'N/A'
        if (suggestion) {
          if (suggestion.property_option_id) {
            const option = property.property_options?.find(o => o.id === suggestion.property_option_id)
            displayValue = option ? option.name : 'Unknown option'
          } else if (suggestion.custom_value !== null && suggestion.custom_value !== undefined) {
            displayValue = suggestion.custom_value
          }
        }
        
        return {
          ...property,
          value: displayValue,
          suggestion: suggestion,
          isManual: suggestion?.ai_generated === false,
          confidence: suggestion?.confidence ? Math.round(suggestion.confidence * 100) : null
        }
      })
    },
    
    filteredAISuggestions() {
      if (!this.useAI || !this.curationStarted) return []
      
      // Filter AI suggestions by confidence threshold
      return this.aiSuggestions.filter(s => {
        const confidence = (s.confidence || 0) * 100
        return confidence >= this.confidenceThreshold
      })
    },
    
    isEditValid() {
      if (!this.editingSuggestion) return false
      
      const property = this.properties.find(p => p.id === this.editingSuggestion.property_id)
      if (!property) return false
      
      if (['MULTIPLE_CHOICE', 'SINGLE_CHOICE', 'BINARY'].includes(property.type)) {
        return this.editingSuggestion.property_option_id && this.editingSuggestion.property_option_id !== ''
      } else {
        return this.editingSuggestion.custom_value && this.editingSuggestion.custom_value.toString().trim() !== ''
      }
    },
    
    highlightedContent() {
      if (!this.currentPage || !this.currentPage.text_content) return ''
      if (!this.aiSuggestions || !Array.isArray(this.aiSuggestions)) return this.currentPage.text_content
      
      let content = this.currentPage.text_content
      
      // Get AI suggestions with evidence for highlighting
      const aiSuggestions = this.aiSuggestions.filter(s => 
        s.evidence && s.page_url === this.currentPage.url
      )
      
      if (aiSuggestions.length === 0) return content
      
      // Create highlighted content with evidence
      let replacementCounter = 0
      
      for (let i = 0; i < aiSuggestions.length; i++) {
        const suggestion = aiSuggestions[i]
        const evidence = suggestion.evidence
        
        if (!evidence) continue
        
        // Get the evidence text
        let evidenceText = ''
        if (typeof evidence === 'string') {
          evidenceText = evidence
        } else if (evidence.content) {
          evidenceText = evidence.content
        } else {
          continue
        }
        
        if (!evidenceText || !content.includes(evidenceText)) continue
        
        const propertyName = this.getPropertyName(suggestion.property_id)
        const isActive = this.activeHighlightId === suggestion.id
        
        // Determine highlight color
        let highlightColor = isActive ? '#8B5CF6' : '#F0E6FF'
        
        // Create a unique placeholder
        const placeholder = `__HIGHLIGHT_${suggestion.id}_${replacementCounter}__`
        content = content.replace(evidenceText, placeholder)
        
        // Replace with highlighted content
        content = content.replace(
          placeholder,
          `<span class="ai-highlight" 
                 data-suggestion-id="${suggestion.id}"
                 style="background-color: ${highlightColor}; padding: 2px 4px; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;" 
                 title="${propertyName}: ${evidenceText}"
                 onclick="window.activateHighlight && window.activateHighlight(${suggestion.id})">${evidenceText}</span>`
        )
        
        replacementCounter++
      }
      
      return content
    }
  },
  
  methods: {
    async fetchInitialData() {
      try {
        this.sources = await getSources()
        this.properties = await getProperties()
        console.log('Loaded sources:', this.sources.length)
        console.log('Loaded properties:', this.properties.length)
      } catch (error) {
        console.error('Failed to fetch initial data:', error)
      }
    },
    
    // Handle source selection change
    onSourceChange() {
      // Reset entity selection when source changes
      this.selectedEntityId = null
      this.selectedEntity = null
      this.resetState()
      
      // Update selected source
      const source = this.sources.find(s => s.id === this.selectedSourceId)
      this.selectedSource = source || null
      
      console.log(`Source changed to: ${source ? source.name : 'None'}`)
    },
    
    async onEntityChange() {
      if (!this.selectedEntityId) {
        this.resetState()
        return
      }
      
      // Find the selected entity and source
      for (const source of this.sources) {
        const entity = source.editions.find(e => e.id === parseInt(this.selectedEntityId))
        if (entity) {
          this.selectedEntity = entity
          this.selectedSource = source
          break
        }
      }
      
      if (!this.selectedEntity) {
        console.error('Entity not found:', this.selectedEntityId)
        return
      }
      
      console.log('Selected entity:', this.selectedEntity.entity_name)
      console.log('Selected source:', this.selectedSource.name)
      
      // Reset curation state when entity changes (user must click Start)
      this.curationStarted = false
      this.aiSuggestions = []
      this.manualValues = {}
      
      // Start scraping immediately (but don't start curation yet)
      await this.scrapeContent()
      
      // Load any previously saved suggestions for this entity
      await this.loadSavedSuggestions()
    },
    
    async loadSavedSuggestions() {
      if (!this.selectedEntityId) return
      
      try {
        // Fetch any existing suggestions for this entity from the backend
        const response = await axios.get('/api/suggestions', {
          params: {
            edition_id: this.selectedEntityId,
            source_id: this.selectedSource?.id
          }
        })
        
        if (response.data && response.data.length > 0) {
          // Load saved suggestions BUT don't auto-start curation
          this.aiSuggestions = response.data
          
          // Calculate completion stats (SAME logic as updateCurationProgress)
          const completed = response.data.filter(s => 
            s.ai_generated === false ||  // Manual entries count as complete
            s.status === 'accepted' || 
            s.status === 'rejected' || 
            s.status === 'edited'
          ).length
          const total = this.properties.length
          
          // Update status to show work has been done
          if (completed === total) {
            this.statusText = `✓ All ${total} fields complete - Click Resume to view`
            this.statusClass = 'status-complete'
          } else if (completed > 0) {
            this.statusText = `${completed}/${total} fields curated - Click Resume to continue`
            this.statusClass = 'status-info'
          } else {
            this.statusText = `${response.data.length} suggestions loaded - Click Resume to review`
            this.statusClass = 'status-info'
          }
          
          console.log(`Loaded ${response.data.length} previously saved suggestions for entity ${this.selectedEntityId} (${completed}/${total} complete)`)
        } else {
          this.statusText = 'Ready to start'
          this.statusClass = 'status-ready'
        }
      } catch (error) {
        console.error('Failed to load saved suggestions:', error)
        // Don't show error to user - it's fine if there are no saved suggestions
      }
    },
    
    async onAIToggleChange() {
      // Reset curation state when AI mode changes
      this.curationStarted = false
      
      if (this.selectedEntityId) {
        // Re-scrape with new AI setting
        await this.scrapeContent()
        // Reload saved suggestions after scraping
        await this.loadSavedSuggestions()
      }
    },
    
    resumeEditing() {
      // Allow editing of fully curated entity
      this.curationStarted = true
      this.statusText = 'Editing curated metadata'
      this.statusClass = 'status-in-progress'
      this.updateCurationProgress()
    },
    
    async startCuration() {
      if (!this.selectedEntityId || !this.scrapedContent.pages.length) return
      
      // If already has suggestions, just start curation mode
      if (this.aiSuggestions.length > 0) {
        this.curationStarted = true
        this.statusText = `Curation active - ${this.aiSuggestions.length} suggestions loaded`
        this.statusClass = 'status-success'
        return
      }
      
      this.isLoading = true
      this.statusText = this.useAI ? 'Generating AI suggestions...' : 'Preparing manual curation...'
      this.statusClass = 'status-loading'
      
      try {
        if (this.useAI) {
          // Generate NEW AI suggestions only if none exist
          const response = await axios.post(`/api/entities/${this.selectedEntityId}/scrape`, {
            use_ai: true
        })
        
        if (response.data.success) {
            this.aiSuggestions = response.data.suggestions.items || []
            console.log(`AI suggestions generated: ${this.aiSuggestions.length}`)
          }
        }
        
        // Start curation mode
        this.curationStarted = true
        this.statusText = this.useAI ? 
          `AI curation active - ${this.aiSuggestions.length} suggestions generated` :
          'Manual curation active'
        this.statusClass = 'status-success'
        
      } catch (error) {
        console.error('Failed to start curation:', error)
        this.statusText = 'Failed to start curation'
        this.statusClass = 'status-error'
        alert(`Failed to start curation: ${error.response?.data?.error || error.message}`)
      } finally {
        this.isLoading = false
      }
    },
    
    async scrapeContent() {
      if (!this.selectedEntityId) return
      
      this.isLoading = true
      this.statusText = 'Scraping content...'
      this.statusClass = 'status-loading'
      
      try {
        // Always scrape without AI initially - AI suggestions will be generated when curation starts
        const response = await axios.post(`/api/entities/${this.selectedEntityId}/scrape`, {
          use_ai: false
        })
        
        if (response.data.success) {
          this.scrapedContent = response.data.scraped_content
          this.currentPageIndex = 0
          
          // Clear previous state
          this.aiSuggestions = []
          this.manualValues = {}
          
          this.statusText = `Scraped ${this.scrapedContent.total_pages} pages - Ready to start curation`
          this.statusClass = 'status-success'
          
          console.log('Scraping completed:', {
            pages: this.scrapedContent.total_pages,
            ready_for_curation: true
          })
        }
      } catch (error) {
        console.error('Scraping failed:', error)
        this.statusText = 'Scraping failed'
        this.statusClass = 'status-error'
        alert(`Scraping failed: ${error.response?.data?.error || error.message}`)
      } finally {
        this.isLoading = false
      }
    },
    
    resetState() {
        this.selectedEntity = null
      this.selectedSource = null
      this.scrapedContent = { pages: [], total_pages: 0, scraped_at: null }
      this.aiSuggestions = []
      this.manualValues = {}
        this.currentPageIndex = 0
      this.activeHighlightId = null
      this.curationStarted = false
      this.statusText = 'Ready'
      this.statusClass = 'status-ready'
    },
    
    // Navigation methods
    nextPage() {
      if (this.currentPageIndex < this.scrapedContent.pages.length - 1) {
        this.currentPageIndex++
        this.activeHighlightId = null
      }
    },
    
    previousPage() {
      if (this.currentPageIndex > 0) {
        this.currentPageIndex--
        this.activeHighlightId = null
      }
    },
    
    // Property helper methods
    getPropertyName(propertyId) {
      const prop = this.properties.find(p => p.id === propertyId)
      return prop ? prop.name : `Property ${propertyId}`
    },
    
    getPropertyType(propertyId) {
      const prop = this.properties.find(p => p.id === propertyId)
      return prop ? prop.type : 'Unknown'
    },
    
    isChoiceField(field) {
      return ['MULTIPLE_CHOICE', 'SINGLE_CHOICE', 'BINARY'].includes(field.type)
    },
    
    isChoiceProperty(propertyId) {
      const prop = this.properties.find(p => p.id === propertyId)
      return prop && ['MULTIPLE_CHOICE', 'SINGLE_CHOICE', 'BINARY'].includes(prop.type)
    },
    
    isNumericalProperty(propertyId) {
      const prop = this.properties.find(p => p.id === propertyId)
      return prop && prop.type === 'NUMERICAL'
    },
    
    getPropertyOptions(propertyId) {
      const prop = this.properties.find(p => p.id === propertyId)
      return prop ? prop.property_options || [] : []
    },
    
    renderSuggestionValue(suggestion) {
      if (suggestion.custom_value) return suggestion.custom_value
      const prop = this.properties.find(p => p.id === suggestion.property_id)
      if (!prop) return ''
      const option = prop.property_options?.find(o => o.id === suggestion.property_option_id)
      return option ? option.name : ''
    },
    
    toggleReasoning(field) {
      // Toggle the reasoning expanded state
      field.reasoningExpanded = !field.reasoningExpanded
      this.$forceUpdate() // Force re-render
    },
    
    highlightText(text) {
      // Apply evidence highlighting to a text snippet (for structured content)
      if (!text || !this.aiSuggestions || !this.currentPage) return text
      
      let highlighted = text
      let replacementCounter = 0
      
      const aiSugs = this.aiSuggestions.filter(s => 
        s.evidence && 
        s.page_url === this.currentPage.url
      )
      
      for (const sug of aiSugs) {
        const evidenceText = typeof sug.evidence === 'string' ? sug.evidence : sug.evidence.content
        
        if (!evidenceText || !highlighted.includes(evidenceText)) continue
        
        const propertyName = this.getPropertyName(sug.property_id)
        const isActive = this.activeHighlightId === sug.id
        
        // Purple color scheme: active = dark purple, inactive = light purple
        let highlightColor = isActive ? '#8B5CF6' : '#F0E6FF'
        
        // Create unique placeholder
        const placeholder = `__HIGHLIGHT_${sug.id}_${replacementCounter}__`
        replacementCounter++
        
        // Replace with placeholder first
        highlighted = highlighted.replace(
          evidenceText,
          placeholder
        )
        
        // Then replace placeholder with styled span (same as main highlighting system)
        highlighted = highlighted.replace(
          placeholder,
          `<span class="ai-highlight" 
                 data-suggestion-id="${sug.id}"
                 style="background-color: ${highlightColor}; padding: 2px 4px; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;" 
                 title="${propertyName}: ${evidenceText.substring(0, 100)}"
                 onclick="window.activateHighlight && window.activateHighlight(${sug.id})">${evidenceText}</span>`
        )
      }
      
      return highlighted
    },
    
    getEntityProgressText() {
      // Show progress text for current selected entity
      if (!this.aiSuggestions.length) return ''
      
      // SAME completion logic as updateCurationProgress
      const completed = this.aiSuggestions.filter(s => 
        s.ai_generated === false ||  // Manual entries count as complete
        s.status === 'accepted' || 
        s.status === 'rejected' || 
        s.status === 'edited'
      ).length
      const total = this.properties.length
      
      if (completed === total) {
        return `✓ All ${total} fields completed`
      } else if (completed > 0) {
        return `📊 Progress: ${completed}/${total} fields curated`
      } else {
        return `📋 ${this.aiSuggestions.length} suggestions loaded`
      }
    },
    
    getStatusClass(suggestion) {
      switch (suggestion.status) {
        case 'accepted': return 'status-accepted'
        case 'rejected': return 'status-rejected'
        case 'edited': return 'status-edited'
        default: return 'status-pending'
      }
    },
    
    // AI Suggestion methods
    async acceptSuggestion(suggestion) {
      await this.curateSuggestion(suggestion.id, 'accept')
    },
    
    async rejectSuggestion(suggestion) {
      await this.curateSuggestion(suggestion.id, 'reject')
    },
    
    editSuggestion(suggestion) {
      this.editingSuggestion = { ...suggestion }
      this.showEditModal = true
    },
    
    async curateSuggestion(suggestionId, action) {
      try {
        const response = await axios.post(`/api/suggestions/${suggestionId}/curate`, {
          action: action,
          note: `Curator ${action}ed this suggestion`,
          user_id: 'curator_' + Date.now()
        })
        
        if (response.data.success) {
          const index = this.aiSuggestions.findIndex(s => s.id === suggestionId)
          if (index !== -1) {
            this.aiSuggestions[index] = response.data.suggestion
          }
          
          // Update progress status after each action
          this.updateCurationProgress()
          
          console.log(`${action}ed suggestion ${suggestionId}`)
        }
      } catch (error) {
        console.error(`Failed to ${action} suggestion:`, error)
        alert(`Failed to ${action} suggestion: ${error.response?.data?.error || error.message}`)
      }
    },
    
    updateCurationProgress() {
      // Update status text with current progress
      // Count: accepted/rejected/edited AI suggestions + ALL manual entries
      const completed = this.aiSuggestions.filter(s => 
        s.ai_generated === false ||  // Manual entries always count as complete
        s.status === 'accepted' || 
        s.status === 'rejected' || 
        s.status === 'edited'
      ).length
      const total = this.properties.length
      
      if (completed === total) {
        this.statusText = `✓ All ${total} fields complete!`
        this.statusClass = 'status-complete'
      } else if (completed > 0) {
        this.statusText = `${completed}/${total} fields curated`
        this.statusClass = 'status-in-progress'
      } else {
        this.statusText = 'Curation active'
        this.statusClass = 'status-success'
      }
    },
    
    async bulkAcceptAll() {
      const pendingSuggestions = this.aiSuggestions.filter(s => s.status === 'pending')
      try {
        await Promise.all(pendingSuggestions.map(s => this.curateSuggestion(s.id, 'accept')))
        console.log(`Accepted ${pendingSuggestions.length} suggestions`)
      } catch (error) {
        console.error('Bulk accept failed:', error)
      }
    },
    
    async bulkRejectAll() {
      const pendingSuggestions = this.aiSuggestions.filter(s => s.status === 'pending')
      try {
        await Promise.all(pendingSuggestions.map(s => this.curateSuggestion(s.id, 'reject')))
        console.log(`Rejected ${pendingSuggestions.length} suggestions`)
      } catch (error) {
        console.error('Bulk reject failed:', error)
      }
    },
    
    // Manual entry methods
    onManualValueChange(field) {
      this.manualValues[field.id] = field.manualValue
      console.log(`Manual value changed for field ${field.name}:`, field.manualValue)
    },
    
    async saveManualField(field) {
      const value = field.manualValue
      if (!value) return
      
      try {
            const payload = {
          source_id: this.selectedSource.id,
          edition_id: this.selectedEntity.id,
          property_id: field.id,
              evidence: {
            content: `Manual entry by curator`,
                source_url: window.location.href,
            confidence: 1.0,
                extraction_method: 'manual'
              }
            }
            
        if (this.isChoiceField(field)) {
                payload.property_option_id = value
              } else {
                payload.custom_value = value
        }
        
        const response = await axios.post('/api/manual-metadata', payload)
        
        if (response.data.success) {
          console.log(`Saved manual field ${field.name}`)
          
          // Add the saved suggestion to our list
          if (response.data.suggestion) {
            const existingIndex = this.aiSuggestions.findIndex(s => s.property_id === field.id)
            if (existingIndex !== -1) {
              // Update existing
              this.aiSuggestions[existingIndex] = response.data.suggestion
            } else {
              // Add new
              this.aiSuggestions.push(response.data.suggestion)
            }
          }
          
          // Update progress
          this.updateCurationProgress()
          
          // Clear the manual input field
          this.clearManualField(field)
          
          // No popup - silent save with visual feedback in status
          console.log(`✅ Saved ${field.name} successfully`)
        }
      } catch (error) {
        console.error('Failed to save manual field:', error)
        alert(`Failed to save ${field.name}: ${error.response?.data?.error || error.message}`)
      }
    },
    
    clearManualField(field) {
      field.manualValue = ''
      this.manualValues[field.id] = ''
     },
     
     // Edit modal methods
     closeEditModal() {
       this.showEditModal = false
       this.editingSuggestion = null
     },
     
     async saveEditedSuggestion() {
       if (!this.editingSuggestion) return
       
       try {
         const payload = {
           note: this.editingSuggestion.curator_note || 'Edited by curator'
         }
         
         const property = this.properties.find(p => p.id === this.editingSuggestion.property_id)
         if (property) {
          if (['MULTIPLE_CHOICE', 'SINGLE_CHOICE', 'BINARY'].includes(property.type)) {
             payload.property_option_id = this.editingSuggestion.property_option_id
           } else {
             payload.custom_value = this.editingSuggestion.custom_value
           }
         }
         
         const response = await axios.put(`/api/suggestions/${this.editingSuggestion.id}/edit`, payload)
         
         if (response.data.success) {
          const index = this.aiSuggestions.findIndex(s => s.id === this.editingSuggestion.id)
           if (index !== -1) {
            this.aiSuggestions[index] = response.data.suggestion
           }
           
           // Update progress after edit
           this.updateCurationProgress()
           
           console.log('Suggestion edited successfully')
           this.closeEditModal()
         }
       } catch (error) {
         console.error('Failed to edit suggestion:', error)
        alert(`Failed to edit suggestion: ${error.response?.data?.error || error.message}`)
      }
    },
    
    // Highlighting methods
    activateHighlight(suggestionId) {
      this.activeHighlightId = this.activeHighlightId === suggestionId ? null : suggestionId
    },
    
    // Utility methods
    formatTime(timestamp) {
      try {
        return new Date(timestamp).toLocaleTimeString()
      } catch {
        return ''
      }
    },
    
    // Header methods
    showSettings() {
      this.showUserMenu = false
      alert('Settings panel would open here.')
    },
    
    showHelp() {
      this.showUserMenu = false
      alert('Help & Documentation would open here.')
    },
    
    logout() {
      this.showUserMenu = false
      if (confirm('Are you sure you want to logout?')) {
        this.resetState()
        this.selectedEntityId = null
        this.curationStarted = false
        alert('Logged out successfully.')
      }
    }
  },
  
  async created() {
    await this.fetchInitialData()
    
    // Set up global highlight function for content
    window.activateHighlight = (suggestionId) => {
      this.activateHighlight(suggestionId)
    }
    
    // Close user menu when clicking outside
    document.addEventListener('click', (event) => {
      if (this.showUserMenu && !event.target.closest('.user-profile') && !event.target.closest('.user-dropdown')) {
        this.showUserMenu = false
      }
    })
  },
  
  beforeDestroy() {
    delete window.activateHighlight
  }
}
</script>

<style>
/* Reset and base styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  line-height: 1.6;
  color: #333;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  background-attachment: fixed;
}

#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header styles */
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.app-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.version-badge {
  background: rgba(255,255,255,0.2);
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-greeting {
  font-weight: 500;
  font-size: 0.9rem;
}

.user-role {
  font-size: 0.8rem;
  opacity: 0.8;
}

.user-menu-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.25rem;
  transition: background-color 0.2s;
}

.user-menu-btn:hover {
  background: rgba(255,255,255,0.1);
}

.user-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  color: #333;
  border-radius: 0.5rem;
  box-shadow: 0 10px 25px rgba(0,0,0,0.15);
  min-width: 200px;
  z-index: 1000;
  margin-top: 0.5rem;
}

.dropdown-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background-color 0.2s;
}

.dropdown-item:hover {
  background: #f8f9fa;
}

.dropdown-item.logout {
  color: #dc3545;
}

.dropdown-divider {
  height: 1px;
  background: #dee2e6;
  margin: 0.5rem 0;
}

/* Control Panel - Rock Solid Layout */
.control-panel {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  padding: 1.5rem 2rem;
  min-height: 120px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.control-grid {
  display: grid;
  grid-template-columns: 520px 220px 360px 180px auto; /* selection, ai, confidence, action, status */
  gap: 1.5rem;
  align-items: center;
  max-width: 1600px;
  margin: 0 auto;
  min-height: 100px; /* Taller for better visual balance */
}

/* Fixed column widths */
.entity-group { width: 520px; }
.ai-group { width: 220px; height: 72px; justify-content: center; }
.confidence-group { width: 480px; height: 72px; justify-content: center; overflow: hidden; }
.action-group { width: 260px; height: 72px; justify-content: center; }
.status-group { min-width: 220px; height: 72px; justify-content: center; align-items: center; white-space: nowrap; justify-self: end; }

/* Confidence controls spacing */
.confidence-controls { gap: 0.25rem; }

/* Slider track styling to avoid thick black bar */
.slider-input::-webkit-slider-runnable-track { height: 4px; border-radius: 2px; background: #e5e7eb; }
.slider-input::-moz-range-track { height: 4px; border-radius: 2px; background: #e5e7eb; }

.status-indicator { white-space: nowrap; }

.entity-select {
  padding: 0.875rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 0.75rem;
  font-size: 1rem;
  width: 520px; /* fixed desktop width for stability */
  min-width: 520px;
  max-width: 100%;
  background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%);
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.entity-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  background: white;
}

.entity-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f5f5f5;
}

.entity-progress-info {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: linear-gradient(135deg, #f3e5f5 0%, #faf5ff 100%);
  border-left: 3px solid #8B5CF6;
  border-radius: 0.375rem;
  font-size: 0.85rem;
  color: #6b21a8;
  font-weight: 600;
}

.ai-toggle-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.ai-checkbox {
  width: 1.2rem;
  height: 1.2rem;
}

.ai-toggle-text {
  font-weight: 500;
}

.ai-info {
  font-size: 0.8rem;
  color: #666;
  font-style: italic;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; opacity: 0.75;
}

/* Confidence threshold slider */
.slider-input {
  width: 100%;
  margin: 0.25rem 0;
  height: 4px; /* slimmer */
  border-radius: 2px;
  background: #e5e7eb;
  outline: none;
  -webkit-appearance: none;
}

.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transition: all 0.2s ease;
}

.slider-input::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.slider-input::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.confidence-info {
  font-size: 0.8rem;
  color: #666;
  font-style: italic;
  margin-top: 0.25rem;
}

/* Start curation button */
.start-curation-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 200px;
}

.start-curation-btn.ai-mode {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.start-curation-btn.ai-mode:hover:not(:disabled) {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.start-curation-btn.manual-mode {
  background: linear-gradient(135deg, #9c27b0 0%, #673ab7 100%);
  color: white;
}

.start-curation-btn.manual-mode:hover:not(:disabled) {
  background: linear-gradient(135deg, #8e24aa 0%, #5e35b1 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(156, 39, 176, 0.3);
}

.start-curation-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

.curation-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  font-weight: 500;
  color: #2e7d32;
}

.status-icon {
  font-size: 1.1rem;
}

.icon-img {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.info-icon-img {
  width: 14px;
  height: 14px;
  object-fit: contain;
  margin-right: 0.5rem;
}

.status-group {
  margin-left: auto;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: 500;
  white-space: nowrap; /* keep pill in single line */
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-ready {
  background: #e3f2fd;
  color: #1976d2;
}

.status-ready .status-dot {
  background: #1976d2;
}

.status-loading {
  background: #fff3e0;
  color: #f57c00;
}

.status-loading .status-dot {
  background: #f57c00;
  animation: pulse 1.5s infinite;
}

.status-success {
  background: #e8f5e8;
  color: #2e7d32;
}

.status-success .status-dot {
  background: #2e7d32;
}

.status-error {
  background: #ffebee;
  color: #c62828;
}

.status-error .status-dot {
  background: #c62828;
}

.status-info {
  background: #f3e5f5;
  color: #8B5CF6;
}

.status-info .status-dot {
  background: #8B5CF6;
}

.status-in-progress {
  background: #fff8e1;
  color: #f57c00;
}

.status-in-progress .status-dot {
  background: #f57c00;
  animation: pulse 1.5s infinite;
}

.status-complete {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-complete .status-dot {
  background: #2e7d32;
  animation: none;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Loading indicator */
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1rem;
  padding: 1.25rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e3f2fd 100%);
  border-radius: 0.75rem;
  border: 1px solid #e3f2fd;
  box-shadow: 0 2px 8px rgba(33, 150, 243, 0.1);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e0e0e0;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  box-shadow: 0 0 10px rgba(102, 126, 234, 0.2);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: #666;
  font-style: italic;
}

/* Main content */
.main-content {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 1.5rem;
  padding: 1.5rem;
  max-width: 1600px;
  margin: 0 auto;
  flex: 1;
  min-height: 0; /* Allow flex children to shrink */
  overflow: hidden;
  height: calc(100vh - 160px);
}

.content-panel, .metadata-panel {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  border: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.panel-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-radius: 0.75rem 0.75rem 0 0;
}

.panel-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.content-stats, .metadata-stats {
  font-size: 0.9rem;
  color: #666;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.field-count {
  background: #f0f0f0;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
}

.scraped-time {
  font-size: 0.8rem;
  opacity: 0.8;
}

/* Empty state */
.empty-state {
  padding: 4rem 2rem;
  text-align: center;
  color: #666;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  opacity: 0.6;
  filter: grayscale(0.3);
  display: flex;
  justify-content: center;
  align-items: center;
}

.empty-icon .icon-img {
  width: 64px;
  height: 64px;
  opacity: 0.6;
  filter: grayscale(0.3);
}

.empty-state h3 {
  margin-bottom: 0.75rem;
  color: #333;
  font-size: 1.25rem;
  font-weight: 600;
}

.empty-state p {
  font-size: 1rem;
  line-height: 1.6;
  max-width: 400px;
  margin: 0 auto;
}

/* Content display */
.content-display {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.page-navigation {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #fafafa 0%, #ffffff 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-btn {
  padding: 0.6rem 1.2rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.nav-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.page-counter {
  font-weight: 500;
  color: #666;
}

.page-content {
  padding: 1.5rem;
  flex: 1;
  overflow-y: auto;
}

.page-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #333;
}

.page-url {
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 1rem;
  word-break: break-all;
}

.content-text {
  line-height: 1.8;
  color: #444;
  font-size: 0.95rem;
  text-align: justify;
  padding: 1rem;
  background: #fafafa;
  border-radius: 0.5rem;
  border: 1px solid #f0f0f0;
  max-height: 500px;
  overflow-y: auto;
}

.ai-highlight {
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 2px 4px;
  border-radius: 3px;
}

.ai-highlight:hover {
  background-color: #A78BFA !important;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
}

/* Structured Page Content */
.structured-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-height: 500px;
  overflow-y: auto;
  padding: 1rem;
  background: #fafafa;
  border-radius: 0.5rem;
}

.page-navigation-bar {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  padding: 0.75rem 1rem;
  border-radius: 0.375rem;
  border-left: 4px solid #2196f3;
  font-size: 0.85rem;
  color: #1565c0;
}

.nav-label {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.nav-content {
  color: #666;
  line-height: 1.6;
}

.page-headers {
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 1rem;
  margin-bottom: 1rem;
}

.main-header {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 0.5rem 0;
  line-height: 1.3;
}

.sub-header {
  font-size: 1.3rem;
  font-weight: 600;
  color: #444;
  margin: 0.25rem 0 0 0;
  line-height: 1.4;
}

.main-content-sections {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.content-section {
  background: white;
  padding: 1.25rem;
  border-radius: 0.5rem;
  border: 1px solid #e8e8e8;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 1rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e0e0e0;
}

.section-paragraphs {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-paragraph {
  line-height: 1.8;
  color: #333;
  margin: 0;
  text-align: justify;
}

.section-lists {
  margin: 1rem 0;
}

.section-list {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.section-list li {
  line-height: 1.8;
  color: #444;
  margin: 0.25rem 0;
}

.page-footer {
  background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
  padding: 0.75rem 1rem;
  border-radius: 0.375rem;
  border-top: 2px solid #d0d0d0;
  font-size: 0.85rem;
  margin-top: auto;
}

.footer-label {
  font-weight: 600;
  color: #666;
  margin-bottom: 0.25rem;
}

.footer-content {
  color: #888;
  line-height: 1.6;
}

/* Metadata content */
.metadata-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.mode-indicator {
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-bottom: 1px solid #eee;
  font-weight: 500;
}

.ai-mode {
  background: #e3f2fd;
  color: #1976d2;
}

.manual-mode {
  background: #f3e5f5;
  color: #7b1fa2;
}

.mode-icon {
  font-size: 1.2rem;
}

.threshold-info {
  margin-left: auto;
  font-size: 0.8rem;
  opacity: 0.8;
}

/* Pre-curation info */
.pre-curation-info {
  padding: 1rem 1.5rem;
  background: #fff3e0;
  color: #f57c00;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-bottom: 1px solid #eee;
  font-weight: 500;
}

.info-icon {
  font-size: 1.2rem;
}

/* Field preview styles */
.field-preview {
  padding: 1.25rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #f0f0f0 100%);
  border-radius: 0.75rem;
  border: 2px dashed #d0d0d0;
  transition: all 0.3s ease;
}

.field-preview:hover {
  border-color: #b0b0b0;
  background: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
}

/* Curated View Styles */
.curated-view {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-radius: 1rem;
  padding: 2rem;
  margin-bottom: 1.5rem;
  border: 2px solid #86efac;
}

.curated-header {
  margin-bottom: 1.5rem;
  text-align: center;
}

.curated-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.check-icon {
  font-size: 2rem;
  color: #16a34a;
  background: white;
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(22, 163, 74, 0.2);
}

.curated-title h3 {
  margin: 0;
  color: #15803d;
  font-size: 1.5rem;
}

.curated-subtitle {
  color: #166534;
  margin: 0;
  font-size: 0.95rem;
}

.curated-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 2rem;
}

.btn-resume,
.btn-ai-recurate {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-resume {
  background: #3b82f6;
  color: white;
}

.btn-resume:hover {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-ai-recurate {
  background: #8b5cf6;
  color: white;
}

.btn-ai-recurate:hover {
  background: #7c3aed;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.btn-icon {
  font-size: 1.1rem;
}

.curated-metadata {
  display: grid;
  gap: 1rem;
}

.curated-field {
  background: white;
  border-radius: 0.75rem;
  padding: 1.25rem;
  border: 1px solid #d1d5db;
  transition: all 0.2s ease;
}

.curated-field:hover {
  border-color: #9ca3af;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.curated-field.is-required {
  border-left: 4px solid #f59e0b;
}

.curated-field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.curated-field-name {
  margin: 0;
  font-size: 1rem;
  color: #374151;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.curated-field-badges {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.field-type-badge-small {
  padding: 0.25rem 0.5rem;
  background: #e5e7eb;
  color: #6b7280;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.manual-badge-small {
  padding: 0.25rem 0.5rem;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.ai-badge-small {
  padding: 0.25rem 0.5rem;
  background: #f3e8ff;
  color: #6b21a8;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.curated-field-value {
  color: #111827;
  font-size: 1rem;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  min-height: 2.5rem;
  display: flex;
  align-items: center;
}

.preview-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #666;
  font-style: italic;
}

.field-description {
  text-transform: capitalize;
}

.options-count {
  font-size: 0.8rem;
  background: #e9ecef;
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
}

.preview-badge {
  background: #fff3e0;
  color: #f57c00;
}

/* Metadata fields */
.metadata-fields {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.metadata-field-card {
  margin: 0.5rem;
  padding: 1.25rem;
  border: 1px solid #f0f0f0;
  border-radius: 0.75rem;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%);
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.metadata-field-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.metadata-field-card.has-ai-suggestion {
  border-left: 4px solid #2196f3;
  background: linear-gradient(135deg, #f0f8ff 0%, #ffffff 100%);
}

.metadata-field-card.has-manual-value {
  border-left: 4px solid #9c27b0;
  background: linear-gradient(135deg, #faf5ff 0%, #ffffff 100%);
}

.metadata-field-card.is-required {
  border-top: 3px solid #f44336;
  box-shadow: 0 2px 8px rgba(244, 67, 54, 0.1);
}

.metadata-field-card.active-highlight {
  border-color: #8B5CF6;
  background: linear-gradient(135deg, #f3f4f6 0%, #ffffff 100%);
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.2);
  transform: translateY(-2px);
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #f0f0f0;
}

.field-header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.field-header-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.field-name {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  color: #1a1a1a;
}

.required-indicator {
  color: #ef4444;
  font-size: 1.3rem;
  font-weight: 700;
  line-height: 1;
}

.field-type-label {
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: capitalize;
  font-weight: 500;
}

.ai-confidence-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.75rem;
  background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
  color: white;
  border-radius: 1rem;
  font-size: 0.85rem;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3);
}

.preview-label {
  font-size: 0.7rem;
  color: #9ca3af;
  font-weight: 600;
  letter-spacing: 0.5px;
  border: 1px solid #ffcdd2;
}

.field-type-badge {
  background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
  color: #7b1fa2;
  border: 1px solid #e1bee7;
}

.ai-badge {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  color: #1976d2;
  border: 1px solid #bbdefb;
}

.confidence-badge {
  background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}

.preview-badge {
  background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
  color: #f57c00;
  border: 1px solid #ffe0b2;
}

/* Manual Entry Saved Section - Clean, NO AI elements */
.manual-saved-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.manual-value {
  border-color: #9333ea !important;
}

/* AI Suggestion Section - ONLY for AI-generated */
.ai-suggestion-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.suggestion-value-container {
  margin-bottom: 1rem;
}

.suggestion-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.suggested-value-display {
  background: white;
  padding: 0.875rem 1.125rem;
  border-radius: 0.5rem;
  border: 2px solid #8B5CF6;
  font-size: 1.05rem;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.5;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.15);
}

.ai-reasoning {
  margin-bottom: 1rem;
}

.reasoning-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.reasoning-text {
  font-size: 0.9rem;
  color: #374151;
  line-height: 1.7;
}

.expand-link, .collapse-link {
  color: #8B5CF6;
  cursor: pointer;
  font-weight: 600;
  font-style: normal;
  text-decoration: none;
  user-select: none;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  background: rgba(139, 92, 246, 0.1);
  transition: all 0.2s;
}

.expand-link:hover, .collapse-link:hover {
  background: rgba(139, 92, 246, 0.2);
  color: #7C3AED;
}

.suggestion-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-top: 1rem;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  border: 2px solid transparent;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  flex: 1;
  min-width: 90px;
}

.btn-icon {
  font-size: 1.1rem;
  font-weight: 700;
  line-height: 1;
}

.btn-text {
  font-size: 0.9rem;
}

.accept-btn {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  color: white;
  border-color: #06b6d4;
}

.accept-btn:hover {
  background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
  border-color: #0891b2;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(6, 182, 212, 0.4);
}

.reject-btn {
  background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
  color: white;
  border-color: #ec4899;
}

.reject-btn:hover {
  background: linear-gradient(135deg, #db2777 0%, #be185d 100%);
  border-color: #db2777;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(236, 72, 153, 0.4);
}

.edit-btn {
  background: linear-gradient(135deg, #a78bfa 0%, #9333ea 100%);
  color: white;
  border-color: #a78bfa;
}

.edit-btn:hover {
  background: linear-gradient(135deg, #9333ea 0%, #7e22ce 100%);
  border-color: #9333ea;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(167, 139, 250, 0.4);
}

.edit-btn-secondary {
  background: transparent;
  color: #6b7280;
  border-color: #d1d5db;
  padding: 0.5rem 0.875rem;
  flex: 0 0 auto;
  min-width: 70px;
}

.edit-btn-secondary:hover {
  background: #f9fafb;
  border-color: #9ca3af;
  color: #374151;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.15);
}

.status-display {
  padding: 0.4rem 0.8rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-accepted {
  background: #e8f5e8;
  color: #2e7d32;
}

.status-rejected {
  background: #ffebee;
  color: #c62828;
}

.status-edited {
  background: #fff3e0;
  color: #f57c00;
}

.status-manual {
  background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
  color: #7b1fa2;
  font-weight: 600;
}

.status-pending {
  background: #f3e5f5;
  color: #7b1fa2;
}

/* Manual Entry Section */
.manual-entry-section {
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  padding: 1.25rem;
  border-radius: 0.75rem;
  border: 1px solid #f3e5f5;
  box-shadow: 0 2px 8px rgba(156, 39, 176, 0.06);
}

.field-input {
  margin-bottom: 0.75rem;
}

.field-input label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #555;
}

.form-select, .form-input, .form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  background: white;
  transition: all 0.2s ease;
}

.form-select:focus, .form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  background: #fafafa;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.manual-actions {
  display: flex;
  gap: 0.5rem;
}

.save-btn, .clear-btn {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.save-btn {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #45a049 0%, #388e3c 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.clear-btn {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  color: #666;
  border: 1px solid #e0e0e0;
}

.clear-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.save-btn:disabled, .clear-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Bulk actions */
.bulk-actions {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-radius: 0 0 0.75rem 0.75rem;
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.bulk-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  min-width: 160px;
}

.accept-all-btn {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  color: white;
}

.accept-all-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #45a049 0%, #388e3c 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.3);
}

.reject-all-btn {
  background: linear-gradient(135deg, #f44336 0%, #e53935 100%);
  color: white;
}

.reject-all-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #e53935 0%, #d32f2f 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(244, 67, 54, 0.3);
}

.bulk-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 1.5rem;
}

.edit-field {
  margin-bottom: 1rem;
}

.field-type {
  color: #666;
  font-size: 0.9rem;
  margin: 0;
}

.edit-input {
  margin-bottom: 1rem;
}

.edit-notes {
  margin-bottom: 1rem;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5a6fd8;
}

.btn-secondary {
  background: #f8f9fa;
  color: #666;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #e9ecef;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive design */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
    gap: 1rem;
    padding: 1rem;
  }
  
  .content-panel, .metadata-panel {
    height: auto;
    max-height: 60vh;
  }
  
  .control-row { grid-template-columns: 1fr; gap: 1rem; }
  .entity-group, .ai-group, .confidence-group, .action-group, .status-group { width: 100%; }
}

@media (max-width: 768px) {
  .control-panel {
    padding: 1rem;
  }
  
  .main-content {
    padding: 0.75rem;
    gap: 0.75rem;
  }
  
  .entity-select {
    min-width: auto;
    width: 100%;
  }
  
  .user-info {
    display: none;
  }
  
  .panel-header {
    padding: 1rem;
  }
  
  .metadata-field-card {
    padding: 1rem;
    margin: 0.25rem;
  }
  
  .bulk-actions {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .bulk-btn {
    min-width: auto;
  }
}

@media (max-width: 480px) {
  .app-header {
    padding: 1rem;
  }
  
  .header-container {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .control-panel {
    padding: 0.75rem;
  }
  
  .main-content {
    padding: 0.5rem;
  }
}

/* New Grid Column Styles - Override Everything */
.control-col {
  display: flex !important;
  flex-direction: column !important;
  gap: 0.5rem !important;
  min-height: 90px !important;
  justify-content: center !important;
  padding: 0.5rem 0 !important;
}

.col-selection { width: 520px !important; }
.col-entity { width: 520px !important; }
.col-ai { width: 220px !important; }
.col-confidence { width: 360px !important; }
.col-action { width: 180px !important; }
.col-status { min-width: auto !important; justify-self: end !important; }

.ai-label {
  display: flex !important;
  align-items: center !important;
  gap: 0.5rem !important;
  font-size: 0.85rem !important;
  cursor: pointer !important;
}

.ai-desc {
  font-size: 0.75rem !important;
  color: #666 !important;
  font-style: italic !important;
}

.confidence-slider {
  width: 100% !important;
  height: 4px !important;
  border-radius: 2px !important;
  background: #e5e7eb !important;
  outline: none !important;
  -webkit-appearance: none !important;
  margin: 0.25rem 0 !important;
}

.confidence-slider::-webkit-slider-thumb {
  -webkit-appearance: none !important;
  width: 16px !important;
  height: 16px !important;
  border-radius: 50% !important;
  background: #667eea !important;
  cursor: pointer !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
}

.confidence-slider::-webkit-slider-track {
  height: 4px !important;
  border-radius: 2px !important;
  background: #e5e7eb !important;
}

.start-btn {
  padding: 0.6rem 1rem !important;
  border: none !important;
  border-radius: 0.5rem !important;
  font-size: 0.85rem !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  transition: all 0.2s !important;
}

.start-btn.ai-mode {
  background: #667eea !important;
  color: white !important;
}

.start-btn.manual-mode {
  background: #9c27b0 !important;
  color: white !important;
}

.start-placeholder {
  font-size: 0.75rem !important;
  color: #999 !important;
  text-align: center !important;
  font-style: italic !important;
}

.status-pill {
  display: inline-flex !important;
  align-items: center !important;
  gap: 0.4rem !important;
  padding: 0.4rem 0.8rem !important;
  border-radius: 0.8rem !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  white-space: nowrap !important;
  height: 2.2rem !important;
  width: fit-content !important;
  min-width: fit-content !important;
  max-width: none !important;
}

@media (max-width: 1200px) {
  .control-grid { 
    grid-template-columns: 1fr !important; 
    gap: 1rem !important; 
    height: auto !important;
  }
  .col-entity, .col-ai, .col-confidence, .col-action, .col-status { 
    width: 100% !important; 
    height: auto !important;
  }
}
</style>
