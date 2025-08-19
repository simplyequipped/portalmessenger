<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Header from '$lib/components/Header.svelte';
	import Toast from '$lib/components/Toast.svelte';
	import { websocketService } from '$lib/services/websocket.ts';
	import { settings, loadSettings } from '$lib/stores/settings.js';

	let { children } = $props();
	
	// Detect system theme preference
	function getSystemTheme(): 'light' | 'dark' {
		if (typeof window !== 'undefined' && window.matchMedia) {
			return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
		}
		return 'dark'; // fallback
	}

	// Apply theme and font size based on settings
	$effect(() => {
		if (typeof document !== 'undefined' && $settings.theme && $settings.size) {
			// Remove existing theme and size classes
			const existingClasses = document.documentElement.className
				.split(' ')
				.filter(cls => !cls.startsWith('theme-') && !cls.startsWith('size-'));
			
			// Determine actual theme to apply
			let actualTheme: string;
			const themeSetting = $settings.theme.value || 'auto';
			
			if (themeSetting === 'auto') {
				actualTheme = getSystemTheme();
			} else {
				actualTheme = themeSetting;
			}
			
			// Apply theme and font size
			const fontSize = $settings.size.value || 'normal';
			
			document.documentElement.className = [...existingClasses, `theme-${actualTheme}`, `size-${fontSize}`].join(' ');
		}
	});

	onMount(async () => {
		try {
			// Load settings first
			await loadSettings();
			
			// Give a small delay to ensure API URL updates are complete
			await new Promise(resolve => setTimeout(resolve, 100));
			
			// Initialize WebSocket service and connection monitoring
			await websocketService.initialize();
			
		} catch (error) {
			console.error('Failed to initialize Portal Messenger:', error);
		}
	});

	onDestroy(() => {
		// Clean up WebSocket service
		websocketService.destroy();
	});
</script>

<svelte:head>
	<title>Portal Messenger</title>
	<link rel="icon" href={favicon} />
	<meta name="viewport" content="width=device-width,initial-scale=1.0" />
</svelte:head>

<div class="app">
	<Header />
	<main>
		{@render children?.()}
	</main>
	<Toast />
</div>

<style>
	.app {
		display: flex;
		flex-direction: column;
		height: 100vh;
		height: 100dvh; /* Use dynamic viewport height for mobile */
		overflow: hidden;
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
	}

	main {
		flex: 1;
		overflow: hidden;
	}
</style>
