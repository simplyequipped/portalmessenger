/**
 * Message store for managing messages in conversations
 */
import { writable, derived } from 'svelte/store';
import { backendAPI } from '$lib/api/backend.ts';
import { pyjs8callAPI } from '$lib/api/pyjs8call.ts';
import { updateStationFromMessage } from './stations.js';

// Store for messages keyed by callsign for caching
// Structure: { callsign: [messages...] }
export const messageStore = writable({});

// Currently selected conversation's messages
export const selectedMessages = writable([]);

// Message sending status
export const sendingMessages = writable({}); // { messageId: 'queued' | 'sending' | 'sent' | 'failed' }

// Removed: messageIdMapping - no longer needed without temp IDs

// Derived store for messages with sending status
export const messagesWithStatus = derived(
	[selectedMessages, sendingMessages],
	([$selectedMessages, $sendingMessages]) => {
		return $selectedMessages.map(msg => ({
			...msg,
			sendingStatus: $sendingMessages[msg.id] || null
		}));
	}
);

/**
 * Load messages for a specific conversation
 */
export async function loadMessages(callsign, limit = 50, before = null) {
	try {
		const messages = await backendAPI.getConversation(callsign, limit, before);
		
		// Update message store cache
		messageStore.update(store => ({
			...store,
			[callsign]: messages
		}));

		// Update selected messages if this is the active conversation
		selectedMessages.set(messages);
		
		return messages;
	} catch (error) {
		console.error(`Failed to load messages for ${callsign}:`, error);
		throw error;
	}
}

/**
 * Add a new message to the store (from WebSocket events)
 */
export function addMessage(message) {
	const { origin, destination, time } = message;
	
	// Determine which conversation this belongs to
	// For received messages, conversation is with the origin
	// For sent messages, conversation is with the destination
	const conversationWith = message.type === 'rx' ? origin : destination;
	
	// Update station data to create conversation
	if (message.type === 'rx') {
		// For incoming messages, update the station
		updateStationFromMessage({
			origin: message.origin,
			timestamp: new Date(message.time).getTime() / 1000
		});
	}
	
	// Update message store
	messageStore.update(store => {
		const existing = store[conversationWith] || [];
		
		// Check if message already exists (prevent duplicates)
		if (existing.find(m => m.id === message.id)) {
			return store;
		}
		
		// Insert message in chronological order
		const updated = [...existing, message].sort((a, b) => 
			new Date(a.time).getTime() - new Date(b.time).getTime()
		);
		
		return {
			...store,
			[conversationWith]: updated
		};
	});
	
	// Update selected messages if this conversation is active
	selectedMessages.update(current => {
		// Check if we need to update (current conversation)
		if (current.length === 0) return current;
		
		// Assuming we can determine current conversation from first message
		const currentConversation = current[0]?.origin === conversationWith || 
								   current[0]?.destination === conversationWith;
		
		if (!currentConversation) return current;
		
		// Add message if not already present
		if (current.find(m => m.id === message.id)) return current;
		
		return [...current, message].sort((a, b) => 
			new Date(a.time).getTime() - new Date(b.time).getTime()
		);
	});
}

/**
 * Send a message via pyjs8call
 */
export async function sendMessage(destination, text) {
	try {
		// Send via pyjs8call API first - no optimistic UI updates
		const response = await pyjs8callAPI.sendDirectedMessage(destination, text);
		
		// Create message data for backend storage
		const messageData = {
			id: response.id,
			origin: response.origin,
			destination: response.destination,
			type: response.type.substring(0, 2).toLowerCase(), // Convert TX.* -> tx, RX.* -> rx
			timestamp: response.timestamp,
			text: response.text,
			status: response.status
		};
		
		// Store in backend
		await backendAPI.createMessage(messageData);
		
		// Create message object for UI
		const message = {
			...messageData,
			time: new Date(messageData.timestamp * 1000).toISOString()
		};
		
		// Add message to UI with real ID
		addMessage(message);
		
		// Set initial status (message accepted by pyjs8call)
		sendingMessages.update(status => {
			const updated = {
				...status,
				[response.id]: 'queued'
			};
			return updated;
		});
		
		return response;
		
	} catch (error) {
		console.error('Failed to send message:', error);
		throw error;
	}
}

/**
 * Update message status (from WebSocket events)
 */
export function updateMessageStatus(messageId, status) {
	// Update status for the given message ID (real IDs only)
	sendingMessages.update(statuses => {
		const updated = {
			...statuses,
			[messageId]: status
		};
		return updated;
	});
	
	// Auto-cleanup "sent" status after 10 seconds
	if (status === 'sent') {
		setTimeout(() => {
			sendingMessages.update(statuses => {
				const newStatuses = { ...statuses };
				delete newStatuses[messageId];
				return newStatuses;
			});
		}, 10000);
	}
	
	// Update message in store
	messageStore.update(store => {
		const updatedStore = { ...store };
		
		for (const callsign in updatedStore) {
			const messages = updatedStore[callsign];
			const messageIndex = messages.findIndex(m => m.id === messageId);
			
			if (messageIndex !== -1) {
				updatedStore[callsign] = [
					...messages.slice(0, messageIndex),
					{ ...messages[messageIndex], status },
					...messages.slice(messageIndex + 1)
				];
				break;
			}
		}
		
		return updatedStore;
	});
	
	// Update selected messages if needed
	selectedMessages.update(messages => 
		messages.map(msg => 
			msg.id === messageId ? { ...msg, status } : msg
		)
	);
}

/**
 * Resend a failed message
 */
export async function resendMessage(messageId, destination, text) {
	try {
		// Remove the old failed status
		sendingMessages.update(status => {
			const { [messageId]: removed, ...rest } = status;
			return rest;
		});
		
		// Send the message again
		await sendMessage(destination, text);
		
	} catch (error) {
		console.error('Failed to resend message:', error);
		throw error;
	}
}

/**
 * Select messages for a specific conversation
 */
export function selectConversation(callsign) {
	messageStore.subscribe(store => {
		const messages = store[callsign] || [];
		selectedMessages.set(messages);
	})();
}

/**
 * Clear message cache for a conversation
 */
export function clearConversationMessages(callsign) {
	messageStore.update(store => {
		const { [callsign]: removed, ...rest } = store;
		return rest;
	});
}

/**
 * Get cached messages for a conversation
 */
export function getCachedMessages(callsign) {
	let messages = [];
	messageStore.subscribe(store => {
		messages = store[callsign] || [];
	})();
	return messages;
}

