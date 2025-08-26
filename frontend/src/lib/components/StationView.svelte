<script lang="ts">
	import { onMount } from 'svelte';
	import { stations, loadStationDetails } from '$lib/stores/stations.js';
	import { drawerOpen, toggleDrawer } from '$lib/stores/drawer.js';
	
	export let callsign: string;
	
	let loading = false;
	
	// Get reactive station data
	$: station = $stations[callsign] || { callsign };
	
	function formatTimestamp(timestamp) {
		if (!timestamp) return 'Never';
		return new Date(timestamp).toLocaleString([], { 
			year: 'numeric', 
			month: 'short', 
			day: '2-digit', 
			hour: '2-digit', 
			minute: '2-digit' 
		});
	}
	
	function formatList(items, isLoading = false) {
		if (isLoading) return 'Loading...';
		if (!items || items.length === 0) return 'None';
		return items.join(', ');
	}
	
	function formatDistance(distance, units, isLoading = false) {
		if (isLoading) return 'Loading...';
		if (distance == null || !units) return 'Unknown';
		return `${distance} ${units}`;
	}
	
	async function refreshStationData() {
		if (loading) return;
		
		loading = true;
		try {
			await loadStationDetails(callsign);
		} catch (error) {
			console.error('Failed to refresh station data:', error);
		} finally {
			loading = false;
		}
	}
	
	onMount(() => {
		// Load station details when component mounts
		refreshStationData();
	});
	
	// Reload when callsign changes
	$: if (callsign) {
		refreshStationData();
	}
</script>

