/**
 * Store for managing mobile drawer state
 */
import { writable } from 'svelte/store';

// Drawer open state - starts open by default on mobile
export const drawerOpen = writable(true);

/**
 * Toggle drawer open/closed
 */
export function toggleDrawer() {
	drawerOpen.update(isOpen => !isOpen);
}

/**
 * Open the drawer
 */
export function openDrawer() {
	drawerOpen.set(true);
}

/**
 * Close the drawer
 */
export function closeDrawer() {
	drawerOpen.set(false);
}