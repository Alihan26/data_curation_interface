<template>
  <div id="app">
    <!-- Header Navigation -->
    <header class="app-header">
      <div class="header-container">
        <!-- Logo and Title -->
        <div class="header-left">
          <div class="logo-section">
            <h1 class="app-title">
              Metadata Curation Interface
            </h1>
            <span class="version-badge">v1.0</span>
          </div>
        </div>

        <!-- Navigation Links -->
        <nav class="header-nav">
          <button @click="goToOverview" class="nav-btn overview-btn">
            Project Overview
          </button>
        </nav>

        <!-- User Section -->
        <div class="header-right">
          <!-- User Profile -->
          <div class="user-profile">
            <div class="user-avatar">AK</div>
            <div class="user-info">
              <div class="user-greeting">Hello, Alihan Karataşlı</div>
              <div class="user-role">Data Curator</div>
            </div>
            <button @click="showUserMenu = !showUserMenu" class="user-menu-btn" title="User menu">
              <span class="icon">⚙️</span>
            </button>
          </div>

          <!-- User Dropdown Menu -->
          <div v-if="showUserMenu" class="user-dropdown" @click.stop>
            <div class="dropdown-item" @click="showSettings">
              <span class="icon">⚙️</span>
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

    <!-- Pre-Curation View -->
    <div v-if="currentView === 'pre'" class="pre-curation-container">
      <aside class="setup-sidebar">
        <h2>How to Use This System</h2>
        <div class="workflow-guide">
          <div class="workflow-step">
            <div class="step-number">1</div>
            <div class="step-content">
              <h4>Select Source & Entity</h4>
              <p>Choose a source, then click on a specific entity within it</p>
            </div>
          </div>
          <div class="workflow-step">
            <div class="step-number">2</div>
            <div class="step-content">
              <h4>Enter URLs</h4>
              <p>Add URLs to analyze (or use default)</p>
            </div>
          </div>
          <div class="workflow-step">
            <div class="step-number">3</div>
            <div class="step-content">
              <h4>Process Curation</h4>
              <p>Click "Process Curation" to get AI suggestions for the selected entity</p>
            </div>
          </div>
          <div class="workflow-step">
            <div class="step-number">4</div>
            <div class="step-content">
              <h4>Review & Accept</h4>
              <p>Review AI suggestions, accept good ones, reject incorrect ones</p>
            </div>
          </div>
        </div>
        
        <h3>Configuration</h3>
        <div class="section">
          <h3>Source Selection</h3>
          <div v-if="sources.length > 0" class="sources-list">
            <div v-for="source in sources" :key="source.id" 
                 @click="selectSource(source)" 
                 :class="['source-item', { active: selectedSource?.id === source.id }]">
              <div class="source-header">
                <div class="source-name">{{ source.name }}</div>
                <div v-if="source.is_dummy" class="dummy-badge">Test Data</div>
              </div>
              <div class="source-description">{{ source.description }}</div>
              <div class="source-stats">
                <span>{{ source.editions_count }} editions</span>
                <span>{{ source.suggestions_count }} suggestions</span>
              </div>
              
              <!-- Entity Information -->
              <div v-if="source.entities && source.entities.length > 0" class="entities-list">
                <div class="entities-header">Entities:</div>
                <div v-for="entity in source.entities" :key="entity.name" 
                     class="entity-item"
                     @click.stop="selectEntity(entity)"
                     :class="{ 'active-entity': selectedEntity?.id === entity.id }"
                     :style="{ cursor: 'pointer' }">
                  <div class="entity-name">{{ entity.name }}</div>
                  <div class="entity-description">{{ entity.description }}</div>
                  
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <p>No sources available</p>
          </div>
        </div>

        <div class="config-form">
          <div class="form-group">
            <label>Current Selection:</label>
            <div class="current-selection">
              <div v-if="selectedSource" class="selection-item">
                <strong>Source:</strong> {{ selectedSource.name }}
                <button @click="selectSource(selectedSource)" class="deselect-btn" title="Click to deselect">
                  ×
                </button>
              </div>
              <div v-if="selectedEntity" class="selection-item">
                <strong>Entity:</strong> {{ selectedEntity.name }}
                <button @click="selectEntity(selectedEntity)" class="deselect-btn" title="Click to deselect">
                  ×
                </button>
              </div>
              <div v-else class="selection-item">
                <em>Please select an entity from the source above</em>
              </div>
            </div>
          </div>
          
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="config.useAI">
              Use AI Suggestions
            </label>
            <small v-if="config.useAI" class="ai-info">
              OpenAI API key required in backend/.env
            </small>
          </div>
          
          <!-- Adjustable Confidence Threshold -->
          <div v-if="config.useAI" class="form-group">
            <label>Confidence Threshold: {{ config.confidenceThreshold }}%</label>
            <input 
              type="range" 
              min="0" 
              max="100" 
              step="5" 
              v-model.number="config.confidenceThreshold" 
              class="slider-input"
            >
            <small class="confidence-info">
              Only show AI suggestions with confidence ≥ {{ config.confidenceThreshold }}%.
            </small>
          </div>
          
          <button @click="processCuration" :disabled="!selectedEntity || !selectedSource || isLoading" class="btn btn-primary">
            {{ isLoading ? 'AI Processing...' : 'Process Curation' }}
          </button>
          
          <!-- AI Processing Status -->
          <div v-if="isLoading && config.useAI" class="ai-processing-status">
            <p>AI is analyzing your content and generating metadata suggestions...</p>
            <p><small>This may take 10-30 seconds depending on content length</small></p>
          </div>
          
          <!-- Manual Processing Status -->
          <div v-if="isLoading && !config.useAI" class="manual-processing-status">
            <p>Processing your content and preparing metadata fields...</p>
            <p><small>Preparing manual entry forms for all metadata fields</small></p>
          </div>
          
          <!-- AI Results Summary -->
          
          
          <!-- Manual Results Summary -->
          
        </div>

        
      </aside>

      <!-- Metadata Preview Panel -->
      <aside class="metadata-preview">
        <div v-if="selectedSource" class="section">
          <h2>Metadata Fields for {{ selectedSource.name }}</h2>
          <div class="suggestions-info">
            <div class="info-item">
              <strong>Source:</strong> {{ selectedSource.name }}
            </div>
            <div class="info-item">
              <strong>Entity:</strong> {{ selectedEntity?.name || 'Not selected' }}
            </div>
            <div class="info-item">
              <strong>Metadata Fields:</strong> {{ properties.length }} fields available
            </div>
          </div>
          
          <!-- Show Properties Summary -->
          <div class="properties-summary">
            <h4>Metadata Fields Overview</h4>
            <p style="color: #6b6b6b; margin-bottom: 1rem;">
              <strong>Ready to Process:</strong> {{ properties.length }} metadata fields are available for curation.
            </p>
            
            <!-- Quick Stats -->
            <div class="quick-stats">
              <div class="stat-item">
                <span class="stat-number">{{ properties.length }}</span>
                <span class="stat-label">Total Fields</span>
              </div>
            </div>
            
            <!-- Next Steps -->
            
          </div>
        </div>
      </aside>
    </div>

    <!-- Post-Curation View -->
    <div v-else class="post-curation-container">
      <main class="content">
        <div class="content-header">
          <h2>Page Content</h2>
          <button @click="resetToPreCuration" class="btn btn-secondary">
            Back to Setup
          </button>
        </div>
        
        <!-- Page Navigation Controls -->
        <div v-if="pages.length > 1" class="page-navigation">
          <button 
            @click="previousPage" 
            :disabled="currentPageIndex === 0"
            class="btn btn-secondary"
          >
            Previous Page
          </button>
          <span class="page-counter">
            Page {{ currentPageIndex + 1 }} of {{ pages.length }}
          </span>
          <button 
            @click="nextPage" 
            :disabled="currentPageIndex === pages.length - 1"
            class="btn btn-secondary"
          >
            Next Page
          </button>
        </div>
        
        <div v-if="!currentPage" class="empty-state">
          <h3>Select a page to view content</h3>
        </div>
        <div v-else class="page-content">
          <h3>{{ currentPage.title }}</h3>
          <div class="content-text" v-html="highlightedContent"></div>
        </div>
      </main>

      <aside class="curation-panel">

        <div v-if="selectedSource" class="section" style="margin-top: 2rem;">
          <h2>Metadata Fields for {{ selectedSource.name }}</h2>
          
          
          <!-- Bulk Operations -->
          <div class="bulk-operations">
            <button 
              @click="bulkAcceptAll" 
              :disabled="!hasPendingSuggestions"
              class="btn btn-success"
            >
              Accept All Pending
            </button>
            <button 
              @click="bulkRejectAll" 
              :disabled="!hasPendingSuggestions"
              class="btn btn-danger"
            >
              Reject All Pending
            </button>
            <span class="bulk-stats">
              {{ pendingSuggestionsCount }} pending suggestions
            </span>
          </div>
          
          <!-- Show message when no suggestions exist -->
          <div v-if="suggestions.length === 0" class="no-suggestions-message">
            <h4>No AI Suggestions Available</h4>
            <p style="color: #6b6b6b; margin-bottom: 1rem;">
              <strong>Manual Processing Mode:</strong> Since no AI suggestions were generated, you need to manually enter metadata for all {{ properties.length }} fields.
            </p>
            <div class="manual-entry-redirect">
              <p><strong>To enter metadata manually:</strong></p>
              <ol>
                <li>Go back to Pre-Curation view</li>
                <li>Uncheck the "Use AI" option</li>
                <li>Click "Process Curation" to generate manual entry forms</li>
                <li>Fill in all metadata fields manually</li>
              </ol>
              <button @click="resetToPreCuration" class="btn btn-primary">
                Back to Pre-Curation
              </button>
            </div>
          </div>
          
          <!-- Show Suggestions when they exist -->
          <div v-else>

            
            
            
            
            
            <div class="suggestions-list">
              <div v-for="sug in filteredAndSortedSuggestions" :key="sug.id" 
                   class="metadata-card"
                   @click="activateHighlight(sug.id)"
                   :class="{ 'active-highlight': activeHighlightId === sug.id }"
                   :style="{ cursor: 'pointer' }">
                
                <!-- Header Section -->
                <div class="card-header">
                  <div class="header-left">
                    <h3 class="property-name">{{ getPropertyName(sug.property_id) }}</h3>
                    <div class="header-badges">
                      <span v-if="isAIGenerated(sug)" class="ai-badge">AI</span>
                      <span v-if="sug.is_required" class="required-badge">Required</span>
                      <span v-if="isAIGenerated(sug)" class="confidence-badge" :title="getInterpreterRationale(sug)">
                        {{ getSuggestionConfidence(sug) }}%
                        <div class="confidence-tooltip">
                          <div class="tooltip-header">Confidence Analysis</div>
                          <div class="tooltip-rationale">{{ getInterpreterRationale(sug) }}</div>
                          <div v-if="getInterpreterTags(sug).length > 0" class="tooltip-tags">
                            <strong>Tags:</strong> {{ getInterpreterTags(sug).join(', ') }}
                          </div>
                        </div>
                      </span>
                    </div>
                  </div>
                  
                </div>

                <!-- Value Section -->
                <div class="value-section">
                  <div class="value-label">Suggested Value</div>
                  <div class="suggested-value">{{ renderSuggestionValue(sug) }}</div>
                </div>

                <!-- Evidence Section -->
                <div class="evidence-section">
                  <div v-if="sug.evidence" class="evidence-content">
                    <div class="evidence-header">
                      
                      <span class="evidence-label">Supporting Evidence</span>
                    </div>
                    <div class="evidence-text">{{ getSuggestionEvidence(sug) }}</div>
                  </div>
                  <div v-else class="evidence-missing">
                    <div class="evidence-header">
                      <span class="evidence-label">No Evidence Available</span>
                    </div>
                    <div class="evidence-text">Cannot curate without supporting evidence</div>
                  </div>
                </div>

                <!-- Reasoning Section -->
                <div v-if="sug.ai_generated && sug.reasoning" class="reasoning-section">
                  <div class="reasoning-content">
                    <div class="reasoning-header">
                      
                      <span class="reasoning-label">AI Reasoning</span>
                    </div>
                    <div class="reasoning-text">{{ getSuggestionReasoning(sug) }}</div>
                  </div>
                </div>

                <!-- Status Only (teardown) -->
                <div class="status-display" :class="getStatusClass(sug)">
                  {{ getSuggestionStatus(sug).toUpperCase() }}
                  <span v-if="isAIGenerated(sug) && getSuggestionStatus(sug) === 'accepted'" class="confidence-display">
                    ({{ getSuggestionConfidence(sug) }}% confidence)
                  </span>
                </div>

                <!-- Minimal Curation Actions -->
                <div class="action-buttons">
                  <button 
                    v-if="getSuggestionStatus(sug) === 'pending' && hasValidEvidence(sug)"
                    class="action-btn accept-btn" 
                    @click="acceptSuggestion(sug)"
                  >
                    Accept
                  </button>
                  <button 
                    v-if="getSuggestionStatus(sug) === 'pending' && hasValidEvidence(sug)"
                    class="action-btn reject-btn" 
                    @click="rejectSuggestion(sug)"
                  >
                    Reject
                  </button>
                  <button 
                    v-if="getSuggestionStatus(sug) === 'pending' && !hasValidEvidence(sug)"
                    class="action-btn disabled-btn" 
                    disabled
                    title="Cannot curate without evidence"
                  >
                    Add Evidence First
                  </button>
                  <div v-else class="status-display" :class="getStatusClass(sug)">
                    {{ getSuggestionStatus(sug).toUpperCase() }}
                    <span v-if="isAIGenerated(sug) && getSuggestionStatus(sug) === 'accepted'" class="confidence-display">
                      ({{ getSuggestionConfidence(sug) }}% confidence)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Manual Entry Section for Missing Properties -->
          <div v-if="missingProperties.length > 0" class="missing-properties-section">
            <h3>Manual Entry Required</h3>
            <p class="missing-info">
              {{ missingProperties.length }} field{{ missingProperties.length > 1 ? 's' : '' }} need{{ missingProperties.length === 1 ? 's' : '' }} manual input 
              (no AI suggestions{{ config.useAI ? ' or low confidence' : '' }})
            </p>
            
            <div class="manual-entry-forms">
              <div v-for="property in missingProperties" :key="property.id" class="manual-field-card">
                <div class="field-header">
                  <h4>{{ property.name }}</h4>
                  <span v-if="property.is_required" class="required-indicator">Required</span>
                  <span class="field-type">{{ property.type }}</span>
                </div>
                
                <!-- Choice-based properties -->
                <div v-if="property.type === 'MULTIPLE_CHOICE' || property.type === 'SINGLE_CHOICE' || property.type === 'BINARY'" class="field-input">
                  <label>Select Value:</label>
                  <select v-model="manualMetadata[property.id]" class="form-input">
                    <option value="">Select an option...</option>
                    <option v-for="opt in property.property_options" :key="opt.id" :value="opt.id">
                      {{ opt.name }}
                    </option>
                  </select>
                </div>
                
                <!-- Free text and numerical properties -->
                <div v-else class="field-input">
                  <label>Value:</label>
                  <input 
                    v-if="property.type === 'NUMERICAL'"
                    v-model="manualMetadata[property.id]" 
                    type="number" 
                    class="form-input"
                    :placeholder="`Enter ${property.name.toLowerCase()}`"
                  >
                  <textarea 
                    v-else
                    v-model="manualMetadata[property.id]" 
                    class="form-input" 
                    rows="2"
                    :placeholder="`Enter ${property.name.toLowerCase()}`"
                  ></textarea>
                </div>
                
                <!-- Notes field -->
                <div class="field-notes">
                  <label>Notes (optional):</label>
                  <textarea 
                    v-model="manualMetadataNotes[property.id]" 
                    class="form-input notes-input" 
                    rows="1"
                    :placeholder="`Add notes for ${property.name.toLowerCase()}`"
                  ></textarea>
                </div>
              </div>
              
              <!-- Manual entry actions -->
              <div class="manual-entry-actions">
                <button 
                  @click="saveManualMetadata" 
                  :disabled="!hasManualMetadataChanges"
                  class="btn btn-primary"
                >
                  Save Manual Entries
                </button>
                <button 
                  @click="clearManualMetadata" 
                  :disabled="!hasManualMetadataChanges"
                  class="btn btn-secondary"
                >
                  Clear Form
                </button>
                <div class="manual-stats">
                  {{ Object.keys(manualMetadata).filter(k => manualMetadata[k]).length }} of {{ missingProperties.length }} filled
                </div>
              </div>
            </div>
          </div>
        </div>

        
      </aside>
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
import { getProperties, getSuggestions, getSources, getEditions } from './api'

