<script lang="ts">
	import { onMount } from 'svelte';
	import { derived } from 'svelte/store';
	import { conversationsWithUnread, selectedCallsign, selectConversation, deleteConversation, calculatePresenceStatus, formatLastHeard } from '$lib/stores/stations.js';
	import { loadMessages } from '$lib/stores/messages.js';
	import { closeDrawer } from '$lib/stores/drawer.js';
	
	let showAddForm = false;
	let newCallsign = '';
	let showDeleteMode = false;
	
	
	
	function handleSelectConversation(callsign: string) {
		selectConversation(callsign);
		// Close drawer immediately for better mobile UX
		closeDrawer();
		
		// Load messages in the background (don't await)
		loadMessages(callsign).catch(error => {
			console.error('Failed to load messages:', error);
		});
	}
	
	function showAddConversation() {
		showAddForm = true;
		// Focus the input after the DOM updates
		setTimeout(() => {
			const input = document.getElementById('new-callsign-input');
			if (input) input.focus();
		}, 0);
	}
	
	function hideAddConversation() {
		showAddForm = false;
		newCallsign = '';
	}
	
	function validateCallsignOrGroup(input: string): { valid: boolean; error?: string } {
		if (!input) {
			return { valid: false, error: 'Please enter a callsign or group' };
		}
		
		// Check if it's a group (starts with @)
		if (input.startsWith('@')) {
			if (input.length <= 1) {
				return { valid: false, error: 'Group name cannot be empty after @' };
			}
			if (input.length > 10) { // @ + 9 characters max
				return { valid: false, error: 'Group name must be 9 characters or less' };
			}
			return { valid: true };
		}
		
		// It's a callsign - validate callsign format
		// Remove suffix after slash (e.g., "W1ABC/P" -> "W1ABC")
		const baseCallsign = input.split('/')[0];
		
		if (baseCallsign.length === 0 || baseCallsign.length > 9) {
			return { valid: false, error: 'Callsign must be 1-9 characters (before any slash)' };
		}
		
		// Must contain at least one number
		if (!/\d/.test(baseCallsign)) {
			return { valid: false, error: 'Callsign must contain at least one number' };
		}
		
		// Should only contain alphanumeric characters
		if (!/^[A-Z0-9]+$/.test(baseCallsign)) {
			return { valid: false, error: 'Callsign can only contain letters and numbers' };
		}
		
		return { valid: true };
	}

	async function handleAddConversation(event: Event) {
		event.preventDefault();
		const input = newCallsign.trim().toUpperCase();
		
		// Validate the input
		const validation = validateCallsignOrGroup(input);
		if (!validation.valid) {
			alert(validation.error);
			return;
		}
		
		try {
			// This will create the conversation and load messages
			await handleSelectConversation(input);
			hideAddConversation();
		} catch (error) {
			console.error('Failed to add conversation:', error);
			alert('Failed to add conversation');
		}
	}
	
	function toggleDeleteMode() {
		showDeleteMode = !showDeleteMode;
	}
	
	async function handleDeleteConversation(event: Event, callsign: string) {
		event.stopPropagation();
		
		if (confirm(`Delete entire conversation with ${callsign}?`)) {
			try {
				await deleteConversation(callsign);
				showDeleteMode = false;
			} catch (error) {
				console.error('Failed to delete conversation:', error);
				alert('Failed to delete conversation');
			}
		}
	}
	
	onMount(() => {
		// Load initial conversations
		// This would typically come from the backend API
		// For now, conversations are populated from message events
	});
</script>

