/**
 * pyjs8call API Client
 * Handles WebSocket connections and REST API calls for JS8Call integration
 */

export interface PyJS8CallMessage {
	id: string;
	origin: string;
	destination: string;
	type: string;
	timestamp: number;
	text: string;
	status?: string;
	error?: string;
}

export interface ConnectionStatus {
	connected: boolean;
}

export interface JS8CallSetting {
	value: string | number | boolean;
}

class PyJS8CallAPI {
	private baseURL: string;
	private websocket: WebSocket | null = null;
	private reconnectAttempts = 0;
	private maxReconnectAttempts = 5;
	private reconnectDelay = 1000; // Start with 1 second
	private eventHandlers: Map<string, ((data: any) => void)[]> = new Map();

	constructor() {
		// Will be set from user settings
		this.baseURL = '';
	}

	/**
	 * Update base URL (from settings)
	 */
	updateBaseURL(host: string, port: number) {
		const newURL = `http://${host}:${port}`;
		// Update base URL
		this.baseURL = newURL;
		// Disconnect existing WebSocket - reconnection handled by caller
		if (this.websocket) {
			this.disconnectWebSocket();
		}
	}
	
	/**
	 * Get current base URL for debugging
	 */
	getCurrentBaseURL(): string {
		return this.baseURL;
	}

