import axios from 'axios'

class MessagingService {
  constructor() {
    // Safely get environment variable with fallback
    this.baseURL = (typeof process !== 'undefined' && process.env?.REACT_APP_API_URL) || 'http://localhost:5000'
    // Use global axios instance (which has the interceptor) instead of creating a new one
    this.api = axios
  }

  // Email notification methods
  async sendEmail(notification) {
    try {
      const response = await this.api.post(`${this.baseURL}/api/notifications/email`, {
        to: notification.recipients.email,
        subject: notification.subject,
        body: notification.body,
        template: notification.template,
        priority: notification.priority || 'normal',
        attachments: notification.attachments || [],
        metadata: notification.metadata || {}
      })

      return {
        success: true,
        messageId: response.data.messageId,
        deliveryStatus: response.data.deliveryStatus
      }
    } catch (error) {
      console.error('📧 Email sending failed:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // SMS notification methods
  async sendSMS(notification) {
    try {
      const response = await this.api.post(`${this.baseURL}/api/notifications/sms`, {
        to: notification.recipients.sms,
        message: notification.message,
        priority: notification.priority || 'normal',
        metadata: notification.metadata || {}
      })

      return {
        success: true,
        messageId: response.data.messageId,
        deliveryStatus: response.data.deliveryStatus
      }
    } catch (error) {
      console.error('📱 SMS sending failed:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Multi-channel notification
  async sendMultiChannel(notification) {
    const results = {
      email: null,
      sms: null,
      webhook: null
    }

    // Send email if recipients specified
    if (notification.recipients.email) {
      results.email = await this.sendEmail(notification)
    }

    // Send SMS if recipients specified
    if (notification.recipients.sms) {
      results.sms = await this.sendSMS(notification)
    }

    // Send webhook if configured
    if (notification.recipients.webhook) {
      results.webhook = await this.sendWebhook(notification)
    }

    return results
  }

  // Webhook notification
  async sendWebhook(notification) {
    try {
      const response = await this.api.post(`${this.baseURL}/api/notifications/webhook`, {
        url: notification.recipients.webhook,
        payload: notification.payload,
        headers: notification.headers || {},
        retryPolicy: notification.retryPolicy || { maxRetries: 3, delay: 1000 }
      })

      return {
        success: true,
        response: response.data
      }
    } catch (error) {
      console.error('🔗 Webhook sending failed:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Get delivery status
  async getDeliveryStatus(messageId) {
    try {
      const response = await this.api.get(`${this.baseURL}/api/notifications/status/${messageId}`)
      return response.data
    } catch (error) {
      console.error('📊 Failed to get delivery status:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Get notification templates
  async getTemplates() {
    try {
      const response = await this.api.get(`${this.baseURL}/api/notifications/templates`)
      return response.data
    } catch (error) {
      console.error('📝 Failed to get templates:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Create notification template
  async createTemplate(template) {
    try {
      const response = await this.api.post(`${this.baseURL}/api/notifications/templates`, template)
      return response.data
    } catch (error) {
      console.error('📝 Failed to create template:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Update notification template
  async updateTemplate(templateId, template) {
    try {
      const response = await this.api.put(`${this.baseURL}/api/notifications/templates/${templateId}`, template)
      return response.data
    } catch (error) {
      console.error('📝 Failed to update template:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Delete notification template
  async deleteTemplate(templateId) {
    try {
      const response = await this.api.delete(`${this.baseURL}/api/notifications/templates/${templateId}`)
      return response.data
    } catch (error) {
      console.error('📝 Failed to delete template:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Test notification delivery
  async testNotification(notification) {
    try {
      const response = await this.api.post(`${this.baseURL}/api/notifications/test`, notification)
      return response.data
    } catch (error) {
      console.error('🧪 Test notification failed:', error)
      return {
        success: false,
        error: error.response?.data?.message || error.message
      }
    }
  }

  // Get notification statistics
  async getNotificationStats(timeRange = '24h') {
    try {
      const response = await this.api.get(`${this.baseURL}/api/notifications/stats?range=${timeRange}`)
      return response.data
    } catch (error) {
      console.error('📊 Failed to get notification stats:', error)
      // Return default stats if API fails
      return {
        success: true,
        totalNotifications: 0,
        deliveryRate: 0,
        avgResponseTime: 0
      }
    }
  }
}

// Create singleton instance
const messagingService = new MessagingService()

export default messagingService
