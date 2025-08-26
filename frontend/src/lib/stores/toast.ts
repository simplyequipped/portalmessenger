/**
 * Simple toast notification system for Svelte 5
 */
import { writable } from 'svelte/store';

export interface Toast {
	id: string;
	message: string;
	type: 'success' | 'error' | 'info' | 'warning';
	duration?: number;
}

// Store for active toasts
export const toasts = writable<Toast[]>([]);

let toastId = 0;

/**
 * Add a new toast notification
 */
export function addToast(message: string, type: Toast['type'] = 'info', duration = 5000) {
	const id = `toast-${++toastId}`;
	const toast: Toast = { id, message, type, duration };
	
	// Add to store
	toasts.update(current => [...current, toast]);
	
	// Auto-remove after duration
	if (duration > 0) {
		setTimeout(() => {
			removeToast(id);
		}, duration);
	}
	
	return id;
}

/**
 * Remove a specific toast
 */
export function removeToast(id: string) {
	toasts.update(current => current.filter(toast => toast.id !== id));
}

/**
 * Clear all toasts
 */
export function clearToasts() {
	toasts.set([]);
}

// Convenience functions
export const toast = {
	success: (message: string, duration?: number) => addToast(message, 'success', duration),
	error: (message: string, duration?: number) => addToast(message, 'error', duration),
	info: (message: string, duration?: number) => addToast(message, 'info', duration),
	warning: (message: string, duration?: number) => addToast(message, 'warning', duration),
};