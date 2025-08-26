<script lang="ts">
	import { onMount, afterUpdate, tick } from 'svelte';
	import { messagesWithStatus, loadMessages, sendMessage, resendMessage } from '$lib/stores/messages.js';
	import { selectedCallsign, stations, calculatePresenceStatus, formatLastHeard } from '$lib/stores/stations.js';
	import { drawerOpen, toggleDrawer } from '$lib/stores/drawer.js';
	
	export let callsign: string;
	
	let messageText = '';
	let messagesContainer: HTMLDivElement;
	let showCommands = false;
	let sending = false;
	
	// JS8Call command templates
	const commandTemplates = [
		{ label: 'Inbox Message', value: ' MSG [text]' },
		{ label: 'Store Inbox Message', value: ' MSG TO:[callsign] [text]' },
		{ label: 'Query Messages', value: ' QUERY MSGS' },
		{ label: 'Query Message ID', value: ' QUERY MSG [ID]' },
		{ label: 'Query SNR', value: ' SNR?' },
		{ label: 'Query Hearing', value: ' HEARING?' },
		{ label: 'Query Callsign', value: ' QUERY CALL [callsign]' },
		{ label: 'Query Grid Square', value: ' GRID?' },
		{ label: 'Query Info', value: ' INFO?' },
		{ label: 'Query Status', value: ' STATUS?' }
	];
	
	$: {
		if (callsign) {
			loadMessages(callsign);
		}
	}
	
	// Get reactive presence data for this station
	$: station = $stations[callsign] || { callsign, lastHeard: null };
	$: presenceStatus = calculatePresenceStatus(station.lastHeard);
	$: presenceText = formatLastHeard(station.lastHeard);
	
	function formatTime(isoString: string): string {
		const date = new Date(isoString);
		return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
	}
	
	function getMessageClass(message: any): string {
		const baseClass = message.type === 'tx' ? 'message-sent' : 'message-received';
		const statusClass = message.sendingStatus ? `message-${message.sendingStatus}` : '';
		return `${baseClass} ${statusClass}`.trim();
	}
	
	function getStatusText(status: string): string {
		switch (status) {
			case 'queued': return 'Queued';
			case 'sending': return 'Sending...';
			case 'sent': return 'Sent';
			case 'failed': return 'Failed';
			default: return '';
		}
	}
	
	async function handleSendMessage(event: Event) {
		event.preventDefault();
		
		if (!messageText.trim() || sending) return;
		
		const text = messageText.trim();
		messageText = '';
		sending = true;
		
		try {
			await sendMessage(callsign, text);
			scrollToBottom();
		} catch (error) {
			console.error('Failed to send message:', error);
			// Could show error notification to user
		} finally {
			sending = false;
		}
	}
	
	function insertCommand(command: string) {
		messageText = command;
		showCommands = false;
		
		// Focus the input and position cursor after the command
		tick().then(() => {
			const input = document.getElementById('message-input') as HTMLInputElement;
			if (input) {
				input.focus();
				// Position cursor at end or at first bracket for editing
				const bracketIndex = command.indexOf('[');
				if (bracketIndex !== -1) {
					input.setSelectionRange(bracketIndex, command.indexOf(']') + 1);
				} else {
					input.setSelectionRange(command.length, command.length);
				}
			}
		});
	}
	
	function scrollToBottom() {
		if (messagesContainer) {
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}
	}
	
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			handleSendMessage(event);
		}
	}
	
	async function handleResendMessage(message: any) {
		try {
			await resendMessage(message.id, callsign, message.text);
		} catch (error) {
			console.error('Failed to resend message:', error);
		}
	}
	
	onMount(() => {
		scrollToBottom();
	});
	
	afterUpdate(() => {
		scrollToBottom();
	});
</script>

