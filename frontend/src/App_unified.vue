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
              <span class="icon">⚙️</span>
            </button>
          </div>

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

    <!-- Unified Control Panel -->
    <div class="control-panel">
      <div class="control-row">
        <!-- Entity Selection -->
        <div class="control-group">
          <label for="entity-select">Select Entity:</label>
          <select 
            id="entity-select" 
            v-model="selectedEntityId" 
            @change="onEntityChange"
            :disabled="isLoading"
            class="entity-select"
          >
            <option value="">Choose an entity...</option>
            <optgroup v-for="source in sources" :key="source.id" :label="source.name">
              <option 
                v-for="edition in source.editions" 
                :key="edition.id" 
                :value="edition.id"
              >
                {{ edition.entity_name }}
              </option>
            </optgroup>
          </select>
        </div>

        <!-- AI Toggle -->
        <div class="control-group">
          <label class="ai-toggle-label">
            <input 
              type="checkbox" 
              v-model="useAI" 
              @change="onAIToggleChange"
              :disabled="isLoading || !selectedEntityId"
              class="ai-checkbox"
            >
            <span class="ai-toggle-text">Use AI Suggestions</span>
          </label>
          <div v-if="useAI" class="ai-info">
            AI will analyze scraped content and suggest values
          </div>
        </div>

        <!-- Status Indicator -->
        <div class="control-group status-group">
          <div class="status-indicator" :class="statusClass">
            <span class="status-dot"></span>
            <span class="status-text">{{ statusText }}</span>
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
          <div class="empty-icon">📄</div>
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
            <div class="content-text" v-html="highlightedContent"></div>
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
          <div class="empty-icon">📋</div>
          <h3>Metadata Fields</h3>
          <p>Select an entity to see metadata fields for curation.</p>
        </div>
        
        <div v-else class="metadata-content">
          <!-- Mode Indicator -->
          <div class="mode-indicator" :class="useAI ? 'ai-mode' : 'manual-mode'">
            <img :src="useAI ? '/src/assets/icons/artificial-intelligence.png' : '/src/assets/icons/filling-form.png'" class="mode-icon" alt="Mode icon" />
            <span class="mode-text">{{ useAI ? 'AI Suggestion Mode' : 'Manual Curation Mode' }}</span>
          </div>

          <!-- Metadata Fields List -->
          <div class="metadata-fields">
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
                <h3 class="field-name">{{ field.name }}</h3>
                <div class="field-badges">
                  <span v-if="field.is_required" class="required-badge">Required</span>
                  <span class="field-type-badge">{{ field.type }}</span>
                  <span v-if="field.aiSuggestion" class="ai-badge">AI</span>
                  <span v-if="field.aiSuggestion && field.aiSuggestion.confidence" class="confidence-badge">
                    {{ Math.round(field.aiSuggestion.confidence * 100) }}%
                  </span>
                </div>
              </div>

              <!-- AI Suggestion Section (when AI is enabled and suggestion exists) -->
              <div v-if="useAI && field.aiSuggestion" class="ai-suggestion-section">
                <div class="suggestion-value">
                  <strong>AI Suggested Value:</strong>
                  <span class="suggested-value">{{ renderSuggestionValue(field.aiSuggestion) }}</span>
                </div>
                
                <div v-if="field.aiSuggestion.evidence" class="suggestion-evidence">
                  <strong>Evidence:</strong>
                  <span class="evidence-text">{{ getSuggestionEvidence(field.aiSuggestion) }}</span>
                </div>
                
                <div v-if="field.aiSuggestion.reasoning" class="suggestion-reasoning">
                  <strong>AI Reasoning:</strong>
                  <span class="reasoning-text">{{ getSuggestionReasoning(field.aiSuggestion) }}</span>
                </div>

                <!-- AI Suggestion Actions -->
                <div class="suggestion-actions">
                  <button 
                    v-if="field.aiSuggestion.status === 'pending'"
                    @click.stop="acceptSuggestion(field.aiSuggestion)"
                    class="action-btn accept-btn"
                  >
                    Accept
                  </button>
                  <button 
                    v-if="field.aiSuggestion.status === 'pending'"
                    @click.stop="rejectSuggestion(field.aiSuggestion)"
                    class="action-btn reject-btn"
                  >
                    Reject
                  </button>
                  <button 
                    v-if="field.aiSuggestion.status === 'pending'"
                    @click.stop="editSuggestion(field.aiSuggestion)"
                    class="action-btn edit-btn"
                  >
                    Edit
                  </button>
                  <div v-else class="status-display" :class="getStatusClass(field.aiSuggestion)">
                    {{ field.aiSuggestion.status.toUpperCase() }}
                  </div>
                </div>
              </div>

              <!-- Manual Entry Section (always visible for manual mode, or when no AI suggestion) -->
              <div v-if="!useAI || !field.aiSuggestion || field.aiSuggestion.status === 'rejected'" class="manual-entry-section">
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

          <!-- Bulk Actions (only when AI suggestions exist) -->
          <div v-if="useAI && aiSuggestions.length > 0" class="bulk-actions">
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
      selectedEntityId: null,
      selectedEntity: null,
      selectedSource: null,
      
      // UI state
      useAI: false,
      isLoading: false,
      showUserMenu: false,
      
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
    currentPage() {
      return this.scrapedContent.pages[this.currentPageIndex] || null
    },
    
    metadataFields() {
      if (!this.properties.length) return []
      
      return this.properties.map(property => {
        // Find AI suggestion for this property
        const aiSuggestion = this.aiSuggestions.find(s => s.property_id === property.id)
        
        return {
          ...property,
          aiSuggestion: aiSuggestion || null,
          manualValue: this.manualValues[property.id] || ''
        }
      })
    },
    
    hasPendingSuggestions() {
      return this.pendingSuggestionsCount > 0
    },
    
    pendingSuggestionsCount() {
      return this.aiSuggestions.filter(s => s.status === 'pending').length
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
      
      // Start scraping immediately
      await this.scrapeContent()
    },
    
    async onAIToggleChange() {
      if (this.selectedEntityId) {
        // Re-scrape with new AI setting
        await this.scrapeContent()
      }
    },
    
    async scrapeContent() {
      if (!this.selectedEntityId) return
      
      this.isLoading = true
      this.statusText = this.useAI ? 'Scraping & AI Processing...' : 'Scraping Content...'
      this.statusClass = 'status-loading'
      
      try {
        const response = await axios.post(`/api/entities/${this.selectedEntityId}/scrape`, {
          use_ai: this.useAI
        })
        
        if (response.data.success) {
          this.scrapedContent = response.data.scraped_content
          this.aiSuggestions = response.data.suggestions.items || []
          this.currentPageIndex = 0
          
          // Reset manual values when switching modes
          this.manualValues = {}
          
          this.statusText = this.useAI ? 
            `Scraped ${this.scrapedContent.total_pages} pages, ${this.aiSuggestions.length} AI suggestions` :
            `Scraped ${this.scrapedContent.total_pages} pages - Ready for manual curation`
          this.statusClass = 'status-success'
          
          console.log('Scraping completed:', {
            pages: this.scrapedContent.total_pages,
            ai_suggestions: this.aiSuggestions.length,
            ai_enabled: this.useAI
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
    
    getSuggestionEvidence(suggestion) {
      if (!suggestion.evidence) return 'No evidence'
      if (typeof suggestion.evidence === 'string') return suggestion.evidence
      if (suggestion.evidence.content) {
        const content = suggestion.evidence.content
        return content.length > 100 ? content.substring(0, 100) + '...' : content
      }
      return 'Evidence available'
    },
    
    getSuggestionReasoning(suggestion) {
      if (!suggestion.reasoning) return 'No reasoning provided'
      const reasoning = suggestion.reasoning
      return reasoning.length > 150 ? reasoning.substring(0, 150) + '...' : reasoning
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
          console.log(`${action}ed suggestion ${suggestionId}`)
        }
      } catch (error) {
        console.error(`Failed to ${action} suggestion:`, error)
        alert(`Failed to ${action} suggestion: ${error.response?.data?.error || error.message}`)
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
          // Clear the field after saving
          this.clearManualField(field)
          alert(`Saved ${field.name} successfully!`)
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

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f8f9fa;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
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

/* Control panel */
.control-panel {
  background: white;
  padding: 1.5rem 2rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  border-bottom: 1px solid #eee;
}

.control-row {
  display: flex;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
  max-width: 1400px;
  margin: 0 auto;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-group label {
  font-weight: 500;
  font-size: 0.9rem;
  color: #555;
}

.entity-select {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  font-size: 1rem;
  min-width: 300px;
  background: white;
}

.entity-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 0.5rem;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e0e0e0;
  border-top: 2px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
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
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  flex: 1;
}

.content-panel, .metadata-panel {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  height: fit-content;
  max-height: 80vh;
}

.panel-header {
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  padding: 3rem 2rem;
  text-align: center;
  color: #666;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  margin-bottom: 0.5rem;
  color: #333;
}

.empty-state p {
  font-size: 0.9rem;
}

/* Content display */
.content-display {
  flex: 1;
  overflow-y: auto;
}

.page-navigation {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-btn {
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover:not(:disabled) {
  background: #e9ecef;
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-counter {
  font-weight: 500;
  color: #666;
}

.page-content {
  padding: 1.5rem;
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
}

.ai-highlight {
  cursor: pointer;
  transition: all 0.2s ease;
}

.ai-highlight:hover {
  background-color: #C4B5FD !important;
}

/* Metadata content */
.metadata-content {
  flex: 1;
  overflow-y: auto;
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
  width: 28px;
  height: 28px;
  vertical-align: middle;
  margin-right: 0.5rem;
}

/* Metadata fields */
.metadata-fields {
  padding: 1rem;
}

.metadata-field-card {
  margin-bottom: 1rem;
  padding: 1.5rem;
  border: 1px solid #eee;
  border-radius: 0.5rem;
  transition: all 0.2s;
}

.metadata-field-card:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.metadata-field-card.has-ai-suggestion {
  border-left: 4px solid #2196f3;
}

.metadata-field-card.has-manual-value {
  border-left: 4px solid #9c27b0;
}

.metadata-field-card.is-required {
  border-top: 2px solid #f44336;
}

.metadata-field-card.active-highlight {
  border-color: #8B5CF6;
  background: #F3F4F6;
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 1rem;
}

.field-name {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.field-badges {
  display: flex;
  gap: 0.5rem;
}

.required-badge, .field-type-badge, .ai-badge, .confidence-badge {
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
  font-weight: 500;
}

.required-badge {
  background: #ffebee;
  color: #c62828;
}

.field-type-badge {
  background: #f3e5f5;
  color: #7b1fa2;
}

.ai-badge {
  background: #e3f2fd;
  color: #1976d2;
}

.confidence-badge {
  background: #e8f5e8;
  color: #2e7d32;
}

/* AI Suggestion Section */
.ai-suggestion-section {
  background: #f8f9ff;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.suggestion-value {
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
}

.suggested-value {
  font-weight: 600;
  color: #1976d2;
}

.suggestion-evidence, .suggestion-reasoning {
  margin-bottom: 0.75rem;
  font-size: 0.85rem;
  color: #666;
}

.evidence-text, .reasoning-text {
  display: block;
  margin-top: 0.25rem;
  font-style: italic;
}

.suggestion-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.action-btn {
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.accept-btn {
  background: #4caf50;
  color: white;
}

.accept-btn:hover {
  background: #45a049;
}

.reject-btn {
  background: #f44336;
  color: white;
}

.reject-btn:hover {
  background: #da190b;
}

.edit-btn {
  background: #ff9800;
  color: white;
}

.edit-btn:hover {
  background: #f57c00;
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

.status-pending {
  background: #f3e5f5;
  color: #7b1fa2;
}

/* Manual Entry Section */
.manual-entry-section {
  background: #fafafa;
  padding: 1rem;
  border-radius: 0.5rem;
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
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 0.25rem;
  font-size: 0.9rem;
}

.form-select:focus, .form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
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
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn {
  background: #4caf50;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #45a049;
}

.clear-btn {
  background: #f8f9fa;
  color: #666;
  border: 1px solid #ddd;
}

.clear-btn:hover:not(:disabled) {
  background: #e9ecef;
}

.save-btn:disabled, .clear-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Bulk actions */
.bulk-actions {
  padding: 1rem 1.5rem;
  border-top: 1px solid #eee;
  display: flex;
  gap: 1rem;
}

.bulk-btn {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.accept-all-btn {
  background: #4caf50;
  color: white;
}

.accept-all-btn:hover:not(:disabled) {
  background: #45a049;
}

.reject-all-btn {
  background: #f44336;
  color: white;
}

.reject-all-btn:hover:not(:disabled) {
  background: #da190b;
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
@media (max-width: 1024px) {
  .main-content {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .control-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .status-group {
    margin-left: 0;
  }
}

@media (max-width: 768px) {
  .control-panel {
    padding: 1rem;
  }
  
  .main-content {
    padding: 1rem;
  }
  
  .entity-select {
    min-width: auto;
    width: 100%;
  }
  
  .user-info {
    display: none;
  }
}
</style>
