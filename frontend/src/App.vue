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

    <!-- Control Panel - Modern Compact Layout -->
    <div class="control-panel">
      <div class="control-bar">
        <!-- Entity Selection -->
        <div class="control-group entity-group">
          <div class="select-wrapper">
            <label class="select-label">Catalog</label>
          <select 
            v-model="selectedSourceId" 
            @change="onSourceChange"
            :disabled="isLoading"
              class="modern-select"
          >
              <option value="">Choose catalog...</option>
            <option 
              v-for="source in sources" 
              :key="source.id" 
              :value="source.id"
            >
                {{ source.name }} ({{ source.editions_count }})
            </option>
          </select>
          </div>
          
          <div class="select-wrapper">
            <label class="select-label">Entity</label>
          <select 
            v-model="selectedEntityId" 
            @change="onEntityChange"
            :disabled="isLoading || !selectedSourceId"
              class="modern-select"
          >
              <option value="">{{ selectedSourceId ? 'Choose entity...' : '—' }}</option>
            <option 
              v-for="edition in filteredEditions" 
              :key="edition.id" 
              :value="edition.id"
            >
              {{ edition.entity_name || edition.source_internal_id || `Entity ${edition.id}` }}
            </option>
          </select>
          </div>
        </div>
        
        <!-- AI Toggle Compact -->
        <div class="control-group toggle-group">
          <label class="toggle-switch-modern">
            <input 
              type="checkbox" 
              v-model="useAI" 
              :disabled="isLoading || !selectedEntityId || curationStarted"
              @change="onAIToggleChange"
            >
            <span class="toggle-slider-modern">
              <span class="toggle-label-off">Manual</span>
              <span class="toggle-label-on">AI</span>
            </span>
            </label>
          </div>
          
        <!-- Confidence Slider Compact -->
        <div class="control-group confidence-group" v-if="useAI">
          <div class="confidence-compact">
            <span class="confidence-label-text">Confidence</span>
            <span class="confidence-value">{{ confidenceThreshold }}%</span>
            <input 
              type="range" 
              min="0" 
              max="80" 
              step="5" 
            v-model.number="confidenceThreshold" 
              :disabled="isLoading || curationStarted"
              class="slider-modern"
            >
            <div class="confidence-help">
              <button class="help-icon" @click="showConfidenceHelp = !showConfidenceHelp" type="button">?</button>
              <div v-if="showConfidenceHelp" class="help-tooltip">
                <div class="help-tooltip-content">
                  <strong>Confidence Threshold</strong>
                  <p>AI will only suggest values it's at least <span class="confidence-highlight">{{ confidenceThreshold }}%</span> confident about. Lower values = more suggestions, higher values = fewer but more reliable suggestions.</p>
                  <p><strong>Tip:</strong> Start with 50-60% to see a good balance of suggestions.</p>
                </div>
              </div>
            </div>
          </div>
          </div>
          
        <!-- Start Button -->
        <div class="control-group action-group">
          <button 
            v-if="selectedEntityId && scrapedContent.pages.length > 0"
            @click="startCuration" 
            :disabled="isLoading || curationStarted"
            class="btn-start-modern"
            :class="{ 'active': curationStarted }"
          >
            {{ curationStarted ? 'Active' : (isEntityFullyCurated ? 'Restart' : (aiSuggestions.length > 0 ? 'Resume' : 'Start')) }}
          </button>
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
            
            <!-- Structured Content Display -->
            <div v-if="currentPage.structured_content" class="structured-page">
              <!-- Navigation Bar -->
              <div v-if="currentPage.structured_content.navigation" class="page-navigation-bar">
                <div class="nav-label">Navigation:</div>
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
                  
                  <div v-if="section.tables && section.tables.length" class="section-tables">
                    <table v-for="(table, tIdx) in section.tables" :key="'table-' + tIdx" class="content-table">
                      <tr v-for="(row, rIdx) in table.rows" :key="'row-' + rIdx">
                        <td class="table-label">{{ row.label }}</td>
                        <td class="table-value" v-html="highlightText(row.value)"></td>
                      </tr>
                    </table>
                  </div>
                  
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
          <div v-if="selectedEntityId" class="progress-indicator">
            <span class="progress-icon">✓</span>
            <span class="progress-text">{{ progressText }}</span>
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
          <!-- Fully Curated Read-Only View -->
          <div v-if="isEntityFullyCurated && !curationStarted" class="curated-view">
            <div class="curated-header">
              <div class="curated-title">
                <span class="check-icon">✓</span>
                <h3>Fully Curated Entity</h3>
              </div>
              <p class="curated-subtitle">All metadata fields have been completed for this entity</p>
              
              <!-- Curation Time Display -->
              <div v-if="curationDuration" class="curation-time-badge">
                <span class="time-icon">⏱️</span>
                <span class="time-label">Curation Time:</span>
                <span class="time-value">{{ formattedCurationTime }}</span>
              </div>
            </div>

            <div class="curated-actions">
              <button @click="resumeEditing" class="btn-resume">
                <img src="/src/assets/icons/pen.png" class="btn-icon" alt="Manual" />
                Edit Metadata
              </button>
              <button @click="useAI = true; startCuration()" class="btn-ai-recurate" v-if="!useAI">
                <img src="/src/assets/icons/artificial-intelligence.png" class="btn-icon" alt="AI" />
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
                    <span v-if="field.isManual" class="manual-badge-small"><img src="/src/assets/icons/filling-form.png" class="badge-icon" alt="" /> Manual</span>
                    <span v-else-if="field.confidence" class="ai-badge-small"><img src="/src/assets/icons/artificial-intelligence.png" class="badge-icon" alt="" /> AI {{ field.confidence }}%</span>
                  </div>
                </div>
                <div class="curated-field-value">
                  <!-- Multiple choice values as list -->
                  <div v-if="field.isMultipleChoice && field.multipleValues" class="multiple-values-list">
                    <div v-for="(val, idx) in field.multipleValues" :key="idx" class="value-list-item">
                      • {{ val }}
                    </div>
                  </div>
                  <!-- Single value as text -->
                  <span v-else>{{ field.value }}</span>
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
                    <img src="/src/assets/icons/artificial-intelligence.png" class="inline-icon" alt="" /> {{ Math.round(field.aiSuggestion.confidence * 100) }}%
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
              <div v-else-if="curationStarted && field.showAISuggestion && field.aiSuggestion.ai_generated === false && editingFieldId !== field.id" class="manual-saved-section">
                <div class="suggestion-value-container">
                  <div class="suggestion-label">Manual Entry:</div>
                  <!-- Multiple choice values displayed as list -->
                  <div v-if="getMultipleChoiceValues(field.aiSuggestion)" class="suggested-value-display manual-value multiple-values">
                    <div v-for="(value, idx) in getMultipleChoiceValues(field.aiSuggestion)" :key="idx" class="value-item">
                      • {{ value }}
                    </div>
                  </div>
                  <!-- Single value displayed as text -->
                  <div v-else class="suggested-value-display manual-value">{{ renderSuggestionValue(field.aiSuggestion) }}</div>
                </div>
                
                <div class="suggestion-actions">
                  <div class="status-display status-manual">
                    ✓ SAVED
                  </div>
                  <button
                    @click.stop="reEditManualField(field)"
                    class="action-btn edit-btn-secondary" 
                  >
                    <span class="btn-icon">✎</span>
                    <span class="btn-text">Edit</span>
                  </button>
                </div>
              </div>
              
              <!-- AI Suggestion Section (ONLY for AI-generated suggestions) -->
              <div v-else-if="curationStarted && field.showAISuggestion && field.aiSuggestion.ai_generated !== false && editingFieldId !== field.id" class="ai-suggestion-section">
                <!-- AI Suggested Value -->
                <div class="suggestion-value-container">
                  <div class="suggestion-label">AI Suggested:</div>
                  <!-- Multiple choice values displayed as list -->
                  <div v-if="getMultipleChoiceValues(field.aiSuggestion)" class="suggested-value-display multiple-values">
                    <div v-for="(value, idx) in getMultipleChoiceValues(field.aiSuggestion)" :key="idx" class="value-item">
                      • {{ value }}
                    </div>
                  </div>
                  <!-- Single value displayed as text -->
                  <div v-else class="suggested-value-display">{{ renderSuggestionValue(field.aiSuggestion) }}</div>
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
                      @click.stop="editInline(field)"
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
                      @click.stop="editInline(field)"
                      class="action-btn edit-btn-secondary" 
                    >
                      <span class="btn-icon">✎</span>
                      <span class="btn-text">Edit</span>
                    </button>
                  </template>
              </div>
          </div>
          
              <!-- Manual Entry Section (when it needs manual entry OR is being re-edited inline) -->
              <div v-else-if="curationStarted && (field.needsManualEntry || editingFieldId === field.id)" class="manual-entry-section">
                <!-- Multiple Choice field (checkboxes) -->
                <div v-if="field.type === 'MULTIPLE_CHOICE'" class="field-input">
                  <label>Select Values (multiple allowed):</label>
                  <div class="checkbox-group">
                    <label 
                      v-for="option in field.property_options" 
                      :key="option.id"
                      class="checkbox-label"
                    >
                      <input 
                        type="checkbox"
                        :value="option.id"
                        v-model="field.manualSelectedOptions"
                        @change="onManualValueChange(field)"
                        @click.stop
                        class="checkbox-input"
                      >
                      <span>{{ option.name }}</span>
                    </label>
                    <label class="checkbox-label not-sure-option">
                      <input 
                        type="checkbox"
                        value="not_sure"
                        v-model="field.manualSelectedOptions"
                        @change="onManualValueChange(field)"
                        @click.stop
                        class="checkbox-input"
                      >
                      <span>⚠️ Not sure</span>
                    </label>
                  </div>
                </div>
                
                <!-- Single Choice / Binary field (dropdown) -->
                <div v-else-if="isChoiceField(field)" class="field-input">
                  <label>Select Value:</label>
                  <select 
                    v-model="field.manualValue" 
                    @change="onManualValueChange(field)"
                    @click.stop
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
                    <option value="not_sure">⚠️ Not sure</option>
                  </select>
                </div>
                
                <!-- Text and numerical fields -->
                <div v-else class="field-input">
                  <label>Value:</label>
                  <input 
                    v-if="field.type === 'NUMERICAL'"
                    v-model="field.manualValue"
                    @input="onManualValueChange(field)"
                    @click.stop
                    type="number" 
                    class="form-input"
                    :placeholder="`Enter ${field.name.toLowerCase()}`"
                  >
                  <textarea 
                    v-else
                    v-model="field.manualValue"
                    @input="onManualValueChange(field)"
                    @click.stop
                    class="form-textarea"
                    rows="3"
                    :placeholder="`Enter ${field.name.toLowerCase()}`"
                  ></textarea>
                </div>
                
                <!-- Curator Comment (Always Available) -->
                <div class="field-input curator-comment-field">
                  <label>Curator Comment (optional):</label>
                  <textarea 
                    v-model="field.curatorComment"
                    @input="onManualValueChange(field)"
                    @click.stop
                    class="form-textarea"
                    rows="2"
                    placeholder="Add notes, uncertainties, or additional context..."
                  ></textarea>
                </div>
                
                <!-- Manual Entry Actions -->
                <div class="manual-actions">
                  <button 
                    @click.stop="saveManualField(field)"
                    :disabled="!hasManualValue(field)"
                    class="save-btn"
                  >
                    Save
                  </button>
                  <button 
                    @click.stop="clearManualField(field)"
                    :disabled="!hasManualValue(field)"
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
                <option value="not_sure">⚠️ Not sure</option>
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
      confidenceThreshold: 60,
      curationStarted: false,
      
      // Curation time tracking
      curationStartTime: null,  // Timestamp when curation starts
      curationCompletionTime: null,  // Timestamp when curation completes
      curationDuration: null,  // Duration in seconds
      entityCurationTimes: {},  // Map of entity_id -> duration for persistence
      
      // Help tooltips
      showConfidenceHelp: false,
      
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
      manualSelectedOptions: {},  // For MULTIPLE_CHOICE fields
      curatorComments: {},  // For curator comments on any field
      activeHighlightId: null,
      editingFieldId: null,
      
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
          manualSelectedOptions: this.manualSelectedOptions[property.id] || [],
          curatorComment: this.curatorComments[property.id] || '',
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
        let isMultipleChoice = false
        let multipleValues = null
        
        if (suggestion) {
          // Handle MULTIPLE_CHOICE with comma-separated IDs
          if (property.type === 'MULTIPLE_CHOICE' && suggestion.custom_value && suggestion.custom_value.includes(',')) {
            const ids = suggestion.custom_value.split(',').map(v => parseInt(v.trim()))
            multipleValues = ids.map(id => (property.property_options || []).find(o => o.id === id)?.name || id)
            isMultipleChoice = true
            displayValue = null // Will use multipleValues array instead
          } else if (suggestion.property_option_id) {
            const option = property.property_options?.find(o => o.id === suggestion.property_option_id)
            displayValue = option ? option.name : 'Unknown option'
          } else if (suggestion.custom_value !== null && suggestion.custom_value !== undefined) {
            displayValue = suggestion.custom_value
          }
        }
        
        return {
          ...property,
          value: displayValue,
          multipleValues: multipleValues,
          isMultipleChoice: isMultipleChoice,
          suggestion: suggestion,
          isManual: suggestion?.ai_generated === false,
          confidence: suggestion?.confidence ? Math.round(suggestion.confidence * 100) : null
        }
      })
    },
    
    // Format curation duration for display
    formattedCurationTime() {
      if (!this.curationDuration) return 'N/A'
      
      const duration = this.curationDuration
      if (duration < 60) {
        return `${duration.toFixed(0)} seconds`
      } else if (duration < 3600) {
        const minutes = Math.floor(duration / 60)
        const seconds = Math.floor(duration % 60)
        return `${minutes}m ${seconds}s`
      } else {
        const hours = Math.floor(duration / 3600)
        const minutes = Math.floor((duration % 3600) / 60)
        return `${hours}h ${minutes}m`
      }
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
    
    progressText() {
      if (!this.selectedEntityId || !this.properties.length) return '0/0'
      
      // Count completed fields (same logic as other progress calculations)
      const completed = this.aiSuggestions.filter(s => 
        s.ai_generated === false ||  // Manual entries count as complete
        s.status === 'accepted' || 
        s.status === 'rejected' || 
        s.status === 'edited'
      ).length
      const total = this.properties.length
      
      if (completed === total && total > 0) {
        return `✓ All ${total} fields completed`
      } else {
        return `${completed}/${total}`
      }
    },
    
    highlightedContent() {
      if (!this.currentPage || !this.currentPage.text_content) return ''
      if (!this.aiSuggestions || !Array.isArray(this.aiSuggestions)) return this.currentPage.text_content
      
      let content = this.currentPage.text_content

    // Reset per-page highlight placement tracking so each suggestion is highlighted at most once
    this._highlightPageUrl = this.currentPage.url
    this._placedHighlights = {}
      
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
        
        if (!evidenceText) continue
        
        const propertyName = this.getPropertyName(suggestion.property_id)
        const isActive = this.activeHighlightId === suggestion.id
        
        // Determine highlight color
        let highlightColor = isActive ? '#8B5CF6' : '#F0E6FF'
        
        // Try exact phrase match (sentences/phrases preferred)
        if (content.includes(evidenceText)) {
        const placeholder = `__HIGHLIGHT_${suggestion.id}_${replacementCounter}__`
        content = content.replace(evidenceText, placeholder)
        
        content = content.replace(
          placeholder,
          `<span class="ai-highlight" 
                   id="highlight-${suggestion.id}"
                 data-suggestion-id="${suggestion.id}"
                 style="background-color: ${highlightColor}; padding: 2px 4px; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;" 
                   title="${propertyName}"
                 onclick="window.activateHighlight && window.activateHighlight(${suggestion.id})">${evidenceText}</span>`
        )
          replacementCounter++
        } else {
          // Try to find a sentence containing keywords from evidence
          const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 20)
          const evidenceKeywords = evidenceText.toLowerCase().split(/\s+/).filter(w => w.length > 4)
          
          let bestSentence = null
          let bestScore = 0
          
          for (const sentence of sentences) {
            const sentenceLower = sentence.toLowerCase()
            let score = 0
            for (const keyword of evidenceKeywords) {
              if (sentenceLower.includes(keyword)) score++
            }
            if (score > bestScore && score >= 2) { // Need at least 2 matching keywords
              bestScore = score
              bestSentence = sentence.trim()
            }
          }
          
          if (bestSentence && content.includes(bestSentence)) {
            const placeholder = `__HIGHLIGHT_${suggestion.id}_${replacementCounter}__`
            
            content = content.replace(
              bestSentence,
              placeholder
            )
            
            content = content.replace(
              placeholder,
              `<span class="ai-highlight" 
                     id="highlight-${suggestion.id}"
                     data-suggestion-id="${suggestion.id}"
                     style="background-color: ${highlightColor}; padding: 2px 4px; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;" 
                     title="${propertyName}"
                     onclick="window.activateHighlight && window.activateHighlight(${suggestion.id})">${bestSentence}</span>`
            )
        replacementCounter++
          }
        }
      }
      
      return content
    }
  },
  
  methods: {
    async fetchInitialData() {
      try {
        // Fetch and filter sources: hide "Manual Curation" catalog
        const allSources = await getSources()
        this.sources = allSources.filter(s => (s.name || '').toLowerCase() !== 'manual curation')
        // Load properties scoped to the currently selected source if available
        if (this.selectedSourceId) {
          this.properties = await getProperties({ source_id: this.selectedSourceId })
        } else {
        this.properties = await getProperties()
        }
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
      // Reload properties for the selected source to keep catalogs isolated
      this.reloadPropertiesForSelectedSource()
    },

    async reloadPropertiesForSelectedSource() {
      try {
        if (this.selectedSourceId) {
          const props = await getProperties({ source_id: this.selectedSourceId })
          const selected = this.sources.find(s => s.id === this.selectedSourceId)
          this.properties = (selected && selected.is_dummy) ? props : props.filter(p => !p.is_dummy)
        } else {
          this.properties = await getProperties()
        }
      } catch (e) {
        console.error('Failed to reload properties for source', e)
      }
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
      this.manualSelectedOptions = {}
      this.curatorComments = {}
      this.editingFieldId = null
      
      // Load saved curation time for this entity (if exists)
      this.curationDuration = this.entityCurationTimes[this.selectedEntityId] || null
      
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
      
      // Calculate current progress for status text
      const completed = this.aiSuggestions.filter(s => 
        s.ai_generated === false ||
        s.status === 'accepted' || 
        s.status === 'rejected' || 
        s.status === 'edited'
      ).length
      const total = this.properties.length
      
      this.statusText = `Editing metadata (${completed}/${total} complete)`
      this.statusClass = 'status-in-progress'
    },
    
    async startCuration() {
      if (!this.selectedEntityId || !this.scrapedContent.pages.length) return
      
      // Start timing the curation process
      this.curationStartTime = Date.now()
      this.curationCompletionTime = null
      this.curationDuration = null
      
      console.log('🕐 Curation timer started for entity', this.selectedEntityId)
      
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
          this.manualSelectedOptions = {}
          this.curatorComments = {}
          
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
      this.manualSelectedOptions = {}
      this.curatorComments = {}
      this.editingFieldId = null
        this.currentPageIndex = 0
      this.activeHighlightId = null
      this.curationStarted = false
      this.statusText = 'Ready'
      this.statusClass = 'status-ready'
      
      // Reset curation timer (but keep entityCurationTimes for persistence)
      this.curationStartTime = null
      this.curationCompletionTime = null
      this.curationDuration = null
      // Note: entityCurationTimes is NOT reset - it persists across entities
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
      // MULTIPLE_CHOICE: backend stores all selected IDs in custom_value as comma-separated list
      const prop = this.properties.find(p => p.id === suggestion.property_id)
      if (!prop) return ''
      if (prop.type === 'MULTIPLE_CHOICE' && suggestion.custom_value && suggestion.custom_value.includes(',')) {
        const ids = suggestion.custom_value.split(',').map(v => parseInt(v.trim()))
        const names = ids.map(id => (prop.property_options || []).find(o => o.id === id)?.name || id)
        return names.join(', ')
      }
      if (suggestion.custom_value && !suggestion.property_option_id) return suggestion.custom_value
      const option = prop.property_options?.find(o => o.id === suggestion.property_option_id)
      return option ? option.name : ''
    },
    
    // Get multiple choice values as an array
    getMultipleChoiceValues(suggestion) {
      const prop = this.properties.find(p => p.id === suggestion.property_id)
      if (!prop || prop.type !== 'MULTIPLE_CHOICE') return null
      if (suggestion.custom_value && suggestion.custom_value.includes(',')) {
        const ids = suggestion.custom_value.split(',').map(v => parseInt(v.trim()))
        return ids.map(id => (prop.property_options || []).find(o => o.id === id)?.name || id)
      }
      return null
    },
    
    toggleReasoning(field) {
      // Toggle the reasoning expanded state
      field.reasoningExpanded = !field.reasoningExpanded
      this.$forceUpdate() // Force re-render
    },
    
    highlightText(text) {
      // Apply evidence highlighting to a text snippet (for structured content)
      if (!text || !this.aiSuggestions || !this.currentPage) return text
      
      // Ensure we only place one highlight per suggestion across the whole page render
      if (!this._highlightPageUrl || this._highlightPageUrl !== this.currentPage.url) {
        this._highlightPageUrl = this.currentPage.url
        this._placedHighlights = {}
      }
      
      let highlighted = text
      let replacementCounter = 0
      
      const aiSugs = this.aiSuggestions.filter(s => 
        s.evidence && 
        s.page_url === this.currentPage.url
      )
      
      for (const sug of aiSugs) {
        if (this._placedHighlights && this._placedHighlights[sug.id]) {
          continue // already highlighted this suggestion elsewhere on the page
        }
        
        // Special handling for MULTIPLE_CHOICE: highlight each selected option name once
        const prop = this.properties.find(p => p.id === sug.property_id)
        if (prop && prop.type === 'MULTIPLE_CHOICE') {
          // Choose a single best target to highlight: prefer evidence text; else first option name found; else best sentence by keywords
          const propertyName = this.getPropertyName(sug.property_id)
          const isActive = this.activeHighlightId === sug.id
          const highlightColor = isActive ? '#8B5CF6' : '#F0E6FF'

          const evidenceText = typeof sug.evidence === 'string' ? sug.evidence : sug.evidence?.content
          if (evidenceText && highlighted.includes(evidenceText)) {
            const placeholder = `__HIGHLIGHT_${sug.id}_${replacementCounter}__`
            replacementCounter++
            highlighted = highlighted.replace(evidenceText, placeholder)
            highlighted = highlighted.replace(
              placeholder,
              `<span class="ai-highlight" id="highlight-${sug.id}" data-suggestion-id="${sug.id}" style="background-color: ${highlightColor}; padding: 2px 4px; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;" title="${propertyName}" onclick="window.activateHighlight && window.activateHighlight(${sug.id})">${evidenceText}</span>`
            )
            this._placedHighlights[sug.id] = true
            continue
          }

          // Build option names
          let optionIds = []
          if (Array.isArray(sug.property_option_ids) && sug.property_option_ids.length > 0) {
            optionIds = sug.property_option_ids
          } else if (sug.custom_value && typeof sug.custom_value === 'string' && sug.custom_value.includes(',')) {
            optionIds = sug.custom_value.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v))
          } else if (sug.property_option_id) {
            optionIds = [sug.property_option_id]
          }
          const optionNames = optionIds
            .map(id => (prop.property_options || []).find(o => o.id === id)?.name)
            .filter(Boolean)

          // Try to highlight the first option name that appears
          let placed = false
          for (let i = 0; i < optionNames.length && !placed; i++) {
            const name = optionNames[i]
            const regex = new RegExp(name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i')
            const match = highlighted.match(regex)
            if (match && match[0]) {
              const placeholder = `__HIGHLIGHT_${sug.id}_opt_${replacementCounter}__`
              replacementCounter++
              highlighted = highlighted.replace(match[0], placeholder)
              highlighted = highlighted.replace(
                placeholder,
                `<span class="ai-highlight" id="highlight-${sug.id}" data-suggestion-id="${sug.id}" style="background-color: ${highlightColor}; padding: 2px 4px; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;" onclick="window.activateHighlight && window.activateHighlight(${sug.id})">${match[0]}</span>`
              )
              this._placedHighlights[sug.id] = true
              placed = true
            }
          }

          if (placed) continue

          // Fallback: best sentence by keywords (from evidence)
          if (evidenceText) {
            const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 20)
            const evidenceKeywords = evidenceText.toLowerCase().split(/\s+/).filter(w => w.length > 4)
            let bestSentence = null
            let bestScore = 0
            for (const sentence of sentences) {
              const sentenceLower = sentence.toLowerCase()
              let score = 0
              for (const keyword of evidenceKeywords) {
                if (sentenceLower.includes(keyword)) score++
              }
              if (score > bestScore && score >= 2) {
                bestScore = score
                bestSentence = sentence.trim()
              }
            }
            if (bestSentence && highlighted.includes(bestSentence)) {
              const placeholder = `__HIGHLIGHT_${sug.id}_${replacementCounter}__`
              replacementCounter++
              highlighted = highlighted.replace(bestSentence, placeholder)
              highlighted = highlighted.replace(
                placeholder,
                `<span class="ai-highlight" id="highlight-${sug.id}" data-suggestion-id="${sug.id}" style="background-color: ${highlightColor}; padding: 2px 4px; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;" title="${propertyName}" onclick="window.activateHighlight && window.activateHighlight(${sug.id})">${bestSentence}</span>`
              )
              this._placedHighlights[sug.id] = true
              continue
            }
          }
        }
        const evidenceText = typeof sug.evidence === 'string' ? sug.evidence : sug.evidence.content
        
        if (!evidenceText) continue
        
        const propertyName = this.getPropertyName(sug.property_id)
        const isActive = this.activeHighlightId === sug.id
        
        // Purple color scheme: active = dark purple, inactive = light purple
        let highlightColor = isActive ? '#8B5CF6' : '#F0E6FF'
        
        // Try exact phrase match (prefer longer matches - sentences/phrases)
        if (highlighted.includes(evidenceText)) {
        const placeholder = `__HIGHLIGHT_${sug.id}_${replacementCounter}__`
        replacementCounter++
        
        highlighted = highlighted.replace(
          evidenceText,
          placeholder
        )
        
        highlighted = highlighted.replace(
          placeholder,
          `<span class="ai-highlight" 
                   id="highlight-${sug.id}"
                 data-suggestion-id="${sug.id}"
                 style="background-color: ${highlightColor}; padding: 2px 4px; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;" 
                   title="${propertyName}"
                 onclick="window.activateHighlight && window.activateHighlight(${sug.id})">${evidenceText}</span>`
        )
        this._placedHighlights[sug.id] = true
        } else {
          // Try to find a sentence or phrase containing key words from evidence
          const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 20)
          const evidenceKeywords = evidenceText.toLowerCase().split(/\s+/).filter(w => w.length > 4)
          
          let bestSentence = null
          let bestScore = 0
          
          for (const sentence of sentences) {
            const sentenceLower = sentence.toLowerCase()
            let score = 0
            for (const keyword of evidenceKeywords) {
              if (sentenceLower.includes(keyword)) score++
            }
            if (score > bestScore && score >= 2) { // Need at least 2 matching keywords
              bestScore = score
              bestSentence = sentence.trim()
            }
          }
          
          if (bestSentence && highlighted.includes(bestSentence)) {
            const placeholder = `__HIGHLIGHT_${sug.id}_${replacementCounter}__`
            replacementCounter++
            
            highlighted = highlighted.replace(
              bestSentence,
              placeholder
            )
            
            highlighted = highlighted.replace(
              placeholder,
              `<span class="ai-highlight" 
                     id="highlight-${sug.id}"
                     data-suggestion-id="${sug.id}"
                     style="background-color: ${highlightColor}; padding: 2px 4px; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;" 
                     title="${propertyName}"
                     onclick="window.activateHighlight && window.activateHighlight(${sug.id})">${bestSentence}</span>`
            )
            this._placedHighlights[sug.id] = true
          }
        }
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
      
      if (completed === total && total > 0) {
        this.statusText = `✓ All ${total} fields complete!`
        this.statusClass = 'status-complete'
        
        // Stop the timer when curation is complete
        if (this.curationStartTime && !this.curationCompletionTime) {
          this.curationCompletionTime = Date.now()
          this.curationDuration = (this.curationCompletionTime - this.curationStartTime) / 1000 // Convert to seconds
          
          // Save duration for this specific entity
          this.entityCurationTimes[this.selectedEntityId] = this.curationDuration
          
          console.log(`⏱️ Curation completed in ${this.curationDuration.toFixed(2)} seconds`)
          console.log(`💾 Saved curation time for entity ${this.selectedEntityId}`)
          
          // Log curation time to backend
          this.logCurationTime()
        }
        
        // IMPORTANT: End curation mode to show the success page
        this.curationStarted = false
        console.log('🎉 Curation complete! Showing success page...')
      } else if (completed > 0) {
        this.statusText = `${completed}/${total} fields curated`
        this.statusClass = 'status-in-progress'
      } else {
        this.statusText = 'Curation active'
        this.statusClass = 'status-success'
      }
    },
    
    async logCurationTime() {
      // Log curation time data to backend for study analysis
      try {
        const logData = {
          entity_id: this.selectedEntityId,
          entity_name: this.selectedEntity?.entity_name || 'Unknown',
          source_id: this.selectedSourceId,
          source_name: this.selectedSource?.name || 'Unknown',
          curation_mode: this.useAI ? 'ai' : 'manual',
          confidence_threshold: this.confidenceThreshold,
          start_time: new Date(this.curationStartTime).toISOString(),
          completion_time: new Date(this.curationCompletionTime).toISOString(),
          duration_seconds: this.curationDuration,
          total_fields: this.properties.length,
          ai_suggestions_count: this.aiSuggestions.filter(s => s.ai_generated === true).length,
          manual_entries_count: this.aiSuggestions.filter(s => s.ai_generated === false).length,
          timestamp: new Date().toISOString()
        }
        
        await axios.post('/api/log-curation-time', logData)
        console.log('✅ Curation time logged to backend:', logData)
      } catch (error) {
        console.error('Failed to log curation time:', error)
        // Don't alert user - this is background logging
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
      if (field.type === 'MULTIPLE_CHOICE') {
        // Exclusive "Not sure"
        if (field.manualSelectedOptions && field.manualSelectedOptions.includes('not_sure')) {
          field.manualSelectedOptions = ['not_sure']
        }
        this.manualSelectedOptions[field.id] = [...field.manualSelectedOptions]
        console.log(`Manual values changed for field ${field.name}:`, field.manualSelectedOptions)
      } else {
      this.manualValues[field.id] = field.manualValue
      console.log(`Manual value changed for field ${field.name}:`, field.manualValue)
      }
      
      // Store curator comment
      if (field.curatorComment) {
        this.curatorComments[field.id] = field.curatorComment
      }
    },

    // Trigger inline edit for a saved manual field
    reEditManualField(field) {
      const suggestion = field.aiSuggestion
      if (!suggestion) return
      // Preload values from saved suggestion
      const prop = this.properties.find(p => p.id === suggestion.property_id)
      if (prop && prop.type === 'MULTIPLE_CHOICE' && suggestion.custom_value && suggestion.custom_value.includes(',')) {
        field.manualSelectedOptions = suggestion.custom_value.split(',').map(id => parseInt(id.trim()))
        this.manualSelectedOptions[field.id] = [...field.manualSelectedOptions]
      } else if (suggestion.property_option_id) {
        field.manualValue = suggestion.property_option_id
        this.manualValues[field.id] = field.manualValue
      } else if (suggestion.custom_value !== undefined && suggestion.custom_value !== null) {
        field.manualValue = suggestion.custom_value
        this.manualValues[field.id] = field.manualValue
      }
      field.curatorComment = suggestion.curator_note || ''
      this.curatorComments[field.id] = field.curatorComment
      // Open inline editor
      this.editingFieldId = field.id
      this.$forceUpdate()
    },

    // Inline edit for AI suggestions or curated AI
    editInline(field) {
      const suggestion = field.aiSuggestion
      if (!suggestion) return
      const prop = this.properties.find(p => p.id === suggestion.property_id)
      if (prop && prop.type === 'MULTIPLE_CHOICE' && suggestion.custom_value && suggestion.custom_value.includes(',')) {
        field.manualSelectedOptions = suggestion.custom_value.split(',').map(id => parseInt(id.trim()))
        this.manualSelectedOptions[field.id] = [...field.manualSelectedOptions]
      } else if (suggestion.property_option_id) {
        field.manualValue = suggestion.property_option_id
        this.manualValues[field.id] = field.manualValue
      } else if (suggestion.custom_value !== undefined && suggestion.custom_value !== null) {
        field.manualValue = suggestion.custom_value
        this.manualValues[field.id] = field.manualValue
      }
      field.curatorComment = suggestion.curator_note || ''
      this.curatorComments[field.id] = field.curatorComment
      this.editingFieldId = field.id
      this.$forceUpdate()
    },
    
    hasManualValue(field) {
      // Check the field object first (this is what v-model updates directly)
      const hasNote = field.curatorComment && field.curatorComment.toString().trim() !== ''
      
      if (field.type === 'MULTIPLE_CHOICE') {
        const hasChoices = field.manualSelectedOptions && field.manualSelectedOptions.length > 0
        return hasChoices || hasNote
      }
      
      const hasValue = field.manualValue && field.manualValue.toString().trim() !== ''
      return hasValue || hasNote
    },
    
    async saveManualField(field) {
      // Check if field has value
      if (!this.hasManualValue(field)) return
      
      try {
            const payload = {
          source_id: this.selectedSource.id,
          edition_id: this.selectedEntity.id,
          property_id: field.id,
          curator_note: field.curatorComment || null,
              evidence: {
            content: `Manual entry by curator`,
                source_url: window.location.href,
            confidence: 1.0,
                extraction_method: 'manual'
              }
            }
            
        // Handle different field types
        if (field.type === 'MULTIPLE_CHOICE') {
          // For multiple choice, filter out "not_sure" and send as array
          const selectedIds = field.manualSelectedOptions.filter(id => id !== 'not_sure')
          if (selectedIds.length > 0) {
            payload.property_option_ids = selectedIds  // Send as array
          }
          // If "not_sure" is selected, add to curator note
          if (field.manualSelectedOptions.includes('not_sure')) {
            payload.curator_note = (payload.curator_note ? payload.curator_note + '\n' : '') + '[UNCERTAIN]'
          }
        } else if (this.isChoiceField(field)) {
          // Single choice or binary
          if (field.manualValue === 'not_sure') {
            payload.curator_note = (payload.curator_note ? payload.curator_note + '\n' : '') + '[UNCERTAIN - No value selected]'
            payload.property_option_id = null
              } else {
            payload.property_option_id = field.manualValue
          }
        } else {
          // Free text or numerical
          payload.custom_value = field.manualValue
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
          // Close inline editor
          this.editingFieldId = null
          
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
      field.manualSelectedOptions = []
      field.curatorComment = ''
      this.manualValues[field.id] = ''
      this.manualSelectedOptions[field.id] = []
      this.curatorComments[field.id] = ''
     },
     
     handleClickOutside(event) {
      // Close confidence help tooltip when clicking outside
      const helpElement = event.target.closest('.confidence-help')
      if (!helpElement && this.showConfidenceHelp) {
        this.showConfidenceHelp = false
      }
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
      // Always activate the requested highlight (no toggle-off) and reset placement map
      this.activeHighlightId = suggestionId
      this._placedHighlights = {}
      this._highlightPageUrl = this.currentPage?.url || null
      
      // Auto-scroll to the highlighted element
      this.$nextTick(() => {
        const highlightElement = document.getElementById(`highlight-${suggestionId}`)
        if (highlightElement) {
          highlightElement.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center',
            inline: 'nearest'
          })
        }
      })
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
  
  mounted() {
    // Close help tooltip when clicking outside
    document.addEventListener('click', this.handleClickOutside)
  },
  
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside)
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
  max-width: 100%;
  margin: 0;
  padding: 0 2rem;
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

/* Control Panel - Modern Compact Layout */
.control-panel {
  background: white;
  padding: 1rem 2rem;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.control-bar {
  display: flex;
  align-items: flex-end;
  gap: 1.5rem;
  max-width: 1600px;
  margin: 0 auto;
}

.control-group {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
}

.entity-group {
  flex: 1;
  gap: 1rem;
  max-width: 700px;
}

.toggle-group {
  flex-shrink: 0;
}

.confidence-group {
  flex-shrink: 0;
  min-width: 180px;
  margin-left: -0.5rem;
}

.action-group {
  flex-shrink: 0;
}

.select-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.select-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding-left: 0.25rem;
}


.modern-select {
  flex: 1;
  padding: 0.625rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  background: white;
  transition: all 0.2s ease;
  cursor: pointer;
  color: #374151;
}

.modern-select:hover:not(:disabled) {
  border-color: #9ca3af;
}

.modern-select:focus {
  outline: none;
  border-color: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
}

.modern-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f9fafb;
}