<div class="message-view">
	<div class="message-header">
		<div class="header-left">
			<button 
				class="drawer-toggle-btn"
				on:click={toggleDrawer}
				title="Toggle conversations"
			>
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="3" y1="6" x2="21" y2="6"></line>
					<line x1="3" y1="12" x2="21" y2="12"></line>
					<line x1="3" y1="18" x2="21" y2="18"></line>
				</svg>
			</button>
			
			<div class="conversation-info">
				<div class="presence-indicator presence-{presenceStatus}"></div>
				<h3 class="callsign">{callsign}</h3>
				<div class="last-heard">Last heard: {presenceText}</div>
			</div>
		</div>
		
		<button 
			class="commands-btn"
			class:active={showCommands}
			on:click={() => showCommands = !showCommands}
			title="JS8Call commands"
		>
			<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
				<path d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zM12 13a1 1 0 110-2 1 1 0 010 2zM12 20a1 1 0 110-2 1 1 0 010 2z"/>
			</svg>
		</button>
	</div>
	
	{#if showCommands}
		<div class="commands-menu">
			{#each commandTemplates as command}
				<button 
					class="command-item"
					on:click={() => insertCommand(command.value)}
				>
					{command.label}
				</button>
			{/each}
		</div>
	{/if}
	
	<div class="messages-container" bind:this={messagesContainer}>
		{#if $messagesWithStatus.length === 0}
			<div class="empty-messages">
				<p>No messages yet</p>
				<p class="empty-subtitle">Send a message to start the conversation</p>
			</div>
		{:else}
			<div class="messages">
				{#each $messagesWithStatus as message (message.id)}
					<div class="message {getMessageClass(message)}">
						<div class="message-content">
							<div class="message-text">{message.text}</div>
							<div class="message-time">{formatTime(message.time)}</div>
						</div>
						{#if message.sendingStatus}
							<div class="message-status-container">
								<span class="message-status">
									{getStatusText(message.sendingStatus)}
								</span>
								{#if message.sendingStatus === 'failed'}
									<button 
										class="resend-btn"
										on:click={() => handleResendMessage(message)}
										title="Resend message"
									>
										<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
											<path d="M4 12a8 8 0 0 1 8-8V2.5L16 6l-4 3.5V8a6 6 0 1 0 6 6h1.5a7.5 7.5 0 1 1-7.5-7.5z"/>
										</svg>
									</button>
								{/if}
							</div>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</div>
	
	<form class="message-input-form" on:submit={handleSendMessage}>
		<div class="input-container">
			<input
				id="message-input"
				type="text"
				bind:value={messageText}
				placeholder="Type a message here..."
				disabled={sending}
				class="message-input"
				on:keydown={handleKeydown}
				autocomplete="off"
			/>
			<button 
				type="submit" 
				class="send-button"
				disabled={!messageText.trim() || sending}
			>
				{#if sending}
					<svg class="loading-spinner" width="20" height="20" viewBox="0 0 24 24">
						<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="60" stroke-dashoffset="60">
							<animate attributeName="stroke-dashoffset" dur="2s" values="60;0" repeatCount="indefinite"/>
						</circle>
					</svg>
				{:else}
					Send
				{/if}
			</button>
		</div>
	</form>
</div>

<style>
	.message-view {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: var(--main-bg, white);
	}
	
	.message-header {
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
	
	.conversation-info {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	
	.presence-indicator {
		width: 12px;
		height: 12px;
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
	
	.callsign {
		margin: 0;
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--text-primary);
		line-height: 1.5;
	}
	
	.last-heard {
		font-size: 0.875rem;
		color: var(--text-muted, #6b7280);
	}
	
	.commands-btn {
		background: transparent;
		border: 1px solid var(--border-color, #d1d5db);
		border-radius: 0.375rem;
		padding: 0.5rem;
		cursor: pointer;
		color: var(--text-secondary, #6b7280);
		transition: all 0.2s;
	}
	
	.commands-btn:hover, .commands-btn.active {
		background: var(--hover-bg, #f3f4f6);
		color: var(--text-primary, #111827);
	}
	
	.commands-menu {
		background: var(--dropdown-bg, white);
		border: 1px solid var(--border-color, #e5e7eb);
		border-radius: 0.5rem;
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
		max-height: 200px;
		overflow-y: auto;
		z-index: 200; /* Above drawer (100) */
		position: fixed;
		top: 60px; /* Below header */
		right: 1rem;
		min-width: 200px;
	}
	
	.command-item {
		display: block;
		width: 100%;
		padding: 0.75rem 1.5rem;
		text-align: left;
		background: transparent;
		border: none;
		color: var(--text-primary, #374151);
		cursor: pointer;
		transition: background-color 0.2s;
		font-size: 0.875rem;
	}
	
	.command-item:hover {
		background: var(--hover-bg, #f3f4f6);
	}
	
	.messages-container {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
	}
	
	.empty-messages {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		color: var(--text-muted, #6b7280);
		text-align: center;
	}
	
	.empty-messages p {
		margin: 0;
	}
	
	.empty-subtitle {
		font-size: 0.875rem;
		margin-top: 0.5rem;
	}
	
	.messages {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.message {
		display: flex;
		flex-direction: column;
		max-width: 70%;
	}
	
	.message-received {
		align-self: flex-start;
	}
	
	.message-sent {
		align-self: flex-end;
	}
	
	.message-content {
		background: var(--message-bg, #f3f4f6);
		padding: 0.75rem 1rem;
		border-radius: 1rem;
		position: relative;
	}
	
	.message-sent .message-content {
		background: var(--primary-bg, #3b82f6);
		color: white;
	}
	
	.message-text {
		font-size: 0.875rem;
		line-height: 1.4;
		word-wrap: break-word;
	}
	
	.message-time {
		font-size: 0.75rem;
		opacity: 0.7;
		margin-top: 0.25rem;
	}
	
	.message-status-container {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 0.5rem;
		margin-top: 0.25rem;
	}
	
	.message-status {
		font-size: 0.75rem;
		color: var(--text-muted, #6b7280);
	}
	
	.resend-btn {
		background: transparent;
		border: 1px solid var(--border-color, #d1d5db);
		border-radius: 0.25rem;
		padding: 0.25rem;
		cursor: pointer;
		color: var(--text-muted, #6b7280);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
		font-size: 0.75rem;
	}
	
	.resend-btn:hover {
		background: var(--hover-bg, #f3f4f6);
		color: var(--text-primary, #111827);
		border-color: var(--text-muted, #6b7280);
	}
	
	.message-sending .message-content,
	.message-queued .message-content {
		opacity: 0.7;
	}
	
	.message-input-form {
		padding: 1rem 1.5rem;
		border-top: 1px solid var(--border-color, #e5e7eb);
		background: var(--form-bg, white);
	}
	
	.input-container {
		display: flex;
		gap: 0.75rem;
		align-items: flex-end;
	}
	
	.message-input {
		flex: 1;
		padding: 0.75rem 1rem;
		border: 1px solid var(--border-color, #d1d5db);
		border-radius: 1.5rem;
		font-size: 0.875rem;
		resize: none;
		min-height: 2.5rem;
		background: var(--input-bg, white);
		color: var(--text-primary, #111827);
	}
	
	.message-input:focus {
		outline: none;
		border-color: var(--primary-color, #3b82f6);
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}
	
	.message-input:disabled {
		background: var(--disabled-bg, #f9fafb);
		color: var(--text-disabled, #9ca3af);
	}
	
	.send-button {
		background: var(--primary-bg, #3b82f6);
		color: white;
		border: none;
		border-radius: 1.5rem;
		padding: 0.75rem 1.5rem;
		cursor: pointer;
		font-size: 0.875rem;
		font-weight: 500;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 80px;
	}
	
	.send-button:hover:not(:disabled) {
		background: var(--primary-hover, #2563eb);
	}
	
	.send-button:disabled {
		background: var(--disabled-bg, #d1d5db);
		color: var(--text-disabled, #9ca3af);
		cursor: not-allowed;
	}
	
	.loading-spinner {
		animation: spin 1s linear infinite;
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
		.message {
			max-width: 85%;
		}
		
		.drawer-toggle-btn {
			display: block;
		}
		
		.message-header {
			padding: 0.75rem 1rem;
		}
		
		.messages-container {
			padding: 0.75rem;
		}
		
		.message-input-form {
			padding: 0.75rem 1rem;
		}
	}
</style>