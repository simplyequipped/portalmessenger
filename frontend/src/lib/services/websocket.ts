/**
 * WebSocket service for real-time pyjs8call integration
 * Handles incoming messages, status updates, and connection management
 */

import { get } from 'svelte/store';
import { pyjs8callAPI } from '$lib/api/pyjs8call.ts';
import { backendAPI } from '$lib/api/backend.ts';
import { addMessage, updateMessageStatus } from '$lib/stores/messages.js';
import { 
	updateStationFromSpot, 
	updateStationFromMessage, 
	incrementUnreadCount, 
	loadConversations, 
	loadInitialStations,
	initializePresenceFromMessages 
} from '$lib/stores/stations.js';
import { 
	startConnectionMonitoring,
	establishWebSocketConnection 
} from '$lib/stores/connection.js';
import { loadSettings, settings } from '$lib/stores/settings.js';

class WebSocketService {
	private initialized = false;
	private connectionMonitorCleanup: (() => void) | null = null;

	/**
	 * Initialize WebSocket service and connection monitoring
	 */
	async initialize() {
		if (this.initialized) {
			return;
		}
		
		try {
			// Settings should already be loaded by the layout
			// Load existing conversations from backend
			await loadConversations();
			
			// Load initial stations from pyjs8call spots using aging setting  
			let agingSeconds = 900; // Default 15 minutes in seconds
			
			// Get current settings value
			const currentSettings = get(settings);
			if (currentSettings.aging?.value) {
				agingSeconds = currentSettings.aging.value * 60; // Convert minutes to seconds
			}
			
			await loadInitialStations(agingSeconds);
			
			// Initialize presence data from stored messages
			await initializePresenceFromMessages();
			
			// Set up WebSocket event handlers
			this.setupEventHandlers();
			
			// Establish initial WebSocket connection
			await establishWebSocketConnection();
			
			// Start connection monitoring (status reporting only)
			this.connectionMonitorCleanup = startConnectionMonitoring();
			
			this.initialized = true;
			
		} catch (error) {
			console.error('Failed to initialize WebSocket service:', error);
		}
	}

	/**
	 * Set up event handlers for pyjs8call WebSocket events
	 */
	private setupEventHandlers() {
		// Incoming message events
		pyjs8callAPI.on('incoming_message', this.handleIncomingMessage.bind(this));
		
		// Outgoing message status events  
		pyjs8callAPI.on('outgoing_status', this.handleOutgoingStatus.bind(this));
		
		// Activity events
		pyjs8callAPI.on('new_spots', this.handleSpot.bind(this));
		
		// Inbox events
		pyjs8callAPI.on('inbox_message', this.handleInboxMessage.bind(this));
		
		// Window transition events
		pyjs8callAPI.on('window_transition', this.handleWindowTransition.bind(this));
		
		// WebSocket event handlers set up
	}

	/**
	 * Handle incoming messages from pyjs8call
	 */
	private async handleIncomingMessage(data: any) {
		try {
			// Check if message is addressed to us
			let currentSettings = null;
			settings.subscribe(s => currentSettings = s)();
			
			const localCallsign = currentSettings?.callsign?.value || '';
			const configuredGroups = currentSettings?.groups?.value ? 
				currentSettings.groups.value.split(',').map(g => g.trim()) : [];
			
			// Only process messages addressed to our callsign or configured groups
			const isAddressedToUs = data.destination === localCallsign || 
				configuredGroups.includes(data.destination);
			
			if (!isAddressedToUs) {
				// Message not for us, ignore
				return;
			}
			
			// Create message object for backend storage
			const messageData = {
				id: data.id,
				origin: data.origin,
				destination: data.destination, 
				type: data.type,
				timestamp: data.timestamp,
				text: data.text,
				status: data.status || 'received'
			};
			
			// Store in backend
			await backendAPI.createMessage(messageData);
			
			// Add to local message store
			const localMessage = {
				...messageData,
				time: new Date(data.timestamp * 1000).toISOString(),
				unread: true
			};
			
			addMessage(localMessage);
			
			// Update station data with message info
			updateStationFromMessage(messageData);
			
			// Increment unread count
			incrementUnreadCount(data.origin, 1);
			
		} catch (error) {
			console.error('Failed to handle incoming message:', error);
		}
	}

	/**
	 * Handle outgoing message status updates
	 */
	private handleOutgoingStatus(data: any) {
		try {
			// Update message status in local store
			updateMessageStatus(data.id, data.status);
			
		} catch (error) {
			console.error('Failed to handle outgoing status:', error);
		}
	}

	/**
	 * Handle spot events (station activity)
	 */
	private handleSpot(data: any) {
		try {
			// Handle spots array from new_spots event
			const spots = data.spots || [];
			for (const spot of spots) {
				// Update station data for Activity page
				if (spot.origin) {
					updateStationFromSpot(spot);
				}
			}
			
		} catch (error) {
			console.error('Failed to handle spots:', error);
		}
	}

	/**
	 * Handle inbox messages
	 */
	private handleInboxMessage(data: any) {
		try {
			//TODO Handle inbox messages
		} catch (error) {
			console.error('Failed to handle inbox message:', error);
		}
	}

	/**
	 * Handle window transitions (RX/TX state changes)
	 */
	private handleWindowTransition(data: any) {
		try {
			//TODO Handle RX/TX window transitions
		} catch (error) {
			console.error('Failed to handle window transition:', error);
		}
	}

	/**
	 * Clean up WebSocket service
	 */
	destroy() {
		if (this.connectionMonitorCleanup) {
			this.connectionMonitorCleanup();
			this.connectionMonitorCleanup = null;
		}
		
		// Disconnect WebSocket
		pyjs8callAPI.disconnectWebSocket();
		
		this.initialized = false;
		// WebSocket service destroyed
	}

	/**
	 * Get initialization status
	 */
	isInitialized(): boolean {
		return this.initialized;
	}

}

// Export singleton instance
export const websocketService = new WebSocketService();