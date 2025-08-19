<script lang="ts">
	import StationList from '$lib/components/StationList.svelte';
	import StationView from '$lib/components/StationView.svelte';
	import { selectedStation } from '$lib/stores/stations.js';
	import { drawerOpen, closeDrawer, toggleDrawer } from '$lib/stores/drawer.js';
	
	// Close drawer on mobile when backdrop is clicked
	function handleBackdropClick() {
		closeDrawer();
	}
</script>

<div class="activity-view">
	<!-- Mobile backdrop -->
	{#if $drawerOpen}
		<div class="drawer-backdrop" on:click={handleBackdropClick}></div>
	{/if}
	
	<div class="sidebar" class:drawer-open={$drawerOpen}>
		<StationList />
	</div>
	
	<div class="main-content">
		{#if $selectedStation}
			<StationView callsign={$selectedStation} />
		{:else}
			<div class="no-station-view">
				<div class="no-station-header">
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
					</div>
					
					<!-- Invisible placeholder button to match header height -->
					<button class="placeholder-btn">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
							<path d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zM12 13a1 1 0 110-2 1 1 0 010 2zM12 20a1 1 0 110-2 1 1 0 010 2z"/>
						</svg>
					</button>
				</div>
				<div class="no-station-content">
					<p>Select a station to view activity details</p>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.activity-view {
		display: flex;
		height: 100%;
		overflow: hidden;
		position: relative;
	}

	.sidebar {
		width: 300px;
		border-right: 1px solid var(--border-color, #e5e7eb);
		background: var(--sidebar-bg, #f9fafb);
		overflow-y: auto;
		transition: transform 0.3s ease;
	}

	.main-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.no-station-view {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.no-station-header {
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

	.placeholder-btn {
		background: transparent;
		border: 1px solid transparent;
		border-radius: 0.375rem;
		padding: 0.5rem;
		opacity: 0;
		pointer-events: none;
		color: transparent;
	}

	.no-station-content {
		display: flex;
		align-items: center;
		justify-content: center;
		flex: 1;
		color: var(--text-muted, #6b7280);
	}

	.drawer-backdrop {
		display: none;
	}

	@media (max-width: 768px) {
		.activity-view {
			flex-direction: row; /* Keep side-by-side for drawer */
		}
		
		.drawer-toggle-btn {
			display: block;
		}

		.no-station-header {
			padding: 0.75rem 1rem; /* Match message header mobile padding */
		}
		
		.sidebar {
			position: fixed;
			top: 60px; /* Position below mobile header */
			left: 0;
			height: calc(100vh - 60px);
			width: 280px;
			z-index: 100; /* Lower z-index */
			transform: translateX(-100%);
			box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
		}

		.sidebar.drawer-open {
			transform: translateX(0);
		}

		.main-content {
			width: 100%;
			position: relative;
		}

		.drawer-backdrop {
			display: block;
			position: absolute;
			top: 60px; /* Start below mobile header */
			left: 0;
			width: 100%;
			height: calc(100% - 60px);
			background: rgba(0, 0, 0, 0.5);
			z-index: 99;
		}
	}
</style>