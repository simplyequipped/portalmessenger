/**
 * Settings store for managing app settings
 */
import { writable, derived, get } from 'svelte/store';
import { backendAPI } from '$lib/api/backend.ts';
import { pyjs8callAPI } from '$lib/api/pyjs8call.ts';
import { updateAllConnectionStatus, establishWebSocketConnection } from '$lib/stores/connection.js';
import { loadInitialStations, clearStations } from '$lib/stores/stations.js';

// Store for all settings
export const settings = writable({});

// Loading state for settings operations
export const settingsLoading = writable(false);

// Whether JS8Call restart is required
export const restartRequired = writable(false);

// Settings validation errors
export const settingsErrors = writable({});

// Derived store for settings that need JS8Call restart
export const restartSettings = derived(
	settings,
	($settings) => {
		const restartKeys = [];
		for (const [key, setting] of Object.entries($settings)) {
			if (setting.restart) {
				restartKeys.push(key);
			}
		}
		return restartKeys;
	}
);

/**
 * Load all settings from backend
 */
export async function loadSettings() {
	settingsLoading.set(true);
	try {
		const settingsArray = await backendAPI.getAllSettings();
		
		// Convert array to object keyed by setting name
		const settingsObject = {};
		settingsArray.forEach(setting => {
			settingsObject[setting.setting] = setting;
		});
		
		settings.set(settingsObject);
		
		// Update pyjs8call API base URL if host/port settings exist
		const hostSetting = settingsObject['pyjs8call-api-host'];
		const portSetting = settingsObject['pyjs8call-api-port'];
		
		if (hostSetting && portSetting) {
			const host = hostSetting.value;
			const port = parseInt(portSetting.value);
			// Update pyjs8call API URL
			pyjs8callAPI.updateBaseURL(host, port);
		}
		
		return settingsObject;
	} catch (error) {
		console.error('Failed to load settings:', error);
		throw error;
	} finally {
		settingsLoading.set(false);
	}
}

/**
 * Update a single setting
 */
export async function updateSetting(key, value) {
	settingsLoading.set(true);
	settingsErrors.update(errors => {
		const { [key]: removed, ...rest } = errors;
		return rest;
	});
	
	try {
		// Update in backend
		const updatedSetting = await backendAPI.updateSetting(key, value);
		
		// Update local store
		settings.update(current => ({
			...current,
			[key]: updatedSetting
		}));
		
		// If setting is invalid, store error
		if (!updatedSetting.valid) {
			settingsErrors.update(errors => ({
				...errors,
				[key]: 'Invalid value'
			}));
			return { success: false, setting: updatedSetting };
		}
		
		// Apply to pyjs8call if this is a JS8Call setting and it's valid
		let needsRestart = false;
		
		if (updatedSetting.valid) {
			try {
				await applySettingToPyJS8Call(key, value);
				needsRestart = updatedSetting.restart;
			} catch (pyjs8error) {
				console.error(`Failed to apply ${key} to pyjs8call:`, pyjs8error);
				// Setting was saved to backend but couldn't be applied to JS8Call
				// This is not necessarily a fatal error
			}
		}
		
		// Update restart required state
		if (needsRestart) {
			restartRequired.set(true);
		}
		
		// Update pyjs8call API base URL if host/port changed
		if (key === 'pyjs8call-api-host' || key === 'pyjs8call-api-port') {
			const currentSettings = {};
			settings.subscribe(s => { currentSettings.value = s; })();
			
			const host = key === 'pyjs8call-api-host' ? value : currentSettings.value['pyjs8call-api-host']?.value;
			const port = key === 'pyjs8call-api-port' ? parseInt(value) : parseInt(currentSettings.value['pyjs8call-api-port']?.value);
			
			// Update API URL (disconnects WebSocket)
			pyjs8callAPI.updateBaseURL(host, port);
			
			// Re-establish WebSocket connection with new URL
			await establishWebSocketConnection();
			
			// Update all connection status with new API URL
			await updateAllConnectionStatus();
		}
		
		// Refresh station data if aging setting changed
		if (key === 'aging') {
			const newAgeSeconds = parseInt(value) * 60; // Convert minutes to seconds
			
			// Clear existing stations and reload with new age filter
			clearStations();
			await loadInitialStations(newAgeSeconds);
		}
		
		return { success: true, setting: updatedSetting, needsRestart };
		
	} catch (error) {
		console.error(`Failed to update setting ${key}:`, error);
		settingsErrors.update(errors => ({
			...errors,
			[key]: error.message
		}));
		throw error;
	} finally {
		settingsLoading.set(false);
	}
}

/**
 * Update multiple settings at once
 */
