<script lang="ts">
	import { systemStatus, backendConnected, pyjs8callConnected, websocketConnected, js8callConnected } from '$lib/stores/connection.js';
	import { totalUnreadCount } from '$lib/stores/stations.js';
	import { page } from '$app/stores';
	
	let showMenu = false;
	let showStatusPopover = false;
	
	function toggleMenu() {
		// Close status popover when opening menu
		if (!showMenu) {
			showStatusPopover = false;
		}
		showMenu = !showMenu;
	}
	
	function toggleStatusPopover(event) {
		event.stopPropagation();
		// Close menu when opening status popover
		if (!showStatusPopover) {
			showMenu = false;
		}
		showStatusPopover = !showStatusPopover;
	}
	
	function closeMenu(event) {
		// Don't close menu if clicking on a link (let SvelteKit handle navigation)
		if (event?.target?.tagName === 'A' || event?.target?.closest('a')) {
			return;
		}
		showMenu = false;
	}
	
	function closeStatusPopover(event) {
		// Don't close if clicking inside the popover
		if (event?.target?.closest('.status-popover')) {
			return;
		}
		showStatusPopover = false;
	}
	
	// Close menu and popover when page changes (navigation completes)
	$: if ($page.url) {
		showMenu = false;
		showStatusPopover = false;
	}
	
	function getStatusColor(status: string) {
		switch (status) {
			case 'connected': return '#10b981'; // green
			case 'warning': return '#f59e0b'; // amber
			case 'error': return '#ef4444'; // red
			default: return '#6b7280'; // gray
		}
	}
</script>

<svelte:window on:click={closeMenu} on:click={closeStatusPopover} />

