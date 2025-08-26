/**
 * Unified station store - manages all station data for activity and conversations
 */
import { writable, derived } from 'svelte/store';
import { pyjs8callAPI } from '$lib/api/pyjs8call.ts';
import { backendAPI } from '$lib/api/backend.ts';
import { settings } from './settings.js';

// Core station data store
// Structure: { callsign: { callsign, lastHeard, lastMessage, hasMessages, unreadCount, grid, snr, speed, hearing, heardBy } }
export const stations = writable({});

// Selection states
export const selectedCallsign = writable(null);  // For conversations view
export const selectedStation = writable(null);   // For activity view

// Loading states
export const stationsLoading = writable(false);

// Activity sorting functions
const sortingFunctions = {
	recent: (a, b) => new Date(b.lastHeard || 0).getTime() - new Date(a.lastHeard || 0).getTime(),
	nearest: (a, b) => (a.distance || Infinity) - (b.distance || Infinity),
	furthest: (a, b) => (b.distance || 0) - (a.distance || 0),
	'hearing most': (a, b) => (b.hearing?.length || 0) - (a.hearing?.length || 0),
	'most heard': (a, b) => (b.heardBy?.length || 0) - (a.heardBy?.length || 0)
};

// Derived store for activity view - all stations with dynamic sorting
export const activityStations = derived(
	[stations, settings],
	([$stations, $settings]) => {
		const sortOption = $settings['activity-sort']?.value || 'recent';
		const sortFn = sortingFunctions[sortOption] || sortingFunctions.recent;
		
		return Object.values($stations).sort(sortFn);
	}
);

// Derived store for conversations view - only stations with messages
export const conversationStations = derived(
	stations,
	($stations) => {
		return Object.values($stations)
			.filter(station => station.hasMessages)
			.map(station => ({
				...station,
				lastMessageTime: station.lastMessage // Alias for compatibility
			}))
			.sort((a, b) => {
				// Sort by unread first, then by last message time
				if (a.unreadCount !== b.unreadCount) {
					return b.unreadCount - a.unreadCount;
				}
				return new Date(b.lastMessage || 0).getTime() - new Date(a.lastMessage || 0).getTime();
			});
	}
);

// Total unread message count
export const totalUnreadCount = derived(
	stations,
	($stations) => {
		return Object.values($stations).reduce((sum, station) => sum + (station.unreadCount || 0), 0);
	}
);

// Legacy alias for existing components
export const stationsSorted = activityStations;
export const conversationsWithUnread = conversationStations;

/**
 * Update station data (core function for all updates)
 */
export function updateStation(callsign, updates) {
	stations.update(current => {
		const existing = current[callsign] || { 
			callsign,
			lastHeard: null,
			lastMessage: null,
			hasMessages: false,
			unreadCount: 0,
			grid: null,
			snr: null,
			speed: null,
			hearing: [],
			heardBy: [],
			distance: null,
			distanceUnits: null,
			bearing: null
		};
		
		return {
			...current,
			[callsign]: {
				...existing,
				...updates
			}
		};
	});
}

/**
 * Load distance data for a station with a grid square
 */
async function loadDistanceForStation(callsign, grid) {
	if (!grid) return;
	
	try {
		const distanceData = await pyjs8callAPI.getGridDistance(grid);
		if (distanceData && distanceData.success) {
			updateStation(callsign, {
				distance: distanceData.distance,
				distanceUnits: distanceData.units,
				bearing: distanceData.bearing
			});
		}
	} catch (error) {
		console.error(`Failed to load distance for ${callsign}:`, error);
		// Don't throw - this is non-critical
	}
}

/**
 * Load hearing/heard-by data for a station
 */
async function loadHearingDataForStation(callsign) {
	try {
		// Get aging setting and calculate age parameter (aging * 4)
		let ageMinutes = undefined;
		settings.subscribe(current => {
			if (current.aging?.value) {
				ageMinutes = current.aging.value * 4;
			}
		})();
		
		const promises = [
			pyjs8callAPI.getStationHearing(callsign, ageMinutes).catch(() => []),
			pyjs8callAPI.getStationHeard(callsign, ageMinutes).catch(() => [])
		];
		
		const [hearingData, heardData] = await Promise.all(promises);
		
		updateStation(callsign, {
			hearing: hearingData.map(h => h.callsign || h),
			heardBy: heardData.map(h => h.callsign || h)
		});
		
	} catch (error) {
		console.error(`Failed to load hearing data for ${callsign}:`, error);
		// Don't throw - this is non-critical
	}
}

/**
 * Add or update station from spot events
 */
export function updateStationFromSpot(spotData) {
	const callsign = spotData.origin;
	const lastHeard = new Date(spotData.timestamp * 1000).toISOString();
	
	updateStation(callsign, {
		lastHeard,
		grid: spotData.grid,
		snr: spotData.snr,
		speed: spotData.speed
	});
	
	// Proactively load distance if grid exists
	if (spotData.grid) {
		loadDistanceForStation(callsign, spotData.grid);
	}
	
	// Proactively load hearing/heard-by data
	loadHearingDataForStation(callsign);
}

/**
 * Add or update station from message events
 */
export function updateStationFromMessage(messageData) {
	const callsign = messageData.origin;
	const timestamp = new Date(messageData.timestamp * 1000).toISOString();
	
	updateStation(callsign, {
		lastHeard: timestamp,
		lastMessage: timestamp,
		hasMessages: true
	});
}

