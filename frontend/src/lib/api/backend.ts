/**
 * Portal Messenger Backend API Client
 * Handles all REST API calls to the backend for data persistence
 */

export interface Message {
	id: string;
	origin: string;
	destination: string;
	type: 'rx' | 'tx';
	time: string;
	text: string;
	status?: string;
	error?: string;
	unread?: boolean;
}

export interface Setting {
	setting: string;
	value: string;
	label: string;
	default: string;
	required: boolean;
	options?: string[] | null;
	display: boolean;
	restart: boolean;
	valid?: boolean;
}

export interface ConversationUnreadStatus {
	unread: boolean;
}

export interface ConversationUnreadCount {
	count: number;
}

class BackendAPI {
	private baseURL: string;

	constructor() {
		// Auto-detect backend URL from where frontend was served
		if (typeof window !== 'undefined') {
			const protocol = window.location.protocol;
			const hostname = window.location.hostname;
			const port = window.location.port;
			this.baseURL = `${protocol}//${hostname}${port ? ':' + port : ''}`;
		} else {
			this.baseURL = '';
		}
	}

	/**
	 * Get all conversations
	 */
	async getConversations(): Promise<any[]> {
		const response = await fetch(`${this.baseURL}/api/conversations`);
		if (!response.ok) {
			throw new Error(`Failed to get conversations: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Get conversation messages between local callsign and specified callsign
	 */
	async getConversation(callsign: string, limit = 50, before?: string): Promise<Message[]> {
		const params = new URLSearchParams({ limit: limit.toString() });
		if (before) {
			params.append('before', before);
		}
		
		const response = await fetch(`${this.baseURL}/api/conversation/${encodeURIComponent(callsign)}?${params}`);
		if (!response.ok) {
			throw new Error(`Failed to get conversation: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Get count of conversations with unread messages
	 */
	async getConversationUnreadCount(): Promise<ConversationUnreadCount> {
		const response = await fetch(`${this.baseURL}/api/conversation/unread`);
		if (!response.ok) {
			throw new Error(`Failed to get unread count: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Check if specific conversation has unread messages
	 */
	async getConversationUnreadStatus(callsign: string): Promise<ConversationUnreadStatus> {
		const response = await fetch(`${this.baseURL}/api/conversation/unread/${encodeURIComponent(callsign)}`);
		if (!response.ok) {
			throw new Error(`Failed to get unread status: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Mark all messages in conversation as read
	 */
	async markConversationRead(callsign: string): Promise<{ updated: number }> {
		const response = await fetch(`${this.baseURL}/api/conversation/read/${encodeURIComponent(callsign)}`, {
			method: 'PATCH'
		});
		if (!response.ok) {
			throw new Error(`Failed to mark conversation read: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Delete all messages in conversation
	 */
	async deleteConversation(callsign: string): Promise<{ deleted: number }> {
		const response = await fetch(`${this.baseURL}/api/conversation/${encodeURIComponent(callsign)}`, {
			method: 'DELETE'
		});
		if (!response.ok) {
			throw new Error(`Failed to delete conversation: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Get specific message by ID
	 */
	async getMessage(id: string): Promise<Message> {
		const response = await fetch(`${this.baseURL}/api/messages/${encodeURIComponent(id)}`);
		if (!response.ok) {
			throw new Error(`Failed to get message: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Store new message (typically from pyjs8call events)
	 */
	async createMessage(messageData: Partial<Message> & { timestamp: number }): Promise<Message> {
		const response = await fetch(`${this.baseURL}/api/messages`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(messageData)
		});
		if (!response.ok) {
			throw new Error(`Failed to create message: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Update existing message
	 */
	async updateMessage(id: string, updates: Partial<Message>): Promise<Message> {
		const response = await fetch(`${this.baseURL}/api/messages/${encodeURIComponent(id)}`, {
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(updates)
		});
		if (!response.ok) {
			throw new Error(`Failed to update message: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Delete message by ID
	 */
	async deleteMessage(id: string): Promise<{ deleted: boolean }> {
		const response = await fetch(`${this.baseURL}/api/messages/${encodeURIComponent(id)}`, {
			method: 'DELETE'
		});
		if (!response.ok) {
			throw new Error(`Failed to delete message: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Get all settings
	 */
	async getAllSettings(): Promise<Setting[]> {
		const response = await fetch(`${this.baseURL}/api/settings`);
		if (!response.ok) {
			throw new Error(`Failed to get settings: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Get specific setting by key
	 */
	async getSetting(key: string): Promise<Setting> {
		const response = await fetch(`${this.baseURL}/api/settings/${encodeURIComponent(key)}`);
		if (!response.ok) {
			throw new Error(`Failed to get setting: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Update specific setting value
	 */
	async updateSetting(key: string, value: string): Promise<Setting> {
		const response = await fetch(`${this.baseURL}/api/settings/${encodeURIComponent(key)}`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ value })
		});
		if (!response.ok) {
			throw new Error(`Failed to update setting: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Update multiple settings at once
	 */
	async updateMultipleSettings(settings: Record<string, string>): Promise<Setting[]> {
		const response = await fetch(`${this.baseURL}/api/settings`, {
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(settings)
		});
		if (!response.ok) {
			throw new Error(`Failed to update settings: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Health check endpoint
	 */
	async getStatus(): Promise<{ status: string; service: string; timestamp: string }> {
		const response = await fetch(`${this.baseURL}/api/status`);
		if (!response.ok) {
			throw new Error(`Failed to get status: ${response.status}`);
		}
		return await response.json();
	}
}

// Export singleton instance
export const backendAPI = new BackendAPI();