<div class="conversation-list">
	<div class="list-header">
		<h2>Conversations</h2>
		<div class="header-actions">
			{#if $conversationsWithUnread.length > 0}
				<button 
					class="delete-toggle-btn"
					class:active={showDeleteMode}
					on:click={toggleDeleteMode}
					title="Delete conversations"
				>
					<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
						<path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
					</svg>
				</button>
			{/if}
			<button class="add-btn" on:click={showAddConversation} title="New conversation">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M12 5v14m7-7H5"/>
				</svg>
			</button>
		</div>
	</div>
	
	{#if showAddForm}
		<form class="add-form" on:submit={handleAddConversation}>
			<input 
				id="new-callsign-input"
				type="text" 
				bind:value={newCallsign}
				placeholder="Enter callsign (e.g. W1ABC) or @group"
				class="callsign-input"
				autocomplete="off"
				maxlength="10"
			/>
			<div class="form-actions">
				<button type="submit" class="add-submit-btn">Add</button>
				<button type="button" class="cancel-btn" on:click={hideAddConversation}>Cancel</button>
			</div>
		</form>
	{/if}
	
	<div class="conversations">
		{#if $conversationsWithUnread.length === 0}
			<div class="empty-state">
				<p>No conversations yet</p>
				<p class="empty-subtitle">Start a new conversation to get started</p>
			</div>
		{:else}
			{#each $conversationsWithUnread as conversation (conversation.callsign)}
				{@const lastHeard = conversation.lastHeard}
				{@const status = calculatePresenceStatus(lastHeard)}
				{@const text = formatLastHeard(lastHeard)}
				
				<div 
					class="conversation-item"
					class:selected={$selectedCallsign === conversation.callsign}
					class:has-unread={conversation.unreadCount > 0}
					on:click={() => handleSelectConversation(conversation.callsign)}
					role="button"
					tabindex="0"
					on:keydown={(e) => e.key === 'Enter' && handleSelectConversation(conversation.callsign)}
				>
					<div class="conversation-content">
						<div 
							class="presence-indicator presence-{status}"
						></div>
						
						<div class="conversation-details">
							<div class="callsign-row">
								<span class="callsign" class:unread={conversation.unreadCount > 0}>
									{conversation.callsign}
								</span>
								{#if conversation.unreadCount > 0}
									<span class="unread-count">{conversation.unreadCount}</span>
								{/if}
							</div>
							<div class="last-heard">
								Last heard: {text}
							</div>
						</div>
					</div>
					
					{#if showDeleteMode}
						<button 
							class="delete-btn"
							on:click={(e) => handleDeleteConversation(e, conversation.callsign)}
							title="Delete conversation"
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
	.conversation-list {
		height: 100%;
		display: flex;
		flex-direction: column;
		background: var(--sidebar-bg, #f9fafb);
	}
	
	.list-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 1.5rem;
		border-bottom: 1px solid var(--border-color, #e5e7eb);
		background: var(--header-bg);
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
	
	.add-btn, .delete-toggle-btn {
		background: transparent;
		border: 1px solid var(--border-color, #d1d5db);
		border-radius: 0.375rem;
		padding: 0.5rem;
		cursor: pointer;
		color: var(--text-secondary, #6b7280);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}
	
	.add-btn:hover, .delete-toggle-btn:hover {
		background: var(--hover-bg, #f3f4f6);
		color: var(--text-primary, #111827);
	}
	
	.delete-toggle-btn.active {
		background: var(--danger-bg, #fee2e2);
		color: var(--danger-text, #dc2626);
		border-color: var(--danger-border, #fecaca);
	}
	
	.add-form {
		padding: 1rem;
		border-bottom: 1px solid var(--border-color, #e5e7eb);
		background: var(--form-bg, white);
	}
	
	.callsign-input {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid var(--border-color, #d1d5db);
		border-radius: 0.375rem;
		font-size: 0.875rem;
		margin-bottom: 0.75rem;
		background: var(--input-bg, white);
		color: var(--text-primary, #111827);
	}
	
	.callsign-input:focus {
		outline: none;
		border-color: var(--primary-color, #3b82f6);
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}
	
	.form-actions {
		display: flex;
		gap: 0.5rem;
	}
	
	.add-submit-btn, .cancel-btn {
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.add-submit-btn {
		background: var(--primary-bg, #3b82f6);
		color: white;
		border: none;
	}
	
	.add-submit-btn:hover {
		background: var(--primary-hover, #2563eb);
	}
	
	.cancel-btn {
		background: transparent;
		color: var(--text-secondary, #6b7280);
		border: 1px solid var(--border-color, #d1d5db);
	}
	
	.cancel-btn:hover {
		background: var(--hover-bg, #f3f4f6);
	}
	
	.conversations {
		flex: 1;
		overflow-y: auto;
	}
	
	.empty-state {
		padding: 2rem 1rem;
		text-align: center;
		color: var(--text-muted, #6b7280);
	}
	
	.empty-state p {
		margin: 0;
	}
	
	.empty-subtitle {
		font-size: 0.875rem;
		margin-top: 0.5rem;
	}
	
	.conversation-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1rem;
		cursor: pointer;
		border-bottom: 1px solid var(--border-light, #f3f4f6);
		transition: background-color 0.2s;
	}
	
	.conversation-item:hover {
		background: var(--hover-bg, rgba(59, 130, 246, 0.05));
	}
	
	.conversation-item.selected {
		background: var(--selected-bg, rgba(59, 130, 246, 0.1));
		border-right: 3px solid var(--primary-color, #3b82f6);
	}
	
	.conversation-item.has-unread {
		background: var(--unread-bg, rgba(59, 130, 246, 0.02));
	}
	
	.conversation-content {
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
	
	.conversation-details {
		flex: 1;
		min-width: 0;
	}
	
	.callsign-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.25rem;
	}
	
	.callsign {
		font-weight: 500;
		color: var(--text-primary, #111827);
		font-size: 0.875rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.callsign.unread {
		font-weight: 700;
	}
	
	.unread-count {
		background: var(--primary-bg, #3b82f6);
		color: white;
		border-radius: 50%;
		min-width: 1.25rem;
		height: 1.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.75rem;
		font-weight: 600;
		margin-left: 0.5rem;
	}
	
	.last-heard {
		font-size: 0.75rem;
		color: var(--text-muted, #6b7280);
	}
	
	.delete-btn {
		background: transparent;
		border: none;
		color: var(--danger-color, #ef4444);
		cursor: pointer;
		padding: 0.25rem;
		border-radius: 0.25rem;
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
	}
</style>