<div class="station-view">
	<div class="station-header">
		<div class="header-left">
			<button 
				class="drawer-toggle-btn"
				on:click={toggleDrawer}
				title="Toggle stations"
			>
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="3" y1="6" x2="21" y2="6"></line>
					<line x1="3" y1="12" x2="21" y2="12"></line>
					<line x1="3" y1="18" x2="21" y2="18"></line>
				</svg>
			</button>
			
			<div class="station-info">
				<h3 class="callsign">{callsign}</h3>
				{#if station.grid}
					<div class="grid-square">
						Grid: {station.grid}
						{#if station.distance !== null && station.distanceUnits}
							<span class="distance">({station.distance} {station.distanceUnits})</span>
						{:else if loading}
							<span class="distance">(Loading...)</span>
						{/if}
					</div>
				{/if}
			</div>
		</div>
		
		<button 
			class="refresh-btn"
			class:loading
			on:click={refreshStationData}
			disabled={loading}
			title="Refresh station data"
		>
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M23 4v6h-6"/>
				<path d="M1 20v-6h6"/>
				<path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
			</svg>
		</button>
	</div>
	
	<!-- Scrollable Content Container -->
	<div class="station-content">
		<!-- Station Data Section -->
		<div class="station-data">
			<div class="data-grid">
			<div class="data-item">
				<label>Callsign</label>
				<span>{station.callsign}</span>
			</div>
			
			<div class="data-item">
				<label>Last Heard</label>
				<span>{formatTimestamp(station.lastHeard)}</span>
			</div>
			
			<div class="data-item">
				<label>SNR</label>
				<span>{station.snr !== undefined ? `${station.snr} dB` : 'Unknown'}</span>
			</div>
			
			<div class="data-item">
				<label>Modem Speed</label>
				<span>{station.speed || 'Unknown'}</span>
			</div>
			
			<div class="data-item">
				<label>Grid Square</label>
				<span>{station.grid || 'Unknown'}</span>
			</div>
			
			<div class="data-item">
				<label>Distance</label>
				<span>{formatDistance(station.distance, station.distanceUnits, loading && station.grid)}</span>
			</div>
			
			<div class="data-item full-width">
				<label>Hearing</label>
				<span class="station-list">{formatList(station.hearing, loading)}</span>
			</div>
			
			<div class="data-item full-width">
				<label>Heard By</label>
				<span class="station-list">{formatList(station.heardBy, loading)}</span>
			</div>
			</div>
		</div>
		
		<!-- Map Section Placeholder -->
		<div class="map-section">
		<div class="map-header">
			<h4>Propagation Map</h4>
			<div class="map-controls">
				<!-- Future map controls will go here -->
			</div>
		</div>
		<div class="map-container">
			<div class="map-placeholder">
				<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
					<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
					<circle cx="12" cy="10" r="3"/>
				</svg>
				<p>Map coming soon...</p>
				<p class="placeholder-subtitle">This will show station locations and propagation paths</p>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.station-view {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: var(--main-bg, white);
	}
	
	.station-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 1.5rem;
		border-bottom: 1px solid var(--border-color, #e5e7eb);
		background: var(--header-bg, #f9fafb);
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	
	.drawer-toggle-btn {
		display: none;
		background: transparent;
		border: 1px solid var(--border-color, #d1d5db);
		border-radius: 0.375rem;
		padding: 0.5rem;
		cursor: pointer;
		color: var(--text-secondary, #6b7280);
		transition: all 0.2s;
	}

	.drawer-toggle-btn:hover {
		background: var(--hover-bg, #f3f4f6);
		color: var(--text-primary, #111827);
	}
	
	.station-info {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	
	.callsign {
		margin: 0;
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--text-primary);
		line-height: 1.5;
	}
	
	.grid-square {
		font-size: 0.875rem;
		color: var(--text-muted, #6b7280);
	}
	
	.distance {
		font-weight: 500;
		color: var(--text-secondary, #6b7280);
		margin-left: 0.5rem;
	}
	
	.refresh-btn {
		background: transparent;
		border: 1px solid var(--border-color, #d1d5db);
		border-radius: 0.375rem;
		padding: 0.5rem;
		cursor: pointer;
		color: var(--text-secondary, #6b7280);
		transition: all 0.2s;
	}

	.refresh-btn:hover:not(:disabled) {
		background: var(--hover-bg, #f3f4f6);
		color: var(--text-primary, #111827);
	}

	.refresh-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.refresh-btn.loading svg {
		animation: spin 1s linear infinite;
	}
	
	.station-content {
		flex: 1;
		overflow-y: auto;
	}
	
	.station-data {
		padding: 1.5rem;
		border-bottom: 1px solid var(--border-color, #e5e7eb);
	}
	
	.data-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
		max-width: 800px;
	}
	
	/* 3 columns on larger screens */
	@media (min-width: 900px) {
		.data-grid {
			grid-template-columns: repeat(3, 1fr);
		}
	}
	
	/* 1 column on very small screens */
	@media (max-width: 350px) {
		.data-grid {
			grid-template-columns: 1fr;
		}
	}
	
	.data-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	
	.data-item.full-width {
		grid-column: 1 / -1;
	}
	
	.data-item label {
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--text-secondary, #6b7280);
	}
	
	.data-item span {
		font-size: 0.875rem;
		color: var(--text-primary, #111827);
		padding: 0.5rem 0.75rem;
		background: var(--input-bg, #f9fafb);
		border: 1px solid var(--border-color, #e5e7eb);
		border-radius: 0.375rem;
	}
	
	.station-list {
		min-height: 2.5rem;
		word-wrap: break-word;
	}
	
	.map-section {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-height: 300px;
	}
	
	.map-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 1.5rem;
		border-bottom: 1px solid var(--border-color, #e5e7eb);
		background: var(--section-header-bg, #fafbfc);
	}
	
	.map-header h4 {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-primary, #111827);
	}
	
	.map-container {
		flex: 1;
		position: relative;
		background: var(--map-bg, #f8fafc);
	}
	
	.map-placeholder {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		color: var(--text-muted, #6b7280);
		text-align: center;
		padding: 2rem;
	}
	
	.map-placeholder svg {
		margin-bottom: 1rem;
		opacity: 0.5;
	}
	
	.map-placeholder p {
		margin: 0;
	}
	
	.placeholder-subtitle {
		font-size: 0.875rem;
		margin-top: 0.5rem !important;
		opacity: 0.7;
	}
	
	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}

	@media (max-width: 768px) {
		.drawer-toggle-btn {
			display: block;
		}
		
		.station-header {
			padding: 0.75rem 1rem;
		}
		
		.station-content {
			padding: 0;
		}
		
		.station-data {
			padding: 1rem;
		}
		
		.data-grid {
			gap: 0.75rem;
		}
		
		.map-header {
			padding: 0.75rem 1rem;
		}
	}
</style>