	/**
	 * Connect to WebSocket for real-time events
	 */
	connectWebSocket(): Promise<void> {
		return new Promise((resolve, reject) => {
			const wsURL = this.baseURL.replace('http://', 'ws://') + '/api/events';
			
			try {
				this.websocket = new WebSocket(wsURL);
				
				this.websocket.onopen = () => {
					console.log('WebSocket connection opened to', wsURL);
					
					// Subscribe to all message events
					const subscribeMessage = {
						action: 'subscribe',
						events: [
							'incoming_message',
							'outgoing_status',
							'new_spots',
							'inbox_message',
							'window_transition'
						]
					};
					
					if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
						this.websocket.send(JSON.stringify(subscribeMessage));
					}
					
					this.reconnectAttempts = 0;
					this.reconnectDelay = 1000;
					resolve();
				};

				this.websocket.onmessage = (event) => {
					try {
						const data = JSON.parse(event.data);
						if (data.event === 'subscribed') {
							console.log('Successfully subscribed to events:', data.events.join(', '));
						} else {
							this.handleWebSocketMessage(data);
						}
					} catch (error) {
						console.error('Failed to parse WebSocket message:', error);
					}
				};

				this.websocket.onclose = (event) => {
					this.websocket = null;
					this.scheduleReconnect();
				};

				this.websocket.onerror = (error) => {
					console.error('pyjs8call WebSocket error:', error);
					reject(error);
				};
			} catch (error) {
				reject(error);
			}
		});
	}

	/**
	 * Disconnect WebSocket
	 */
	disconnectWebSocket() {
		if (this.websocket && this.websocket.readyState !== WebSocket.CLOSED) {
			try {
				this.websocket.close();
			} catch (error) {
				console.warn('Error closing WebSocket:', error);
			}
		}
		this.websocket = null;
	}

	/**
	 * Schedule WebSocket reconnection with exponential backoff
	 */
	private scheduleReconnect() {
		if (this.reconnectAttempts < this.maxReconnectAttempts) {
			setTimeout(() => {
				this.reconnectAttempts++;
				this.reconnectDelay *= 2; // exponential backoff
				// attempting to reconnect to pyjs8call websocket
				this.connectWebSocket().catch(() => {
					// reconnection failed, will try again
				});
			}, this.reconnectDelay);
		}
	}

	/**
	 * Handle incoming WebSocket messages
	 */
	private handleWebSocketMessage(data: any) {
		const { event, ...payload } = data;
		const handlers = this.eventHandlers.get(event);
		if (handlers) {
			handlers.forEach(handler => handler(payload));
		}
	}

	/**
	 * Subscribe to WebSocket events
	 */
	on(eventType: string, handler: (data: any) => void) {
		if (!this.eventHandlers.has(eventType)) {
			this.eventHandlers.set(eventType, []);
		}
		this.eventHandlers.get(eventType)!.push(handler);
	}

	/**
	 * Unsubscribe from WebSocket events
	 */
	off(eventType: string, handler: (data: any) => void) {
		const handlers = this.eventHandlers.get(eventType);
		if (handlers) {
			const index = handlers.indexOf(handler);
			if (index !== -1) {
				handlers.splice(index, 1);
			}
		}
	}

	/**
	 * Check JS8Call connection status
	 */
	async getConnectionStatus(): Promise<ConnectionStatus> {
		const response = await fetch(`${this.baseURL}/api/js8call/connected`);
		if (!response.ok) {
			throw new Error(`Failed to get connection status: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Send directed message
	 */
	async sendDirectedMessage(destination: string, text: string): Promise<PyJS8CallMessage> {
		const response = await fetch(`${this.baseURL}/api/message/directed`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ destination, message: text })
		});
		if (!response.ok) {
			throw new Error(`Failed to send directed message: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Send freetext message
	 */
	async sendFreetextMessage(text: string): Promise<PyJS8CallMessage> {
		const response = await fetch(`${this.baseURL}/api/message/freetext`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ message: text })
		});
		if (!response.ok) {
			throw new Error(`Failed to send freetext message: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Send heartbeat
	 */
	async sendHeartbeat(): Promise<PyJS8CallMessage> {
		const response = await fetch(`${this.baseURL}/api/message/heartbeat`, {
			method: 'POST'
		});
		if (!response.ok) {
			throw new Error(`Failed to send heartbeat: ${response.status}`);
		}
		return await response.json();
	}

	// Settings API methods

	/**
	 * Get callsign
	 */
	async getCallsign(): Promise<JS8CallSetting> {
		const response = await fetch(`${this.baseURL}/api/settings/callsign`);
		if (!response.ok) {
			throw new Error(`Failed to get callsign: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Set callsign
	 */
	async setCallsign(callsign: string): Promise<JS8CallSetting> {
		const response = await fetch(`${this.baseURL}/api/settings/callsign`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ callsign: callsign })
		});
		if (!response.ok) {
			throw new Error(`Failed to set callsign: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Get grid square
	 */
	async getGrid(): Promise<JS8CallSetting> {
		const response = await fetch(`${this.baseURL}/api/settings/grid`);
		if (!response.ok) {
			throw new Error(`Failed to get grid: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Set grid square
	 */
	async setGrid(grid: string): Promise<JS8CallSetting> {
		const response = await fetch(`${this.baseURL}/api/settings/grid`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ grid: grid })
		});
		if (!response.ok) {
			throw new Error(`Failed to set grid: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Get frequency
	 */
	async getFrequency(): Promise<JS8CallSetting> {
		const response = await fetch(`${this.baseURL}/api/settings/frequency`);
		if (!response.ok) {
			throw new Error(`Failed to get frequency: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Set frequency
	 */
	async setFrequency(frequency: number): Promise<JS8CallSetting> {
		const response = await fetch(`${this.baseURL}/api/settings/frequency`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ frequency: frequency })
		});
		if (!response.ok) {
			throw new Error(`Failed to set frequency: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Get speed setting
	 */
	async getSpeed(): Promise<JS8CallSetting> {
		const response = await fetch(`${this.baseURL}/api/settings/speed`);
		if (!response.ok) {
			throw new Error(`Failed to get speed: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Set speed
	 */
	async setSpeed(speed: string): Promise<JS8CallSetting> {
		const response = await fetch(`${this.baseURL}/api/settings/speed`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ speed: speed })
		});
		if (!response.ok) {
			throw new Error(`Failed to set speed: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Get groups
	 */
	async getGroups(): Promise<JS8CallSetting> {
		const response = await fetch(`${this.baseURL}/api/settings/groups`);
		if (!response.ok) {
			throw new Error(`Failed to get groups: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Set groups
	 */
	async setGroups(groups: string[]): Promise<JS8CallSetting> {
		const response = await fetch(`${this.baseURL}/api/settings/groups`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ groups: groups })
		});
		if (!response.ok) {
			throw new Error(`Failed to set groups: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Start pyjs8call
	 */
	async start(headless: boolean = false, debugging: boolean = false, logging: boolean = false, args: string[] = []): Promise<{ status: string }> {
		const response = await fetch(`${this.baseURL}/api/js8call/start`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ headless, debugging, logging, args })
		});
		if (!response.ok) {
			throw new Error(`Failed to start pyjs8call: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Stop pyjs8call
	 */
	async stop(terminate_js8call: boolean = true): Promise<{ status: string }> {
		const response = await fetch(`${this.baseURL}/api/js8call/stop`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ terminate_js8call })
		});
		if (!response.ok) {
			throw new Error(`Failed to stop pyjs8call: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Restart pyjs8call
	 */
	async restart(): Promise<{ status: string }> {
		const response = await fetch(`${this.baseURL}/api/js8call/restart`, {
			method: 'POST'
		});
		if (!response.ok) {
			throw new Error(`Failed to restart pyjs8call: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Get pyjs8call status
	 */
	async getStatus(): Promise<{ status: string }> {
		const response = await fetch(`${this.baseURL}/api/js8call`);
		if (!response.ok) {
			throw new Error(`Failed to get pyjs8call status: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Get stations that this callsign can hear
	 */
	async getStationHearing(callsign: string, ageMinutes?: number): Promise<string[]> {
		// Double-encode callsign for FastAPI - ASGI server decodes once, handler decodes again
		const encodedCallsign = encodeURIComponent(encodeURIComponent(callsign));
		let url = `${this.baseURL}/api/activity/${encodedCallsign}/hearing`;
		if (ageMinutes !== undefined) {
			url += `?age=${ageMinutes}`;
		}
		const response = await fetch(url);
		if (!response.ok) {
			throw new Error(`Failed to get station hearing: ${response.status}`);
		}
		const data = await response.json();
		return data.hearing || [];
	}

	/**
	 * Get stations that can hear this callsign
	 */
	async getStationHeard(callsign: string, ageMinutes?: number): Promise<string[]> {
		// Double-encode callsign for FastAPI - ASGI server decodes once, handler decodes again
		const encodedCallsign = encodeURIComponent(encodeURIComponent(callsign));
		let url = `${this.baseURL}/api/activity/${encodedCallsign}/heard-by`;
		if (ageMinutes !== undefined) {
			url += `?age=${ageMinutes}`;
		}
		const response = await fetch(url);
		if (!response.ok) {
			throw new Error(`Failed to get station heard: ${response.status}`);
		}
		const data = await response.json();
		return data.heard_by || [];
	}

	/**
	 * Get spots filtered by age in seconds
	 */
	async getSpots(ageSeconds: number): Promise<any[]> {
		const response = await fetch(`${this.baseURL}/api/spots/filter?age=${ageSeconds}`);
		if (!response.ok) {
			throw new Error(`Failed to get spots: ${response.status}`);
		}
		const data = await response.json();
		return data.spots || [];
	}

	/**
	 * Calculate grid distance from local station
	 */
	async getGridDistance(grid: string): Promise<{
		success: boolean;
		station_grid?: string;
		grid?: string;
		distance?: number;
		units?: string;
		bearing?: number;
		error?: string;
	}> {
		const response = await fetch(`${this.baseURL}/api/utils/grid-distance/${encodeURIComponent(grid)}`);
		if (!response.ok) {
			throw new Error(`Failed to get grid distance: ${response.status}`);
		}
		return await response.json();
	}

	/**
	 * Get WebSocket for external access (used in connection monitoring)
	 */
	getWebSocket(): WebSocket | null {
		return this.websocket;
	}
}

// Export singleton instance
export const pyjs8callAPI = new PyJS8CallAPI();