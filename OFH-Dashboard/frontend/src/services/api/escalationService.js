import axios from 'axios'

class EscalationService {
  constructor() {
    // Safely get environment variable with fallback
    this.baseURL = (typeof process !== 'undefined' && process.env?.REACT_APP_API_URL) || 'http://localhost:5000'
    // Use global axios instance (which has the interceptor) instead of creating a new one
    this.api = axios
  }

  // Create escalation workflow
  async createEscalationWorkflow(workflow) {
    try {
      const response = await this.api.post(`${this.baseURL}/api/escalations/workflows`, {
        name: workflow.name,
        description: workflow.description,
        triggers: workflow.triggers,
        steps: workflow.steps,
        conditions: workflow.conditions,
        isActive: workflow.isActive !== false
      })

      return {
        success: true,
        workflow: response.data
      }
    } catch (error) {
      console.error('🚨 Failed to create escalation workflow:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Update escalation workflow
  async updateEscalationWorkflow(workflowId, workflow) {
    try {
      const response = await this.api.put(`${this.baseURL}/api/escalations/workflows/${workflowId}`, workflow)
      return {
        success: true,
        workflow: response.data
      }
    } catch (error) {
      console.error('🚨 Failed to update escalation workflow:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Delete escalation workflow
  async deleteEscalationWorkflow(workflowId) {
    try {
      await this.api.delete(`${this.baseURL}/api/escalations/workflows/${workflowId}`)
      return { success: true }
    } catch (error) {
      console.error('🚨 Failed to delete escalation workflow:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Get all escalation workflows
  async getEscalationWorkflows() {
    try {
      const response = await this.api.get(`${this.baseURL}/api/escalations/workflows`)
      return {
        success: true,
        workflows: response.data
      }
    } catch (error) {
      console.error('🚨 Failed to get escalation workflows:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Get escalation workflow by ID
  async getEscalationWorkflow(workflowId) {
    try {
      const response = await this.api.get(`${this.baseURL}/api/escalations/workflows/${workflowId}`)
      return {
        success: true,
        workflow: response.data
      }
    } catch (error) {
      console.error('🚨 Failed to get escalation workflow:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Trigger escalation manually
  async triggerEscalation(alertId, workflowId, options = {}) {
    try {
      const response = await this.api.post(`${this.baseURL}/api/escalations/trigger`, {
        alertId,
        workflowId,
        options
      })

      return {
        success: true,
        escalation: response.data
      }
    } catch (error) {
      console.error('🚨 Failed to trigger escalation:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Get escalation status
  async getEscalationStatus(escalationId) {
    try {
      const response = await this.api.get(`${this.baseURL}/api/escalations/status/${escalationId}`)
      return {
        success: true,
        status: response.data
      }
    } catch (error) {
      console.error('🚨 Failed to get escalation status:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Cancel escalation
  async cancelEscalation(escalationId, reason) {
    try {
      const response = await this.api.post(`${this.baseURL}/api/escalations/cancel/${escalationId}`, {
        reason
      })

      return {
        success: true,
        result: response.data
      }
    } catch (error) {
      console.error('🚨 Failed to cancel escalation:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Get escalation history
  async getEscalationHistory(filters = {}) {
    try {
      const response = await this.api.get(`${this.baseURL}/api/escalations/history`, {
        params: filters
      })

      return {
        success: true,
        history: response.data
      }
    } catch (error) {
      console.error('🚨 Failed to get escalation history:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Get escalation statistics
  async getEscalationStats(timeRange = '24h') {
    try {
      const response = await this.api.get(`${this.baseURL}/api/escalations/stats?range=${timeRange}`)
      return {
        success: true,
        stats: response.data
      }
    } catch (error) {
      console.error('🚨 Failed to get escalation stats:', error)
      // Return default stats if API fails
      return {
        success: true,
        stats: {
          escalationRate: 0,
          avgResponseTime: 0,
          totalEscalations: 0
        }
      }
    }
  }

  // Test escalation workflow
  async testEscalationWorkflow(workflowId, testData) {
    try {
      const response = await this.api.post(`${this.baseURL}/api/escalations/test/${workflowId}`, testData)
      return {
        success: true,
        result: response.data
      }
    } catch (error) {
      console.error('🚨 Failed to test escalation workflow:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Get escalation templates
  async getEscalationTemplates() {
    try {
      const response = await this.api.get(`${this.baseURL}/api/escalations/templates`)
      return {
        success: true,
        templates: response.data
      }
    } catch (error) {
      console.error('🚨 Failed to get escalation templates:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Create escalation template
  async createEscalationTemplate(template) {
    try {
      const response = await this.api.post(`${this.baseURL}/api/escalations/templates`, template)
      return {
        success: true,
        template: response.data
      }
    } catch (error) {
      console.error('🚨 Failed to create escalation template:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }
}

// Create singleton instance
const escalationService = new EscalationService()

export default escalationService