/**
 * Update unread count for a station
 */
export function updateUnreadCount(callsign, count) {
	updateStation(callsign, { unreadCount: count });
}

/**
 * Increment unread count for a station
 */
export function incrementUnreadCount(callsign, increment = 1) {
	stations.update(current => {
		const existing = current[callsign];
		if (existing) {
			const newCount = (existing.unreadCount || 0) + increment;
			return {
				...current,
				[callsign]: {
					...existing,
					unreadCount: Math.max(0, newCount)
				}
			};
		}
		return current;
	});
}

/**
 * Select a conversation (for messages view)
 */
export function selectConversation(callsign) {
	selectedCallsign.set(callsign);
}

/**
 * Select a station (for activity view) 
 */
export function selectStation(callsign) {
	selectedStation.set(callsign);
}

/**
 * Delete a conversation and its station data
 */
export async function deleteConversation(callsign) {
	try {
		// Delete from backend
		await backendAPI.deleteConversation(callsign);
		
		// Remove from store
		stations.update(current => {
			const updated = { ...current };
			delete updated[callsign];
			return updated;
		});
		
		// Clear selection if this was selected
		selectedCallsign.update(current => current === callsign ? null : current);
		
	} catch (error) {
		console.error('Failed to delete conversation:', error);
		throw error;
	}
}

/**
 * Mark conversation as read
 */
export async function markConversationRead(callsign) {
	try {
		await backendAPI.markConversationRead(callsign);
		updateStation(callsign, { unreadCount: 0 });
	} catch (error) {
		console.error('Failed to mark conversation read:', error);
		throw error;
	}
}

/**
 * Load initial conversations from backend
 */
export async function loadConversations() {
	try {
		const conversations = await backendAPI.getConversations();
		
		for (const conv of conversations) {
			updateStation(conv.callsign, {
				hasMessages: true,
				lastMessage: conv.lastMessageTime,
				unreadCount: conv.unreadCount || 0
			});
		}
		
	} catch (error) {
		console.error('Failed to load conversations:', error);
		throw error;
	}
}

/**
 * Load initial stations from pyjs8call spots API
 */
export async function loadInitialStations(ageSeconds = 900) {
	try {
		const spots = await pyjs8callAPI.getSpots(ageSeconds);
		
		for (const spot of spots) {
			if (spot.origin) {
				updateStationFromSpot(spot);
			}
		}
		
	} catch (error) {
		console.error('Failed to load initial stations:', error);
	}
}

/**
 * Get station data from store (data is loaded proactively when spots are received)
 */
export async function loadStationDetails(callsign) {
	try {
		stationsLoading.set(true);
		
		// Just return the current station data from store
		let station = null;
		stations.subscribe(current => {
			station = current[callsign] || null;
		})();
		
		return station;
		
	} catch (error) {
		console.error(`Failed to get station details for ${callsign}:`, error);
		throw error;
	} finally {
		stationsLoading.set(false);
	}
}

/**
 * Clear all station data
 */
export function clearStations() {
	stations.set({});
	selectedCallsign.set(null);
	selectedStation.set(null);
}

/**
 * Get station data for specific callsign
 */
export function getStation(callsign) {
	let station = null;
	stations.subscribe(current => {
		station = current[callsign] || null;
	})();
	return station;
}

/**
 * Presence calculation functions
 */
export function calculatePresenceStatus(lastHeardTimestamp) {
	if (!lastHeardTimestamp) return 'unknown';
	
	const minutesAgo = Math.floor((Date.now() - new Date(lastHeardTimestamp).getTime()) / (1000 * 60));
	
	if (minutesAgo < 10) return 'active';    // Green - heard within 10 minutes
	if (minutesAgo < 60) return 'inactive';  // Yellow - heard within 1 hour
	return 'unknown';                        // Gray - heard over 1 hour ago
}

export function formatLastHeard(lastHeardTimestamp) {
	if (!lastHeardTimestamp) return 'Never';
	
	const minutesAgo = Math.floor((Date.now() - new Date(lastHeardTimestamp).getTime()) / (1000 * 60));
	
	if (minutesAgo < 1) return 'Now';
	if (minutesAgo < 60) return `${minutesAgo}m ago`;
	if (minutesAgo < 1440) {
		const hoursAgo = Math.floor(minutesAgo / 60);
		return `${hoursAgo}h ago`;
	}
	if (minutesAgo < 1440 * 365) {
		const daysAgo = Math.floor(minutesAgo / 1440);
		return `${daysAgo}d ago`;
	}
	return 'Long ago';
}

/**
 * Initialize presence data from stored messages
 */
export async function initializePresenceFromMessages() {
	try {
		const conversations = await backendAPI.getConversations();
		
		for (const conversation of conversations) {
			const messages = await backendAPI.getConversation(conversation.callsign);
			
			if (messages.length > 0) {
				const incomingMessages = messages.filter(msg => msg.type === 'rx');
				
				if (incomingMessages.length > 0) {
					const mostRecentIncoming = incomingMessages.reduce((latest, msg) => {
						const msgTime = new Date(msg.time).getTime();
						const latestTime = new Date(latest.time).getTime();
						return msgTime > latestTime ? msg : latest;
					});
					
					updateStation(conversation.callsign, {
						lastHeard: mostRecentIncoming.time
					});
				}
			}
		}
		
	} catch (error) {
		console.error('Failed to initialize presence from messages:', error);
	}
}