export default {
  name: 'App',
  components: {},
  data() {
    return {
      config: {
        useAI: false,
        confidenceThreshold: 70
      },
      pages: [],
      suggestions: [],
      properties: [],
      sources: [],
      selectedSource: null,
      selectedEntity: null,
      currentPageIndex: 0,
      isLoading: false,
      manualMetadata: {}, // For manual metadata input
      manualMetadataNotes: {}, // For notes on manual metadata
      editingSuggestion: null, // Currently editing suggestion
      showEditModal: false, // Edit modal visibility
      statusFilter: '', // Filter by suggestion status
      sourceFilter: '', // Filter by source
      sortBy: 'id', // Sort suggestions by
      activeHighlightId: null, // Currently active highlight
      hoveredHighlightId: null, // Currently hovered highlight
      
      isPublishing: false, // Flag for publishing process
      isLoadingSourceData: false, // Flag to prevent multiple source data loads
      currentView: 'pre', // 'pre' or 'post'
      hasProcessedContent: false, // Flag to indicate if content has been processed
      publishingStatus: { // Data for publishing status
        can_publish: false,
        validation_status: {
          required_fields: {
            total: 0,
            accepted: 0,
            with_evidence: 0
          }
        }
      },
      currentView: 'pre', // 'pre' or 'post'
      hasProcessedContent: false, // Flag to indicate if content has been processed
      
      // Header-related data
      showUserMenu: false,
      curation_client: false, // Will be set based on API availability
      ai_service: true, // Will be set based on AI service availability
      
    }
  },
  computed: {
    currentPage() {
      return this.pages[this.currentPageIndex] || null
    },
    hasManualMetadataChanges() {
      return Object.keys(this.manualMetadata).length > 0 || Object.keys(this.manualMetadataNotes).length > 0
    },
    hasProcessedContent() {
      return this.pages && this.pages.length > 0
    },
    isEditValid() {
      if (!this.editingSuggestion) return false
      
      const property = this.properties.find(p => p.id === this.editingSuggestion.property_id)
      if (!property) return false
      
      if (property.type === 'MULTIPLE_CHOICE' || property.type === 'SINGLE_CHOICE' || property.type === 'BINARY') {
        return this.editingSuggestion.property_option_id && this.editingSuggestion.property_option_id !== ''
      } else {
        return this.editingSuggestion.custom_value && this.editingSuggestion.custom_value.toString().trim() !== ''
      }
    },
    hasPendingSuggestions() {
      return this.pendingSuggestionsCount > 0
    },
    pendingSuggestionsCount() {
      return this.suggestions.filter(s => this.getSuggestionStatus(s) === 'pending').length
    },
    filteredAndSortedSuggestions() {
      // Remove duplicates by ID to prevent multiple entries
      const uniqueSuggestions = this.suggestions.filter((suggestion, index, self) => 
        index === self.findIndex(s => s.id === suggestion.id)
      )
      
      let filtered = [...uniqueSuggestions]
      
      // Apply status filter
      if (this.statusFilter) {
        filtered = filtered.filter(s => this.getSuggestionStatus(s) === this.statusFilter)
      }
      
      // Apply source filter
      if (this.sourceFilter) {
        filtered = filtered.filter(s => s.source_id === parseInt(this.sourceFilter))
      }
      
      // Apply confidence threshold filter for AI suggestions
      if (this.config.useAI && this.config.confidenceThreshold != null) {
        const confidenceThreshold = this.config.confidenceThreshold / 100
        const beforeCount = filtered.length
        const aiSuggestions = filtered.filter(s => s.ai_generated)
        
        // Simple debug logging
        console.log(`🎯 Filtering ${aiSuggestions.length} AI suggestions with ${this.config.confidenceThreshold}% threshold`)
        
        filtered = filtered.filter(s => {
          if (!s.ai_generated) return true // Keep non-AI suggestions
          return (s.confidence || 0) >= confidenceThreshold
        })
        
        console.log(`   • Result: ${filtered.length}/${beforeCount} suggestions shown`)
      }
      
      // Apply sorting
      filtered.sort((a, b) => {
        switch (this.sortBy) {
          case 'confidence':
            return (b.confidence || 0) - (a.confidence || 0)
          case 'status':
            return this.getSuggestionStatus(a).localeCompare(this.getSuggestionStatus(b))
          case 'property':
            return this.getPropertyName(a.property_id).localeCompare(this.getPropertyName(b.property_id))
          case 'id':
          default:
            return a.id - b.id
        }
      })
      
      // Debug logging
      if (this.suggestions.length !== uniqueSuggestions.length) {
        console.warn(`Duplicate suggestions detected: ${this.suggestions.length} total, ${uniqueSuggestions.length} unique`)
      }
      
      return filtered
    },
    missingProperties() {
      if (!this.properties || !this.properties.length) return []
      
      // If no AI processing, show all properties
      if (!this.config.useAI || !this.suggestions || !this.suggestions.length) {
        return this.properties
      }
      
      // Get properties that need manual input:
      // 1. Properties with no suggestions at all
      // 2. Properties with low-confidence AI suggestions (below fixed 70% threshold)
      const confidenceThreshold = this.config && this.config.confidenceThreshold != null 
        ? (this.config.confidenceThreshold / 100) 
        : 0.7
      
      return this.properties.filter(prop => {
        // Find suggestions for this property
        const propertySuggestions = this.suggestions.filter(s => s.property_id === prop.id)
        
        if (propertySuggestions.length === 0) {
          // No suggestions at all - needs manual input
          return true
        }
        
        // Check if all suggestions are low-confidence AI suggestions
        const hasHighConfidenceAI = propertySuggestions.some(s => 
          s.ai_generated && (s.confidence || 0) >= confidenceThreshold
        )
        
        // If no high-confidence AI suggestions, this property needs manual input
        return !hasHighConfidenceAI
      })
    },
    
    lowConfidenceFieldsCount() {
      if (!this.config.useAI || !this.properties || !this.suggestions) return 0
      
      // Count properties that have AI suggestions but are below fixed 70% threshold
      const confidenceThreshold = this.config && this.config.confidenceThreshold != null 
        ? (this.config.confidenceThreshold / 100) 
        : 0.7
      
      return this.properties.filter(prop => {
        const propertySuggestions = this.suggestions.filter(s => s.property_id === prop.id)
        return propertySuggestions.some(s => 
          s.ai_generated && (s.confidence || 0) < confidenceThreshold
        )
      }).length
    },

    currentPageHighlights() {
      if (!this.currentPage || !this.suggestions || !this.suggestions.length) return []
      
      // Get highlights for the current page
      return this.suggestions.filter(s => 
        s.page_url === this.currentPage.url && 
        s.evidence && 
        this.hasValidEvidence(s)
      ).map(s => ({
        id: s.id,
        property_name: this.getPropertyName(s.property_id),
        highlight_text: s.evidence.content || s.evidence,
        confidence: s.confidence || 0,
        status: s.status
      }))
    },
    highlightedContent() {
      if (!this.currentPage || !this.currentPage.text_content) return ''
      if (!this.suggestions || !Array.isArray(this.suggestions)) return this.currentPage.text_content
      
      let content = this.currentPage.text_content
      
      // Get AI suggestions with evidence for highlighting
      const aiSuggestions = this.suggestions.filter(s => 
        s.ai_generated && s.evidence && s.page_url === this.currentPage.url
      )
      
      if (aiSuggestions.length === 0) return content
      
      // Create highlighted content with evidence
      // Use a counter to ensure unique replacements
      let replacementCounter = 0
      
      for (let i = 0; i < aiSuggestions.length; i++) {
        const suggestion = aiSuggestions[i]
        const evidence = suggestion.evidence
        
        if (!evidence) continue
        
        // Get the evidence text - handle both string and object formats
        let evidenceText = ''
        if (typeof evidence === 'string') {
          evidenceText = evidence
        } else if (evidence.content) {
          evidenceText = evidence.content
        } else {
          continue // Skip if no evidence text
        }
        
        if (!evidenceText || !content.includes(evidenceText)) continue
        
        const propertyName = this.getPropertyName(suggestion.property_id)
        const highlightId = `highlight-${suggestion.id}-${replacementCounter}`
        const isActive = this.activeHighlightId === suggestion.id
        const isHovered = this.hoveredHighlightId === suggestion.id
        
        // Determine highlight color based on state
        let highlightColor = '#F0E6FF' // default (purple-tinted)
        if (isActive) {
          highlightColor = '#8B5CF6' // active (purple)
        } else if (isHovered) {
          highlightColor = '#C4B5FD' // hovered (lighter purple)
        }
        
        // Create a unique placeholder to avoid multiple replacements
        const placeholder = `__HIGHLIGHT_${suggestion.id}_${replacementCounter}__`
        content = content.replace(evidenceText, placeholder)
        
        // Replace the placeholder with the highlighted content
        content = content.replace(
          placeholder,
          `<span class="ai-highlight" 
                 id="${highlightId}" 
                 data-suggestion-id="${suggestion.id}"
                 data-evidence-text="${evidenceText.replace(/"/g, '&quot;')}"
                 style="background-color: ${highlightColor}; padding: 2px 4px; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;" 
                 title="${propertyName}: ${evidenceText}"
                 onclick="window.activateHighlight(${suggestion.id})"
                 onmouseenter="window.highlightEvidence(${suggestion.id})"
                 onmouseleave="window.unhighlightEvidence()">${evidenceText}</span>`
        )
        
        replacementCounter++
      }
      
      return content
    }
  },
  methods: {
    hasAIForProperty(propertyId) {
      try {
        if (!this.suggestions || !Array.isArray(this.suggestions)) return false
        return this.suggestions.some(s => s.property_id === propertyId && s.ai_generated)
      } catch (error) {
        console.warn('Error in hasAIForProperty:', error)
        return false
      }
    },
    
    hasLowConfidenceAI(propertyId) {
      try {
        if (!this.config.useAI || !this.suggestions || !Array.isArray(this.suggestions)) return false
        
        const confidenceThreshold = this.config && this.config.confidenceThreshold != null 
          ? (this.config.confidenceThreshold / 100) 
          : 0.7
        return this.suggestions.some(s => 
          s.property_id === propertyId && 
          s.ai_generated && 
          (s.confidence || 0) < confidenceThreshold
        )
      } catch (error) {
        console.warn('Error in hasLowConfidenceAI:', error)
        return false
      }
    },
    
    async processCuration() {
      if (!this.selectedEntity) {
        alert('Please select an entity first')
        return
      }
      
      if (!this.selectedSource) {
        alert('Please select a source first')
        return
      }
      
      // Select URL based on entity
      let urls = []
      if (this.selectedEntity.name === "Martha Ballard's Diary Online") {
        urls = ['https://dohistory.org/diary/about.html']
      } else {
        // Default to Atharvaveda for other entities
        urls = ['https://www.atharvavedapaippalada.uzh.ch/en.html']
      }
      console.log(`Processing ${this.selectedEntity.name} with URL: ${urls[0]}`)
      
      this.isLoading = true
      try {
        const response = await axios.post('/api/process-curation', {
          entity_name: this.selectedEntity.name,
          source_name: this.selectedSource.name,
          urls: urls,
          use_ai: this.config.useAI,
          source_id: this.selectedSource.id,
          edition_id: this.selectedEntity.editions[0].id
        })
        
        if (response.data.success) {
          this.pages = response.data.pages || []
          
          if (this.config.useAI) {
            // AI processing: filter suggestions based on confidence threshold
            const allSuggestions = response.data.suggestions || []
            const confidenceThreshold = 0.7 // Fixed threshold (70%)
            
            // Remove any duplicate suggestions by ID
            const uniqueAllSuggestions = allSuggestions.filter((suggestion, index, self) => 
              index === self.findIndex(s => s.id === suggestion.id)
            )
            
            if (allSuggestions.length !== uniqueAllSuggestions.length) {
              console.warn(`Duplicate suggestions in response: ${allSuggestions.length} total, ${uniqueAllSuggestions.length} unique`)
            }
            
            // Store all suggestions - filtering will be done by frontend based on threshold
            this.suggestions = uniqueAllSuggestions
            
            // Count AI suggestions
            const totalAISuggestions = allSuggestions.filter(s => s.ai_generated).length
            
            console.log(`AI processing complete: ${totalAISuggestions} total AI suggestions loaded`)
            console.log(`All suggestions stored - frontend will filter based on confidence threshold`)
            
            // Force a refresh of the suggestions to ensure they're displayed
            await this.$nextTick()
            
            // Don't reload from backend after AI processing - keep the filtered suggestions
            // This prevents low-confidence suggestions from reappearing
            console.log(`Keeping ${this.suggestions.length} filtered suggestions (confidence ≥ 70%)`)
            
            // Show summary of what was generated vs. what needs manual input
            const aiGeneratedCount = this.suggestions.filter(s => s.ai_generated).length
            const totalProperties = this.properties.length
            const manualFieldsCount = totalProperties - aiGeneratedCount
            
            console.log(`AI Summary: ${aiGeneratedCount} AI suggestions, ${manualFieldsCount} fields need manual input`)
          } else {
            // Manual processing: keep existing suggestions, add new pages
            console.log(`Manual processing complete: ${this.pages.length} pages loaded`)
          }
          
          this.currentPageIndex = 0
          this.hasProcessedContent = true // Set flag to true after processing
          this.currentView = 'post' // Auto-switch to Post-Curation
          
          // Show success message
          if (this.config.useAI) {
            const allSuggestions = response.data.suggestions || []
            const totalAISuggestions = allSuggestions.filter(s => s.ai_generated).length
            alert(`AI processing complete.\n\nTotal AI suggestions: ${totalAISuggestions}\nUse the confidence slider to filter suggestions.\nThreshold currently set to: ${this.config.confidenceThreshold}%`)
          }
        }
      } catch (error) {
        console.error('Error:', error)
        alert(`Error during processing: ${error.message}`)
      } finally {
        this.isLoading = false
      }
    },
    async fetchMetadata() {
      // Fetch properties & suggestions from backend
      try {
        this.properties = await getProperties()
        this.suggestions = await getSuggestions()
        this.sources = await getSources()
      } catch (err) {
        console.error('Failed fetching metadata', err)
      }
    },
    selectSource(source) {
      // If clicking the same source, deselect it
      if (this.selectedSource && this.selectedSource.id === source.id) {
        this.selectedSource = null
        this.selectedEntity = null
        this.config.sourceName = ''
        this.suggestions = []
        this.pages = []
        this.currentPageIndex = 0
        this.hasProcessedContent = false
        return
      }
      
      // Select the new source
      this.selectedSource = source
      this.selectedEntity = null // Reset entity selection when source changes
      this.config.sourceName = source.name
      // Load editions and suggestions for this source
      this.loadSourceData(source.id)
    },
    
    selectEntity(entity) {
      // If clicking the same entity, deselect it
      if (this.selectedEntity && this.selectedEntity.id === entity.id) {
        this.selectedEntity = null
        return
      }
      
      // Select the new entity
      this.selectedEntity = entity
      console.log('Selected entity:', entity)
    },
    async loadSourceData(sourceId) {
      try {
        // Prevent multiple rapid calls to loadSourceData
        if (this.isLoadingSourceData) {
          console.log(`Already loading source data for ${sourceId}, skipping...`)
          return
        }
        
        this.isLoadingSourceData = true
        
        const [editions, sourceSuggestions] = await Promise.all([
          getEditions({ source_id: sourceId }),
          getSuggestions({ source_id: sourceId })
        ])
        
        // Only show existing suggestions for this source (no mixing with dummy data)
        const filteredSuggestions = sourceSuggestions.filter(s => s.source_id === sourceId)
        
        // Remove duplicates by ID
        const uniqueSuggestions = filteredSuggestions.filter((suggestion, index, self) => 
          index === self.findIndex(s => s.id === suggestion.id)
        )
        
        if (filteredSuggestions.length !== uniqueSuggestions.length) {
          console.warn(`Duplicate suggestions in source data: ${filteredSuggestions.length} total, ${uniqueSuggestions.length} unique`)
        }
        
        this.suggestions = uniqueSuggestions
        console.log(`Loaded ${this.suggestions.length} unique suggestions for source ${sourceId}`)
      } catch (err) {
        console.error('Failed loading source data:', err)
        this.suggestions = []
      } finally {
        this.isLoadingSourceData = false
      }
    },

    
    getPropertyName(id) {
      const p = this.properties.find(pr => pr.id === id)
      return p ? p.name : `Property ${id}`
    },
    renderSuggestionValue(sug) {
      if (sug.custom_value) return sug.custom_value
      const prop = this.properties.find(p => p.id === sug.property_id)
      if (!prop) return ''
      const opt = prop.property_options.find(o => o.id === sug.property_option_id)
      return opt ? opt.name : ''
    },
    getSuggestionConfidence(sug) {
      return sug.confidence ? Math.round(sug.confidence * 100) : 0
    },
    getInterpreterRationale(sug) {
      if (sug.agentB_rationale) {
        return sug.agentB_rationale
      }
      return 'Confidence calculated by single-pass AI system'
    },
    getInterpreterTags(sug) {
      if (sug.agentB_tags) {
        return sug.agentB_tags
      }
      return []
    },
    getSuggestionEvidence(sug) {
      if (!sug.evidence) return 'No evidence provided'
      
      if (typeof sug.evidence === 'string') {
        return sug.evidence
      }
      
      if (sug.evidence.content) {
        let evidence = sug.evidence.content
        if (evidence.length > 100) {
          evidence = evidence.substring(0, 100) + '...'
        }
        return evidence
      }
      
      return 'Evidence available but no content'
    },
    getSuggestionReasoning(sug) {
      if (!sug.reasoning) return 'No reasoning provided'
      
      if (typeof sug.reasoning === 'string') {
        let reasoning = sug.reasoning
        if (reasoning.length > 150) {
          reasoning = reasoning.substring(0, 150) + '...'
        }
        return reasoning
      }
      
      return 'Reasoning available but no content'
    },
    isAIGenerated(sug) {
      return sug.ai_generated || false
    },
    acceptSuggestion(sug) {
      this.curateSuggestion(sug.id, 'accept')
    },
    rejectSuggestion(sug) {
      this.curateSuggestion(sug.id, 'reject')
    },
    async curateSuggestion(suggestionId, action) {
      try {
        const response = await axios.post(`/api/suggestions/${suggestionId}/curate`, {
          action: action,
          note: `Curator ${action}ed this suggestion`
        })
        
        if (response.data.success) {
          // Update the suggestion in our local state
          const index = this.suggestions.findIndex(s => s.id === suggestionId)
          if (index !== -1) {
            this.suggestions[index] = response.data.suggestion
          }
          
          // Show success message
          const actionText = action === 'accept' ? 'Accepted' : action === 'reject' ? 'Rejected' : 'Edited'
          console.log(`${actionText} suggestion ${suggestionId}`)
        }
      } catch (error) {
        console.error(`Failed to ${action} suggestion:`, error)
      }
    },
    getSuggestionStatus(sug) {
      return sug.status || 'pending'
    },
    getStatusClass(sug) {
      const status = this.getSuggestionStatus(sug)
      switch (status) {
        case 'accepted': return 'status-accepted'
        case 'rejected': return 'status-rejected'
        case 'edited': return 'status-edited'
        default: return 'status-pending'
      }
    },
    selectPage(index) {
      this.currentPageIndex = index
    },
         editSuggestion(sug) {
       // Open edit modal for the suggestion
       this.editingSuggestion = { ...sug }
       this.showEditModal = true
     },
    async saveManualMetadata() {
      try {
        // Get the current source and edition IDs
        const sourceId = this.selectedSource?.id || 1
        const editionId = 1 // Default to first edition for now
        
        // Process each property that has manual metadata
        const promises = []
        
        for (const [propertyId, value] of Object.entries(this.manualMetadata)) {
          if (value !== '' && value !== null && value !== undefined) {
            const payload = {
              source_id: sourceId,
              edition_id: editionId,
              property_id: parseInt(propertyId),
              note: this.manualMetadataNotes[propertyId] || '',
              evidence: {
                content: this.manualMetadataNotes[propertyId] || 'Manual entry by curator',
                source_url: window.location.href,
                confidence: 100.0,
                extraction_method: 'manual'
              }
            }
            
            // Add the appropriate field based on property type
            const property = this.properties.find(p => p.id === parseInt(propertyId))
            if (property) {
              if (property.type === 'MULTIPLE_CHOICE' || property.type === 'SINGLE_CHOICE' || property.type === 'BINARY') {
                payload.property_option_id = value
              } else {
                payload.custom_value = value
              }
            }
            
            promises.push(axios.post('/api/manual-metadata', payload))
          }
        }
        
        if (promises.length > 0) {
          await Promise.all(promises)
          console.log(`Saved ${promises.length} manual metadata entries`)
          
          // Refresh suggestions to show the new manual entries
          await this.loadSourceData(sourceId)
        }
        
        this.clearManualMetadata() // Clear form after saving
      } catch (error) {
        console.error('Failed to save manual metadata:', error)
      }
    },
         clearManualMetadata() {
       this.manualMetadata = {}
       this.manualMetadataNotes = {}
       console.log('Manual metadata form cleared.')
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
         
         // Add the appropriate field based on property type
         const property = this.properties.find(p => p.id === this.editingSuggestion.property_id)
         if (property) {
           if (property.type === 'MULTIPLE_CHOICE' || property.type === 'SINGLE_CHOICE' || property.type === 'BINARY') {
             payload.property_option_id = this.editingSuggestion.property_option_id
           } else {
             payload.custom_value = this.editingSuggestion.custom_value
           }
         }
         
         const response = await axios.put(`/api/suggestions/${this.editingSuggestion.id}/edit`, payload)
         
         if (response.data.success) {
           // Update the suggestion in our local state
           const index = this.suggestions.findIndex(s => s.id === this.editingSuggestion.id)
           if (index !== -1) {
             this.suggestions[index] = response.data.suggestion
           }
           
           console.log('Suggestion edited successfully')
           this.closeEditModal()
         }
       } catch (error) {
         console.error('Failed to edit suggestion:', error)
       }
     },
     
     // Helper methods for edit modal
     getPropertyType(propertyId) {
       const prop = this.properties.find(p => p.id === propertyId)
       return prop ? prop.type : 'Unknown'
     },
     
     isChoiceProperty(propertyId) {
       const prop = this.properties.find(p => p.id === propertyId)
       return prop && (prop.type === 'MULTIPLE_CHOICE' || prop.type === 'SINGLE_CHOICE' || prop.type === 'BINARY')
     },
     
     isNumericalProperty(propertyId) {
       const prop = this.properties.find(p => p.id === propertyId)
       return prop && prop.type === 'NUMERICAL'
     },
     
     getPropertyOptions(propertyId) {
       const prop = this.properties.find(p => p.id === propertyId)
       return prop ? prop.property_options || [] : []
     },
     
     // Highlighting methods
     highlightEvidence(suggestionId) {
       this.hoveredHighlightId = suggestionId
     },
     
     unhighlightEvidence() {
       this.hoveredHighlightId = null
     },
     
     activateHighlight(suggestionId) {
       this.activeHighlightId = suggestionId
     },
     
     deactivateHighlight() {
       this.activeHighlightId = null
     },
     
     // Bulk operations
     async bulkAcceptAll() {
       if (!this.hasPendingSuggestions) return
       
       const pendingSuggestions = this.suggestions.filter(s => this.getSuggestionStatus(s) === 'pending')
       
       try {
         const promises = pendingSuggestions.map(suggestion => 
           this.curateSuggestion(suggestion.id, 'accept')
         )
         
         await Promise.all(promises)
         console.log(`Accepted ${pendingSuggestions.length} suggestions`)
       } catch (error) {
         console.error('Failed to bulk accept suggestions:', error)
       }
     },
     
     async bulkRejectAll() {
       if (!this.hasPendingSuggestions) return
       
       const pendingSuggestions = this.suggestions.filter(s => this.getSuggestionStatus(s) === 'pending')
       
       try {
         const promises = pendingSuggestions.map(suggestion => 
           this.curateSuggestion(suggestion.id, 'reject')
         )
         
         await Promise.all(promises)
         console.log(`Rejected ${pendingSuggestions.length} suggestions`)
       } catch (error) {
         console.error('Failed to bulk reject suggestions:', error)
       }
     },

    async publishEdition() {
      if (!this.selectedEntity) {
        alert('Please select an entity first to publish.')
        return
      }

      try {
        this.isPublishing = true
        const response = await axios.post(`/api/editions/${this.selectedEntity.id}/publish`, {
          edition_id: this.selectedEntity.id
        })

        if (response.data.success) {
          this.publishingStatus = response.data.publishing_status
          alert('Edition published successfully!')
          console.log('Edition published:', response.data.publishing_status)
          // Refresh suggestions and properties after publishing
          await this.loadSourceData(this.selectedSource.id)
          await this.fetchMetadata()
        } else {
          alert('Failed to publish edition: ' + response.data.error)
          console.error('Failed to publish edition:', response.data.error)
        }
      } catch (error) {
        console.error('Error publishing edition:', error)
        alert('Error publishing edition: ' + error.message)
      } finally {
        this.isPublishing = false
      }
    },

    

    hasValidEvidence(sug) {
      // Handle both string and object evidence formats
      if (typeof sug.evidence === 'string') {
        return sug.evidence && sug.evidence.trim() !== ''
      }
      return sug.evidence && typeof sug.evidence === 'object' && sug.evidence.content
    },
     
     // Page Navigation Methods
     nextPage() {
       if (this.currentPageIndex < this.pages.length - 1) {
         this.currentPageIndex++
         this.activeHighlightId = null // Reset highlight when changing pages
       }
     },
     
     previousPage() {
       if (this.currentPageIndex > 0) {
         this.currentPageIndex--
         this.activeHighlightId = null // Reset highlight when changing pages
       }
     },
     
     // Publishing Status Methods
     async updatePublishingStatus() {
       if (!this.selectedEntity) return
       
       try {
         const response = await axios.get(`/api/editions/${this.selectedEntity.id}/publishing-status`)
         if (response.data) {
           this.publishingStatus = response.data
         }
       } catch (error) {
         console.error('Failed to update publishing status:', error)
       }
     },
     
     // Enhanced Curation with Evidence Validation
     async curateSuggestion(suggestionId, action) {
       try {
         const response = await axios.post(`/api/suggestions/${suggestionId}/curate`, {
           action: action,
           note: `Curator ${action}ed this suggestion`,
           user_id: 'curator_' + Date.now() // Mock user ID
         })
         
         if (response.data.success) {
           // Update the suggestion in our local state
           const index = this.suggestions.findIndex(s => s.id === suggestionId)
           if (index !== -1) {
             this.suggestions[index] = response.data.suggestion
           }
           
           // Update publishing status after curation
           await this.updatePublishingStatus()
           
           // Show success message
           const actionText = action === 'accept' ? 'Accepted' : action === 'reject' ? 'Rejected' : 'Edited'
           console.log(`${actionText} suggestion ${suggestionId}`)
         } else {
           // Handle evidence validation errors
           if (response.data.error && response.data.error.includes('evidence')) {
             alert(`${response.data.error}\n\n${response.data.details || 'Please add evidence before curating this suggestion.'}`)
           } else {
             alert(`Failed to ${action} suggestion: ${response.data.error}`)
           }
         }
       } catch (error) {
         console.error(`Failed to ${action} suggestion:`, error)
         if (error.response?.data?.error) {
           alert(`Error: ${error.message}`)
         } else {
           alert(`Error: ${error.message}`)
         }
       }
     },
     switchToPostCuration() {
       this.currentView = 'post'
       this.activeHighlightId = null // Reset highlight in post-curation view
     },
     loadSources() {
       this.fetchMetadata() // Re-fetch metadata to show all properties
     },
     
     switchToPostCuration() {
       this.currentView = 'post'
       this.activeHighlightId = null // Reset highlight in post-curation view
     },
     
     resetToPreCuration() {
       this.currentView = 'pre'
       this.hasProcessedContent = false
       this.activeHighlightId = null // Reset highlight
       this.suggestions = [] // Clear suggestions
       this.pages = [] // Clear pages
       this.currentPageIndex = 0 // Reset page index
     },
     
     handleSuggestionReverted(suggestion) {
       // Update the suggestion in our local state after revert
       const index = this.suggestions.findIndex(s => s.id === suggestion.id)
       if (index !== -1) {
         this.suggestions[index] = suggestion
       }
       console.log('Suggestion reverted successfully')
     },
     
     saveManualEntries() {
       const filledFields = Object.keys(this.manualMetadata).filter(key => this.manualMetadata[key])
       const totalFields = this.properties.length
       
       if (filledFields.length === 0) {
         alert('Please fill in at least one metadata field before saving.')
         return
       }
       
       // Here you would typically send the data to your backend
      console.log('Saving manual entries:', {
        metadata: this.manualMetadata,
        notes: this.manualMetadataNotes,
        filledFields: filledFields.length,
        totalFields: totalFields
      })
      
      alert(`Saved ${filledFields.length} of ${totalFields} metadata fields.\n\nYou can switch back to Pre-Curation or continue with manual entry.`)
    },

    // Header Methods
    goToOverview() {
      // Navigate to project overview page
      if (confirm('Are you sure you want to return to the project overview? Any unsaved changes will be lost.')) {
        // In a real application, this would navigate to a different route
        // For now, we'll just reset the application state
        this.resetToPreCuration()
        alert('Returned to project overview. In a full application, this would navigate to the overview page.')
      }
    },

    toggleView() {
      if (this.currentView === 'pre') {
        this.switchToPostCuration()
      } else {
        this.resetToPreCuration()
      }
    },

    showSettings() {
      this.showUserMenu = false
      alert('Settings panel would open here. This would include:\n\n• AI model configuration\n• API endpoint settings\n• Export preferences\n• Language settings')
    },

    showHelp() {
      this.showUserMenu = false
      alert('Help & Documentation would open here. This would include:\n\n• User guide\n• Video tutorials\n• API documentation\n• Contact support')
    },

    exportData() {
      this.showUserMenu = false
      try {
        const exportData = {
          sources: this.sources,
          suggestions: this.suggestions,
          properties: this.properties,
          timestamp: new Date().toISOString(),
          user: 'Alihan Karataşlı'
        }
        
        const dataStr = JSON.stringify(exportData, null, 2)
        const dataBlob = new Blob([dataStr], { type: 'application/json' })
        const url = URL.createObjectURL(dataBlob)
        
        const link = document.createElement('a')
        link.href = url
        link.download = `metadata-curation-export-${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
        
        alert('Data exported successfully!')
      } catch (error) {
        console.error('Export failed:', error)
        alert('Export failed. Please try again.')
      }
    },

    logout() {
      this.showUserMenu = false
      if (confirm('Are you sure you want to logout? Any unsaved changes will be lost.')) {
        // In a real application, this would clear session and redirect to login
        alert('Logout successful. In a full application, you would be redirected to the login page.')
        // Reset application state
        this.resetToPreCuration()
      }
    }
  },
  
  beforeDestroy() {
    // Clean up global functions
    delete window.highlightEvidence
    delete window.unhighlightEvidence
    delete window.activateHighlight
  },
  
  created() {
    // Preload metadata lists once the component is created
    this.fetchMetadata()
    
    // Add global functions for highlight event handling
    window.highlightEvidence = (suggestionId) => {
      this.highlightEvidence(suggestionId)
    }
    
    window.unhighlightEvidence = () => {
      this.unhighlightEvidence()
    }
    
    window.activateHighlight = (suggestionId) => {
      this.activateHighlight(suggestionId)
    }
    
    // Close user menu when clicking outside
    document.addEventListener('click', (event) => {
      if (this.showUserMenu && !event.target.closest('.user-profile') && !event.target.closest('.user-dropdown')) {
        this.showUserMenu = false
      }
    })
  }
}
</script>

<style>
.audit-log-btn {
  background: #17a2b8;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
  margin-right: 12px;
}

.audit-log-btn:hover {
  background: #138496;
}
</style>