export async function updateMultipleSettings(settingsToUpdate) {
	settingsLoading.set(true);
	settingsErrors.set({});
	
	try {
		// Update all in backend
		const updatedSettings = await backendAPI.updateMultipleSettings(settingsToUpdate);
		
		// Update local store
		settings.update(current => {
			const updated = { ...current };
			updatedSettings.forEach(setting => {
				updated[setting.setting] = setting;
			});
			return updated;
		});
		
		// Check for validation errors
		const errors = {};
		let hasValidSettings = false;
		let needsRestart = false;
		
		updatedSettings.forEach(setting => {
			if (!setting.valid) {
				errors[setting.setting] = 'Invalid value';
			} else {
				hasValidSettings = true;
				if (setting.restart) {
					needsRestart = true;
				}
			}
		});
		
		if (Object.keys(errors).length > 0) {
			settingsErrors.set(errors);
		}
		
		// Apply valid settings to pyjs8call
		if (hasValidSettings) {
			try {
				for (const setting of updatedSettings) {
					if (setting.valid) {
						await applySettingToPyJS8Call(setting.setting, setting.value);
					}
				}
			} catch (pyjs8error) {
				console.error('Failed to apply some settings to pyjs8call:', pyjs8error);
			}
		}
		
		// Update restart required state
		if (needsRestart) {
			restartRequired.set(true);
		}
		
		// Check for settings that require immediate action
		let apiSettingsChanged = false;
		let agingChanged = false;
		let newHost, newPort;
		
		for (const setting of updatedSettings) {
			if (setting.valid && setting.setting === 'pyjs8call-api-host') {
				newHost = setting.value;
				apiSettingsChanged = true;
			}
			if (setting.valid && setting.setting === 'pyjs8call-api-port') {
				newPort = parseInt(setting.value);
				apiSettingsChanged = true;
			}
			if (setting.valid && setting.setting === 'aging') {
				agingChanged = true;
			}
		}
		
		// Update API URL and refresh all connections if host/port changed
		if (apiSettingsChanged) {
			// Get current host/port values
			const currentHost = newHost || get(settings)['pyjs8call-api-host']?.value || 'localhost';
			const currentPort = newPort || parseInt(get(settings)['pyjs8call-api-port']?.value) || 8080;
			
			// Update API URL (disconnects WebSocket)
			pyjs8callAPI.updateBaseURL(currentHost, currentPort);
			
			// Re-establish WebSocket connection with new URL
			await establishWebSocketConnection();
			
			// Update all connection status with new API URL
			await updateAllConnectionStatus();
		}
		
		// Refresh station data if aging changed
		if (agingChanged) {
			const agingSetting = updatedSettings.find(s => s.setting === 'aging');
			if (agingSetting) {
				const newAgeSeconds = parseInt(agingSetting.value) * 60; // Convert minutes to seconds
				
				// Clear existing stations and reload with new age filter
				clearStations();
				await loadInitialStations(newAgeSeconds);
			}
		}
		
		return { 
			success: Object.keys(errors).length === 0,
			settings: updatedSettings, 
			errors,
			needsRestart 
		};
		
	} catch (error) {
		console.error('Failed to update settings:', error);
		settingsErrors.update(errors => ({
			...errors,
			general: error.message
		}));
		throw error;
	} finally {
		settingsLoading.set(false);
	}
}

/**
 * Apply a setting to pyjs8call API
 */
async function applySettingToPyJS8Call(key, value) {
	switch (key) {
		case 'callsign':
			await pyjs8callAPI.setCallsign(value);
			break;
		case 'grid':
			await pyjs8callAPI.setGrid(value);
			break;
		case 'freq':
			await pyjs8callAPI.setFrequency(parseInt(value));
			break;
		case 'speed':
			await pyjs8callAPI.setSpeed(value);
			break;
		case 'groups':
			// Parse comma-separated groups
			const groups = value ? value.split(',').map(g => g.trim()).filter(g => g) : [];
			await pyjs8callAPI.setGroups(groups);
			break;
		// Other settings don't need to be applied to pyjs8call
		default:
			// No action needed
			break;
	}
}

/**
 * Perform JS8Call restart
 */
export async function restartJS8Call() {
	try {
		settingsLoading.set(true);
		
		// Restart pyjs8call using the restart endpoint
		await pyjs8callAPI.restart();
		
		// Wait for restart to complete
		await new Promise(resolve => setTimeout(resolve, 3000));
		
		// Clear restart required flag
		restartRequired.set(false);
		
		return true;
	} catch (error) {
		console.error('Failed to restart JS8Call:', error);
		throw error;
	} finally {
		settingsLoading.set(false);
	}
}

/**
 * Get a specific setting value
 */
export function getSettingValue(key) {
	let value = null;
	settings.subscribe(current => {
		value = current[key]?.value || null;
	})();
	return value;
}

/**
 * Check if a setting is valid
 */
export function isSettingValid(key) {
	let valid = true;
	settingsErrors.subscribe(errors => {
		valid = !errors[key];
	})();
	return valid;
}