.ai-toggle-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

/* Modern Toggle Switch */
.toggle-switch-modern {
  position: relative;
  display: inline-block;
  width: 120px;
  height: 36px;
  cursor: pointer;
}

.toggle-switch-modern input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider-modern {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #e5e7eb;
  transition: 0.3s;
  border-radius: 18px;
  display: flex;
  align-items: center;
  padding: 0 8px;
}

.toggle-label-off,
.toggle-label-on {
  position: absolute;
  font-size: 0.75rem;
  font-weight: 600;
  transition: 0.3s;
  color: #6b7280;
  z-index: 1;
}

.toggle-label-off {
  left: 12px;
  opacity: 1;
}

.toggle-label-on {
  right: 12px;
  opacity: 0.4;
}

.toggle-switch-modern input:checked + .toggle-slider-modern .toggle-label-off {
  opacity: 0.4;
}

.toggle-switch-modern input:checked + .toggle-slider-modern .toggle-label-on {
  opacity: 1;
  color: white;
}

.toggle-slider-modern:before {
  position: absolute;
  content: "";
  height: 28px;
  width: 56px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: 0.3s;
  border-radius: 14px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toggle-switch-modern input:checked + .toggle-slider-modern {
  background-color: #7c3aed;
}

.toggle-switch-modern input:checked + .toggle-slider-modern:before {
  transform: translateX(56px);
}

.toggle-switch-modern input:disabled + .toggle-slider-modern {
  opacity: 0.5;
  cursor: not-allowed;
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
  appearance: none;
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
  grid-template-rows: 1fr;
  gap: 1.5rem;
  padding: 1.5rem 2rem;
  max-width: 100%;
  margin: 0;
  flex: 1;
  min-height: 0; /* Allow flex children to shrink */
  overflow: hidden;
  height: calc(100vh - 160px);
  align-items: stretch;
}

.content-panel, .metadata-panel {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  border: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow-y: auto;
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

.content-stats {
  font-size: 0.9rem;
  color: #666;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.progress-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #f3e5f5 0%, #faf5ff 100%);
  border-radius: 0.5rem;
  border-left: 3px solid #8B5CF6;
  font-weight: 600;
  color: #8B5CF6;
  white-space: nowrap;
}

.progress-icon {
  font-size: 1rem;
}

.progress-text {
  font-size: 0.9rem;
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
  flex: 1 1 auto;
  height: 100%;
  min-height: 0;
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
  flex: 1 1 auto;
  overflow-y: visible;
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
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
  flex: 1 1 auto;
  overflow-y: visible;
  min-height: 0;
  height: auto;
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
  display: inline-block;
  font-family: monospace;
  background: #f5f5f5;
  padding: 0.5rem;
  border-radius: 0.25rem;
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
  flex: 1 1 auto;
  overflow-y: visible;
  min-height: 0;
  height: auto;
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
  flex: 1 1 auto;
  overflow-y: visible;
  padding: 1rem;
  background: #fafafa;
  border-radius: 0.5rem;
  min-height: 0;
  height: auto;
}

.page-navigation-bar {
  background: #f9fafb;
  padding: 0.75rem 1rem;
  border-radius: 0.375rem;
  border-left: 3px solid #d1d5db;
  font-size: 0.85rem;
  color: #9ca3af;
}

.nav-label {
  font-weight: 600;
  margin-bottom: 0.25rem;
  color: #9ca3af;
}

.nav-content {
  color: #9ca3af;
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
  flex: 1;
  padding: 0 1.5rem 1.5rem 1.5rem;
}

.content-section {
  background: white;
  padding: 1.25rem;
  border-radius: 0.5rem;
  border: 1px solid #e8e8e8;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  flex: 1;
  display: flex;
  flex-direction: column;
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

.section-tables {
  margin: 1rem 0;
}

.content-table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  background: #fff;
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.content-table tr {
  border-bottom: 1px solid #e0e0e0;
}

.content-table tr:last-child {
  border-bottom: none;
}

.content-table td {
  padding: 0.75rem 1rem;
  line-height: 1.6;
}

.table-label {
  font-weight: 600;
  color: #1e6b4e;
  width: 150px;
  vertical-align: top;
  background: #f8faf9;
}

.table-value {
  color: #444;
}

.table-value a {
  color: #1e6b4e;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all 0.2s ease;
}

.table-value a:hover {
  color: #2d8a66;
  border-bottom-color: #2d8a66;
}

.page-footer {
  background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
  padding: 1.25rem 1.5rem;
  border-radius: 0.5rem;
  border-top: 2px solid #d0d0d0;
  font-size: 0.9rem;
  margin-top: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.footer-label {
  font-weight: 600;
  color: #555;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.footer-content {
  color: #777;
  line-height: 1.7;
  font-size: 0.85rem;
}

/* Metadata content */
.metadata-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.btn-icon {
  width: 20px;
  height: 20px;
  vertical-align: middle;
  margin-right: 0.4rem;
}

.badge-icon {
  width: 18px;
  height: 18px;
  vertical-align: middle;
  margin-right: 0.3rem;
}

.inline-icon {
  width: 18px;
  height: 18px;
  vertical-align: middle;
  margin-right: 0.3rem;
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

.curation-time-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 1rem;
  padding: 0.75rem 1.25rem;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  font-weight: 600;
}

.time-icon {
  font-size: 1.25rem;
}

.time-label {
  color: #6b7280;
  font-size: 0.9rem;
}

.time-value {
  color: #16a34a;
  font-size: 1.1rem;
  font-weight: 700;
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

.curated-field-value .multiple-values-list {
  width: 100%;
}

.curated-field-value .value-list-item {
  padding: 0.25rem 0;
  font-size: 1rem;
  color: #111827;
  line-height: 1.6;
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
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
  background: white;
  box-shadow: none;
}

.metadata-field-card:hover {
  border-color: #c4b5fd;
  box-shadow: 0 1px 3px rgba(139, 92, 246, 0.1);
}

.metadata-field-card.has-ai-suggestion {
  border-left: 3px solid #c4b5fd;
}

.metadata-field-card.has-manual-value {
  border-left: 3px solid #c4b5fd;
}

.metadata-field-card.is-required {
  border-top: 2px solid #f87171;
}

.metadata-field-card.active-highlight {
  border-left: 3px solid #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding-bottom: 0;
  border-bottom: none;
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

.suggested-value-display.multiple-values {
  padding: 0.5rem 1.125rem;
}

.suggested-value-display .value-item {
  padding: 0.375rem 0;
  font-size: 1.05rem;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.6;
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
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
  border: 1px solid transparent;
  padding: 0.5rem 1rem;
  flex: 0 0 auto;
  min-width: auto;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  transition: all 0.15s ease;
  box-shadow: none;
}

.edit-btn-secondary:hover {
  background: rgba(107, 114, 128, 0.15);
  color: #4b5563;
}

.status-display {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  border: 1px solid transparent;
}

.status-accepted {
  background: rgba(34, 197, 94, 0.15);
  color: #16a34a;
}

.status-rejected {
  background: rgba(239, 68, 68, 0.15);
  color: #dc2626;
}

.status-edited {
  background: #fff3e0;
  color: #f57c00;
}

.status-manual {
  background: #7c3aed;
  color: white;
}

.status-pending {
  background: #f3e5f5;
  color: #7b1fa2;
}

/* Manual Entry Section */
.manual-entry-section {
  background: transparent;
  padding: 0;
  border-radius: 0;
  border: none;
  box-shadow: none;
}

/* Checkbox Group for Multiple Choice */
.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0;
  background: transparent;
  border-radius: 0;
  border: none;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.375rem;
  transition: background 0.2s;
}

.checkbox-label:hover {
  background: #f9fafb;
}

.checkbox-input {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #7c3aed;
}

.checkbox-label span {
  font-size: 0.9rem;
  color: #374151;
}

.not-sure-option {
  border-top: 1px solid #e5e7eb;
  padding-top: 0.75rem;
  margin-top: 0.5rem;
}

.not-sure-option span {
  color: #f59e0b;
  font-weight: 500;
}

/* Curator Comment Field */
.curator-comment-field {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.curator-comment-field label {
  color: #7c3aed;
  font-weight: 600;
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
  margin-top: 0.75rem;
  padding-top: 0;
  border-top: none;
}

/* Soft button style (btn-soft btn-primary) */
.save-btn, .clear-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  box-shadow: none;
}

/* Save button: Soft purple initially, dark purple after save */
.save-btn {
  background: rgba(167, 139, 250, 0.15);
  color: #7c3aed;
  border: 1px solid transparent;
}

.save-btn:hover:not(:disabled) {
  background: rgba(167, 139, 250, 0.25);
  color: #6d28d9;
}

.save-btn:active:not(:disabled) {
  background: rgba(167, 139, 250, 0.3);
}

/* After save, button becomes solid dark purple */
.save-btn.saved {
  background: #7c3aed;
  color: white;
}

.save-btn.saved:hover {
  background: #6d28d9;
}

/* Clear button: Soft gray */
.clear-btn {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
  border: 1px solid transparent;
}

.clear-btn:hover:not(:disabled) {
  background: rgba(107, 114, 128, 0.15);
  color: #4b5563;
}

.clear-btn:active:not(:disabled) {
  background: rgba(107, 114, 128, 0.2);
}

.save-btn:disabled, .clear-btn:disabled {
  opacity: 0.4;
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
    padding: 1rem 1.5rem;
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
    padding: 0.75rem 1rem;
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
    padding: 0.5rem 0.75rem;
  }
}


/* Modern Compact Confidence Slider */
.confidence-compact {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  position: relative;
}

.confidence-label-text {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.confidence-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: #7c3aed;
  min-width: 35px;
}

.confidence-help {
  position: relative;
  display: flex;
  align-items: center;
}

.help-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #7c3aed;
  color: white;
  border: none;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  padding: 0;
  line-height: 1;
}

.help-icon:hover {
  background: #6d28d9;
  transform: scale(1.1);
}

.help-tooltip {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.help-tooltip-content {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 280px;
  font-size: 0.875rem;
  line-height: 1.5;
}

.help-tooltip-content strong {
  display: block;
  color: #7c3aed;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.help-tooltip-content p {
  margin: 0.5rem 0;
  color: #4b5563;
}

.help-tooltip-content p:last-child {
  margin-bottom: 0;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e5e7eb;
}

.confidence-highlight {
  color: #7c3aed;
  font-weight: 700;
  font-size: 1em;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slider-modern {
  width: 120px;
  height: 4px;
  border-radius: 2px;
  background: #e5e7eb;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.slider-modern::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #7c3aed;
  cursor: pointer;
  transition: all 0.2s ease;
}

.slider-modern::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.slider-modern::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #7c3aed;
  cursor: pointer;
  border: none;
}

/* Modern Start Button */
.btn-start-modern {
  padding: 0.625rem 3rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  background: #7c3aed;
  color: white;
  box-shadow: 0 1px 3px rgba(124, 58, 237, 0.2);
  min-width: 140px;
}

.btn-start-modern:hover:not(:disabled) {
  background: #6d28d9;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(124, 58, 237, 0.3);
}

.btn-start-modern:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

.btn-start-modern.active {
  background: #059669;
}

/* Responsive Control Panel */
@media (max-width: 1200px) {
  .control-bar {
    flex-wrap: wrap;
    gap: 1rem;
  }
  
  .entity-group {
    width: 100%;
    max-width: none;
    flex-direction: column;
  }
  
  .toggle-group,
  .confidence-group,
  .action-group {
    width: auto;
  }
}
</style>
