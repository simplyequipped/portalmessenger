/**
 * Connection status store for tracking backend and pyjs8call connectivity
 */
import { writable, derived } from 'svelte/store';
import { backendAPI } from '$lib/api/backend.ts';
import { pyjs8callAPI } from '$lib/api/pyjs8call.ts';

// Connection status for pyjs8call
export const pyjs8callConnected = writable(false);

// Connection status for backend
export const backendConnected = writable(true); // Assume connected initially

// WebSocket connection status
export const websocketConnected = writable(false);

// JS8Call application status
export const js8callConnected = writable(false);

// Overall system status
export const systemStatus = derived(
	[backendConnected, pyjs8callConnected, websocketConnected, js8callConnected],
	([$backendConnected, $pyjs8callConnected, $websocketConnected, $js8callConnected]) => {
		if (!$backendConnected) {
			return { status: 'error', message: 'Backend disconnected' };
		}
		if (!$pyjs8callConnected) {
			return { status: 'warning', message: 'pyjs8call API disconnected' };
		}
		if (!$websocketConnected) {
			return { status: 'warning', message: 'Real-time updates disconnected' };
		}
		if (!$js8callConnected) {
			return { status: 'warning', message: 'JS8Call not connected' };
		}
		return { status: 'connected', message: 'All systems connected' };
	}
);

/**
 * Check backend connectivity
 */
export async function checkBackendConnection() {
	try {
		await backendAPI.getStatus();
		backendConnected.set(true);
		return true;
	} catch (error) {
		console.error('Backend connection failed:', error);
		backendConnected.set(false);
		return false;
	}
}

/**
 * Check pyjs8call API connectivity
 */
export async function checkPyJS8CallConnection() {
	try {
		const status = await pyjs8callAPI.getStatus();
		pyjs8callConnected.set(true);
		return true;
	} catch (error) {
		console.error('pyjs8call API connection failed:', error);
		console.error('Error details:', {
			message: error.message,
			stack: error.stack,
			baseURL: pyjs8callAPI.getCurrentBaseURL()
		});
		pyjs8callConnected.set(false);
		return false;
	}
}

/**
 * Check JS8Call application connectivity
 */
export async function checkJS8CallConnection() {
	try {
		const status = await pyjs8callAPI.getConnectionStatus();
		js8callConnected.set(status.connected);
		return status.connected;
	} catch (error) {
		console.error('JS8Call connection check failed:', error);
		js8callConnected.set(false);
		return false;
	}
}

/**
 * Initialize WebSocket connection
 */
export async function initializeWebSocket() {
	try {
		await pyjs8callAPI.connectWebSocket();
		websocketConnected.set(true);
		
		// Set up WebSocket event handlers
		pyjs8callAPI.on('connect', () => {
			websocketConnected.set(true);
		});
		
		pyjs8callAPI.on('disconnect', () => {
			websocketConnected.set(false);
		});
		
		return true;
	} catch (error) {
		console.error('WebSocket connection failed:', error);
		websocketConnected.set(false);
		return false;
	}
}

/**
 * Start connection monitoring
 * Periodically check all connections and update status
 */
export function startConnectionMonitoring(intervalMs = 30000) {
	// Initial status check using unified function
	updateAllConnectionStatus();
	
	// Periodic status checks using unified function
	const interval = setInterval(async () => {
		await updateAllConnectionStatus();
	}, intervalMs);
	
	// Return cleanup function
	return () => {
		clearInterval(interval);
		pyjs8callAPI.disconnectWebSocket();
	};
}

/**
 * UNIFIED CONNECTION STATUS UPDATE - THE SINGLE SOURCE OF TRUTH
 * This is the ONLY function that should be called to update connection status
 */
export async function updateAllConnectionStatus() {
	try {
		// Check all connections in parallel
		const results = await Promise.allSettled([
			checkBackendConnection(),
			checkPyJS8CallConnection(), 
			checkJS8CallConnection(),
			checkWebSocketConnection()
		]);
		
		// Log any failures for debugging
		results.forEach((result, index) => {
			const names = ['Backend', 'pyjs8call API', 'JS8Call', 'WebSocket'];
			if (result.status === 'rejected') {
				console.error(`${names[index]} connection check failed:`, result.reason);
			}
		});
		
	} catch (error) {
		console.error('Failed to update connection status:', error);
	}
}

/**
 * Shared WebSocket connection establishment for init/reinit
 * Used by both initial page load and settings changes
 */
export async function establishWebSocketConnection() {
	try {
		// Check if pyjs8call API base URL is configured
		const baseURL = pyjs8callAPI.getCurrentBaseURL();
		if (!baseURL) {
			websocketConnected.set(false);
			return false;
		}

		// Connect to WebSocket
		await pyjs8callAPI.connectWebSocket();
		websocketConnected.set(true);
		return true;
		
	} catch (error) {
		console.error('Failed to establish WebSocket connection:', error);
		websocketConnected.set(false);
		return false;
	}
}

/**
 * Check WebSocket connection status (unified)
 * Only reports status, does not attempt connections
 */
async function checkWebSocketConnection() {
	try {
		// Check if websocket exists and is open
		const websocket = pyjs8callAPI.getWebSocket();
		const isConnected = websocket && websocket.readyState === WebSocket.OPEN;
		
		websocketConnected.set(isConnected);
		return isConnected;
	} catch (error) {
		console.error('WebSocket connection check failed:', error);
		websocketConnected.set(false);
		return false;
	}
}

/**
 * Get current connection summary
 */
export function getConnectionSummary() {
	let summary = {};
	
	backendConnected.subscribe(connected => summary.backend = connected)();
	pyjs8callConnected.subscribe(connected => summary.pyjs8call = connected)();
	websocketConnected.subscribe(connected => summary.websocket = connected)();
	js8callConnected.subscribe(connected => summary.js8call = connected)();
	
	return summary;
}