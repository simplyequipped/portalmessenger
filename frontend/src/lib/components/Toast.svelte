<script lang="ts">
	import { toasts, removeToast } from '$lib/stores/toast.ts';
	import { fly } from 'svelte/transition';
	
	function getToastStyles(type: string) {
		switch (type) {
			case 'success':
				return 'toast-success';
			case 'error':
				return 'toast-error';
			case 'warning':
				return 'toast-warning';
			case 'info':
			default:
				return 'toast-info';
		}
	}
	
	function getIcon(type: string) {
		switch (type) {
			case 'success':
				return '✓';
			case 'error':
				return '✕';
			case 'warning':
				return '⚠';
			case 'info':
			default:
				return 'ℹ';
		}
	}
</script>

<!-- Toast Container -->
<div class="toast-container">
	{#each $toasts as toast (toast.id)}
		<div class="toast {getToastStyles(toast.type)}" role="alert" in:fly={{ x: 300, duration: 300 }} out:fly={{ x: 300, duration: 300 }}>
			<div class="toast-content">
				<span class="toast-icon">{getIcon(toast.type)}</span>
				<span class="toast-message">{toast.message}</span>
				<button 
					class="toast-close" 
					on:click={() => removeToast(toast.id)}
					aria-label="Close notification"
				>
					×
				</button>
			</div>
		</div>
	{/each}
</div>

<style>
	.toast-container {
		position: fixed;
		top: 5rem;
		right: 1rem;
		z-index: 9999;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		max-width: 400px;
	}
	
	.toast {
		background: var(--dropdown-bg, white);
		color: var(--text-primary, #111827);
		border: 1px solid var(--border-color, #e5e7eb);
		border-radius: 0.5rem;
		box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
		min-width: 300px;
	}
	
	.toast-success {
		border-left: 4px solid var(--success-color, #10b981);
	}
	
	.toast-error {
		border-left: 4px solid var(--danger-color, #ef4444);
	}
	
	.toast-warning {
		border-left: 4px solid var(--warning-color, #f59e0b);
	}
	
	.toast-info {
		border-left: 4px solid var(--primary-color, #3b82f6);
	}
	
	.toast-content {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.875rem 1rem;
	}
	
	.toast-icon {
		font-size: 1.125rem;
		font-weight: bold;
		flex-shrink: 0;
	}
	
	.toast-success .toast-icon {
		color: var(--success-color, #10b981);
	}
	
	.toast-error .toast-icon {
		color: var(--danger-color, #ef4444);
	}
	
	.toast-warning .toast-icon {
		color: var(--warning-color, #f59e0b);
	}
	
	.toast-info .toast-icon {
		color: var(--primary-color, #3b82f6);
	}
	
	.toast-message {
		flex: 1;
		font-size: 0.875rem;
		line-height: 1.25rem;
	}
	
	.toast-close {
		background: transparent;
		border: none;
		color: currentColor;
		cursor: pointer;
		font-size: 1.25rem;
		line-height: 1;
		padding: 0.25rem;
		border-radius: 0.25rem;
		transition: background-color 0.2s;
		flex-shrink: 0;
	}
	
	.toast-close:hover {
		background: var(--hover-bg, #f3f4f6);
	}
	
	
	/* Mobile responsive */
	@media (max-width: 640px) {
		.toast-container {
			left: 1rem;
			right: 1rem;
			max-width: none;
		}
		
		.toast {
			min-width: auto;
		}
	}
</style>