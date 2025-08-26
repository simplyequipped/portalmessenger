<script lang="ts">
	import { onMount } from 'svelte';
	import { stationsSorted, selectedStation, selectStation, loadStationDetails } from '$lib/stores/stations.js';
	import { closeDrawer } from '$lib/stores/drawer.js';
	import { settings, updateSetting } from '$lib/stores/settings.js';
	
	let showDeleteMode = false;
	let showSearch = false;
	let searchQuery = '';
	let showSortMenu = false;
	
	// Get current sort option and available options from settings
	$: currentSort = $settings['activity-sort']?.value || 'recent';
	$: sortOptions = $settings['activity-sort']?.options || ['recent'];
	
	function toggleSortMenu() {
		showSortMenu = !showSortMenu;
		// Close other menus when opening sort menu
		if (showSortMenu) {
			showSearch = false;
			showDeleteMode = false;
		}
	}
	
	async function handleSortChange(newSort) {
		showSortMenu = false;
		try {
			await updateSetting('activity-sort', newSort);
		} catch (error) {
			console.error('Failed to update sort setting:', error);
		}
	}
	
	// Helper functions for time formatting
	function formatLastHeard(timestamp) {
		if (!timestamp) return 'Never';
		
		const now = Date.now();
		const heard = new Date(timestamp).getTime();
		const minutesAgo = Math.floor((now - heard) / (1000 * 60));
		
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
	
	function getPresenceStatus(timestamp) {
		if (!timestamp) return 'unknown';
		
		const minutesAgo = Math.floor((Date.now() - new Date(timestamp).getTime()) / (1000 * 60));
		
		if (minutesAgo < 10) return 'active';    // Green - heard within 10 minutes
		if (minutesAgo < 60) return 'inactive';  // Yellow - heard within 1 hour
		return 'unknown';                        // Gray - heard over 1 hour ago
	}
	
	function handleSelectStation(callsign: string) {
		selectStation(callsign);
		// Close drawer immediately for better mobile UX
		closeDrawer();
		
		// Load station details in the background (don't await)
		loadStationDetails(callsign).catch(error => {
			console.error('Failed to load station details:', error);
		});
	}
	
	function toggleDeleteMode() {
		showDeleteMode = !showDeleteMode;
		// Close sort menu when opening delete mode
		if (showDeleteMode) {
			showSortMenu = false;
		}
	}
	
	function toggleSearch() {
		showSearch = !showSearch;
		if (!showSearch) {
			searchQuery = '';
		}
		// Close sort menu when opening search
		if (showSearch) {
			showSortMenu = false;
		}
	}
	
	function closeSortMenu(event) {
		// Don't close if clicking inside the sort menu
		if (event?.target?.closest('.sort-menu')) {
			return;
		}
		showSortMenu = false;
	}
	
	// Filter stations based on search query
	$: filteredStations = $stationsSorted.filter(station => {
		if (!searchQuery.trim()) return true;
		
		const query = searchQuery.toLowerCase();
		
		// Search in callsign
		if (station.callsign.toLowerCase().includes(query)) return true;
		
		// Search in grid square
		if (station.grid && station.grid.toLowerCase().includes(query)) return true;
		
		// Search in hearing list
		if (station.hearing && station.hearing.some(call => call.toLowerCase().includes(query))) return true;
		
		// Search in heard by list
		if (station.heardBy && station.heardBy.some(call => call.toLowerCase().includes(query))) return true;
		
		// Search in speed
		if (station.speed && station.speed.toString().toLowerCase().includes(query)) return true;
		
		// Search in SNR
		if (station.snr !== undefined && station.snr.toString().includes(query)) return true;
		
		return false;
	});
	
	// TODO: Implement station removal if needed
	async function handleDeleteStation(event: Event, callsign: string) {
		event.stopPropagation();
		if (confirm(`Remove station ${callsign} from activity list?`)) {
			// Implementation depends on whether we want to remove stations
			console.log('Delete station:', callsign);
		}
	}
	
	onMount(async () => {
		// Station data will be populated via WebSocket events
		// No initial loading needed unlike conversations
	});
</script>

<svelte:window on:click={closeSortMenu} />

<div class="station-list">
	<div class="list-header">
		<h2>Activity</h2>
		<div class="header-actions">
			<button 
				class="search-btn"
				class:active={showSearch}
				on:click={toggleSearch}
				title="Search stations"
				disabled={$stationsSorted.length === 0}
			>
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="11" cy="11" r="8"/>
					<path d="m21 21-4.35-4.35"/>
				</svg>
			</button>
			<div class="sort-button-container">
				<button 
					class="sort-btn"
					class:active={showSortMenu}
					on:click|stopPropagation={toggleSortMenu}
					title="Sort stations"
					disabled={$stationsSorted.length === 0}
				>
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M8 9l4-4 4 4"/>
						<path d="M16 15l-4 4-4-4"/>
					</svg>
				</button>
				
				{#if showSortMenu}
					<div class="sort-menu">
						{#each sortOptions as option}
							<button 
								class="sort-option"
								class:active={option === currentSort}
								on:click={() => handleSortChange(option)}
							>
								{option.charAt(0).toUpperCase() + option.slice(1)}
							</button>
						{/each}
					</div>
				{/if}
			</div>
			{#if $stationsSorted.length > 0}
				<button 
					class="delete-toggle-btn"
					class:active={showDeleteMode}
					on:click={toggleDeleteMode}
					title="Manage stations"
				>
					<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
						<path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
					</svg>
				</button>
			{/if}
		</div>
	</div>
	
	<!-- Search field - appears when showSearch is true -->
	{#if showSearch}
		<div class="search-container">
			<input 
				type="text" 
				class="search-input"
				placeholder="Search callsigns, grids, hearing data..."
				bind:value={searchQuery}
				autofocus
			/>
			{#if searchQuery}
				<button 
					class="search-clear-btn"
					on:click={() => searchQuery = ''}
					title="Clear search"
				>
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="m18 6-12 12"/>
						<path d="m6 6 12 12"/>
					</svg>
				</button>
			{/if}
		</div>
	{/if}
	
	
	<div class="stations">
		{#if $stationsSorted.length === 0}
			<div class="empty-state">
				<p>No station activity yet</p>
				<p class="empty-subtitle">Stations will appear as they are heard</p>
			</div>
		{:else if filteredStations.length === 0 && searchQuery}
			<div class="empty-state">
				<p>No stations match your search</p>
				<p class="empty-subtitle">Try a different search term</p>
			</div>
		{:else}
			{#each filteredStations as station (station.callsign)}
				{@const presenceStatus = getPresenceStatus(station.lastHeard)}
				{@const lastHeardText = formatLastHeard(station.lastHeard)}
				
				<div 
					class="station-item"
					class:selected={$selectedStation === station.callsign}
					role="button"
					tabindex="0"
					on:click={() => handleSelectStation(station.callsign)}
					on:keydown={(e) => e.key === 'Enter' && handleSelectStation(station.callsign)}
				>
					<div class="station-content">
						<div class="presence-indicator presence-{presenceStatus}"></div>
						<div class="station-details">
							<div class="callsign-row">
								<span class="callsign">{station.callsign}</span>
								{#if station.grid}
									<span class="grid">{station.grid}</span>
								{/if}
							</div>
							<div class="last-heard">Last heard: {lastHeardText}</div>
							{#if station.snr !== undefined}
								<div class="signal-info">SNR: {station.snr}dB</div>
							{/if}
						</div>
					</div>
					
					{#if showDeleteMode}
						<button 
							class="delete-btn"
							on:click={(e) => handleDeleteStation(e, station.callsign)}
							title="Remove station"
						>
							<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
								<path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
							</svg>
						</button>
					{/if}
				</div>
			{/each}
		{/if}
	</div>
</div>

<style>
	.station-list {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: var(--sidebar-bg, #f9fafb);
	}
	
	.list-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 1.5rem;
		border-bottom: 1px solid var(--border-color, #e5e7eb);
		background: var(--header-bg);
		position: relative;
	}
	
	.list-header h2 {
		margin: 0;
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--text-primary);
		line-height: 1.5;
	}
	
	.header-actions {
		display: flex;
		gap: 0.5rem;
	}
	
	.sort-button-container {
		position: relative;
		display: inline-block;
	}
	
	.search-btn,
	.sort-btn,
	.delete-toggle-btn {
		background: transparent;
		border: 1px solid var(--border-color, #d1d5db);
		border-radius: 0.375rem;
		padding: 0.5rem;
		cursor: pointer;
		color: var(--text-secondary, #6b7280);
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.search-btn:hover:not(:disabled),
	.search-btn.active,
	.sort-btn:hover:not(:disabled),
	.sort-btn.active,
	.delete-toggle-btn:hover,
	.delete-toggle-btn.active {
		background: var(--hover-bg, #f3f4f6);
		color: var(--text-primary, #374151);
	}
	
	.search-btn:disabled,
	.sort-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.search-container {
		position: relative;
		padding: 0.75rem 1.5rem;
		border-bottom: 1px solid var(--border-color, #e5e7eb);
		background: var(--header-bg, white);
	}
	
	.search-input {
		width: 100%;
		padding: 0.5rem 0.75rem;
		padding-right: 2.5rem; /* Space for clear button */
		border: 1px solid var(--border-color, #d1d5db);
		border-radius: 0.375rem;
		font-size: 0.875rem;
		background: var(--input-bg, #f9fafb);
		color: var(--text-primary, #111827);
		transition: border-color 0.2s, box-shadow 0.2s;
	}
	
	.search-input:focus {
		outline: none;
		border-color: var(--primary-color, #3b82f6);
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
		background: white;
	}
	
	.search-input::placeholder {
		color: var(--text-muted, #9ca3af);
	}
	
	.search-clear-btn {
		position: absolute;
		right: 1.5rem;
		top: 50%;
		transform: translateY(-50%);
		background: transparent;
		border: none;
		color: var(--text-muted, #6b7280);
		cursor: pointer;
		padding: 0.25rem;
		border-radius: 0.25rem;
		transition: color 0.2s, background-color 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.search-clear-btn:hover {
		color: var(--text-primary, #374151);
		background: var(--hover-bg, #f3f4f6);
	}
	
	.sort-menu {
		position: absolute;
		top: 100%; /* Position below the sort button */
		right: 0; /* Align with right edge of button */
		background: var(--dropdown-bg, white);
		border: 1px solid var(--border-color, #e5e7eb);
		border-radius: 0.5rem;
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
		min-width: 180px;
		overflow: hidden;
		z-index: 200; /* Above drawer (100) */
		margin-top: 0.25rem; /* Small gap below button */
	}
	
	.sort-option {
		display: block;
		width: 100%;
		padding: 0.75rem 1rem;
		text-align: left;
		background: transparent;
		border: none;
		color: var(--dropdown-text, #374151);
		cursor: pointer;
		transition: background-color 0.2s;
		font-size: 0.875rem;
	}
	
	.sort-option:hover {
		background: var(--hover-bg, #f3f4f6);
	}
	
	.sort-option.active {
		background: var(--selected-bg, rgba(59, 130, 246, 0.1));
		color: var(--primary-color, #3b82f6);
		font-weight: 500;
	}
	
	.stations {
		flex: 1;
		overflow-y: auto;
		padding: 0.5rem 0;
	}
	
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 200px;
		color: var(--text-muted, #6b7280);
		text-align: center;
		padding: 2rem;
	}
	
	.empty-state p {
		margin: 0;
	}
	
	.empty-subtitle {
		font-size: 0.875rem;
		margin-top: 0.5rem;
	}
	
	.station-item {
		display: flex;
		align-items: center;
		padding: 0.75rem 1rem;
		cursor: pointer;
		transition: background-color 0.2s;
		border-bottom: 1px solid var(--border-light, #f3f4f6);
	}
	
	.station-item:hover {
		background: var(--hover-bg, rgba(59, 130, 246, 0.05));
	}
	
	.station-item.selected {
		background: var(--selected-bg, rgba(59, 130, 246, 0.1));
		border-right: 3px solid var(--primary-color, #3b82f6);
	}
	
	.station-content {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex: 1;
		min-width: 0;
	}
	
	.presence-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.presence-active {
		background: var(--success-color, #10b981);
	}
	
	.presence-inactive {
		background: var(--warning-color, #f59e0b);
	}
	
	.presence-unknown {
		background: var(--muted-color, #6b7280);
	}
	
	.station-details {
		flex: 1;
		min-width: 0;
	}
	
	.callsign-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.25rem;
	}
	
	.callsign {
		font-weight: 600;
		color: var(--text-primary, #111827);
		font-size: 0.875rem;
	}
	
	.grid {
		font-size: 0.75rem;
		color: var(--text-primary, #111827);
		background: var(--border-color, #e5e7eb);
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		font-weight: 500;
	}
	
	.last-heard,
	.signal-info {
		font-size: 0.75rem;
		color: var(--text-muted, #6b7280);
		margin-bottom: 0.125rem;
	}
	
	.delete-btn {
		background: transparent;
		border: 1px solid var(--border-color, #d1d5db);
		border-radius: 0.25rem;
		padding: 0.25rem;
		cursor: pointer;
		color: var(--text-muted, #6b7280);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: background-color 0.2s;
		margin-left: 0.5rem;
	}
	
	.delete-btn:hover {
		background: var(--danger-bg, rgba(239, 68, 68, 0.1));
	}

	@media (max-width: 768px) {
		.list-header {
			padding: 0.75rem 1rem; /* Match message header mobile padding */
		}
		
		.search-container {
			padding: 0.75rem 1rem; /* Match mobile padding */
		}
		
		.sort-menu {
			right: 0;
			left: auto;
			min-width: 200px;
			width: max-content;
		}
	}
</style>