<header class="header">
	<div class="header-content">
		<h1 class="title">PORTAL MESSENGER</h1>
		
		<div class="header-right">
			<!-- Connection status indicator -->
			<div class="status-indicator" title={$systemStatus.message}>
				<button 
					class="status-button"
					on:click={toggleStatusPopover}
					aria-label="Show connection status details"
				>
					<div 
						class="status-dot"
						style="background-color: {getStatusColor($systemStatus.status)}"
					></div>
					<span class="status-text">{$systemStatus.message}</span>
				</button>
				
				{#if showStatusPopover}
					<div class="status-popover">
						<div class="status-header">Connection Status</div>
						<div class="status-items">
							<div class="status-item">
								<div class="status-item-dot" class:connected={$backendConnected} class:disconnected={!$backendConnected}></div>
								<span>Backend API</span>
								<span class="status-value">{$backendConnected ? 'Connected' : 'Disconnected'}</span>
							</div>
							<div class="status-item">
								<div class="status-item-dot" class:connected={$pyjs8callConnected} class:disconnected={!$pyjs8callConnected}></div>
								<span>pyjs8call API</span>
								<span class="status-value">{$pyjs8callConnected ? 'Connected' : 'Disconnected'}</span>
							</div>
							<div class="status-item">
								<div class="status-item-dot" class:connected={$websocketConnected} class:disconnected={!$websocketConnected}></div>
								<span>WebSocket</span>
								<span class="status-value">{$websocketConnected ? 'Connected' : 'Disconnected'}</span>
							</div>
							<div class="status-item">
								<div class="status-item-dot" class:connected={$js8callConnected} class:disconnected={!$js8callConnected}></div>
								<span>JS8Call</span>
								<span class="status-value">{$js8callConnected ? 'Connected' : 'Disconnected'}</span>
							</div>
						</div>
					</div>
				{/if}
			</div>
			
			<!-- Unread count badge -->
			{#if $totalUnreadCount > 0}
				<div class="unread-badge">
					{$totalUnreadCount}
				</div>
			{/if}
			
			<!-- Menu button -->
			<button 
				class="menu-button"
				on:click|stopPropagation={toggleMenu}
				aria-label="Open menu"
			>
				<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
					<path d="M3 12h18M3 6h18M3 18h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
				</svg>
			</button>
		</div>
	</div>
	
	<!-- Dropdown menu -->
	{#if showMenu}
		<div class="menu-dropdown">
			<a href="/" class="menu-item">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
					<path d="M20 6L9 17l-5-5"/>
				</svg>
				Messages
			</a>
			<a href="/activity" class="menu-item">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
					<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
				</svg>
				Activity
			</a>
			<a href="/settings" class="menu-item">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
					<path d="M12 15a3 3 0 100-6 3 3 0 000 6z"/>
					<path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
				</svg>
				Settings
			</a>
		</div>
	{/if}
</header>

<style>
	.header {
		background: var(--primary-bg, #1f2937);
		color: var(--primary-text, white);
		border-bottom: 1px solid var(--border-color, #374151);
		position: relative;
		z-index: 1000;
	}
	
	.header-content {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 1.5rem;
		max-width: 100%;
	}
	
	.title {
		font-size: 1.25rem;
		font-weight: bold;
		margin: 0;
		letter-spacing: 0.05em;
	}
	
	.header-right {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.status-indicator {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
	}
	
	.status-dot {
		width: 16px;
		height: 16px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.status-text {
		color: var(--primary-text);
		opacity: 0.9;
	}
	
	.unread-badge {
		background: var(--accent-bg, #ef4444);
		color: white;
		border-radius: 50%;
		min-width: 1.5rem;
		height: 1.5rem;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.75rem;
		font-weight: bold;
	}
	
	.menu-button {
		background: transparent;
		border: none;
		color: currentColor;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 0.375rem;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: background-color 0.2s;
	}
	
	.menu-button:hover {
		background: var(--hover-bg, rgba(255, 255, 255, 0.1));
	}
	
	.menu-dropdown {
		position: fixed;
		top: 60px; /* Position below header */
		right: 1.5rem;
		background: var(--dropdown-bg, white);
		border: 1px solid var(--border-color, #e5e7eb);
		border-radius: 0.5rem;
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
		min-width: 12rem;
		overflow: hidden;
		z-index: 200; /* Above drawer (100) */
	}
	
	.menu-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		color: var(--dropdown-text, #374151);
		text-decoration: none;
		transition: background-color 0.2s;
	}
	
	.menu-item:hover {
		background: var(--hover-bg, #f3f4f6);
	}
	
	.menu-item svg {
		flex-shrink: 0;
		opacity: 0.6;
	}
	
	@media (max-width: 768px) {
		.status-text {
			display: none;
		}
		
		.header-content {
			padding: 0.75rem 1rem;
		}
		
		.title {
			font-size: 1.125rem;
		}
	}
	
	/* Status button and popover styles */
	.status-button {
		background: transparent;
		border: none;
		color: currentColor;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		padding: 0.25rem;
		border-radius: 0.375rem;
		transition: background-color 0.2s;
	}
	
	.status-button:hover {
		background: var(--hover-bg, rgba(255, 255, 255, 0.1));
	}
	
	.status-indicator {
		position: relative;
	}
	
	.status-popover {
		position: fixed;
		top: 60px; /* Position below header */
		right: 6rem; /* Further left than menu dropdown */
		background: var(--dropdown-bg, white);
		border: 1px solid var(--border-color, #e5e7eb);
		border-radius: 0.5rem;
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
		min-width: 275px;
		overflow: hidden;
		z-index: 200; /* Above drawer (100) */
	}

	@media (max-width: 768px) {
		.status-popover {
			left: 1rem; /* Far left on mobile */
			right: auto; /* Override right positioning */
			width: calc(100vw - 3rem); /* Fill most of screen width */
			max-width: 300px; /* But don't get too wide */
			min-width: auto; /* Override the 275px min-width */
		}
	}
	
	.status-header {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--border-color, #e5e7eb);
		font-weight: 600;
		font-size: 0.875rem;
		color: var(--dropdown-text, #374151);
		background: var(--dropdown-bg, white);
	}
	
	.status-items {
		background: var(--dropdown-bg, white);
	}
	
	.status-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		font-size: 0.875rem;
		color: var(--dropdown-text, #374151);
		transition: background-color 0.2s;
	}
	
	.status-item:hover {
		background: var(--hover-bg, #f3f4f6);
	}
	
	.status-item-dot {
		width: 16px;
		height: 16px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.status-item-dot.connected {
		background-color: #10b981;
	}
	
	.status-item-dot.disconnected {
		background-color: #ef4444;
	}
	
	.status-value {
		margin-left: auto;
		color: var(--text-muted, #6b7280);
		font-size: 0.8125rem;
		opacity: 0.8;
	}
	
	/* Mobile adjustments for popover */
	@media (max-width: 640px) {
		.status-popover {
			right: -1rem;
			min-width: 275px;
		}
		
		.status-text {
			display: none;
		}
	}
</style>