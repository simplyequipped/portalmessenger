<script lang="ts">
	import ConversationList from '$lib/components/ConversationList.svelte';
	import MessageView from '$lib/components/MessageView.svelte';
	import { selectedCallsign } from '$lib/stores/conversations.js';
</script>

<div class="messaging-view">
	<div class="sidebar">
		<ConversationList />
	</div>
	<div class="main-content">
		{#if $selectedCallsign}
			<MessageView callsign={$selectedCallsign} />
		{:else}
			<div class="no-conversation">
				<p>Select a conversation or start a new one</p>
			</div>
		{/if}
	</div>
</div>

<style>
	.messaging-view {
		display: flex;
		height: 100%;
		overflow: hidden;
	}

	.sidebar {
		width: 300px;
		border-right: 1px solid var(--border-color, #e5e7eb);
		background: var(--sidebar-bg, #f9fafb);
		overflow-y: auto;
	}

	.main-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.no-conversation {
		display: flex;
		align-items: center;
		justify-content: center;
		flex: 1;
		color: var(--text-muted, #6b7280);
	}

	@media (max-width: 768px) {
		.messaging-view {
			flex-direction: column;
		}
		
		.sidebar {
			width: 100%;
			height: 40%;
		}
	}
</style>