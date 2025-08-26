<script lang="ts">
	import { onMount } from 'svelte';
	import { 
		settings, 
		settingsLoading, 
		restartRequired, 
		settingsErrors,
		loadSettings,
		updateMultipleSettings,
		restartJS8Call
	} from '$lib/stores/settings.js';
	import { toast } from '$lib/stores/toast.ts';
	
	let formData: Record<string, string> = {};
	let saveAttempted = false;
	let showAdvanced = false;
	let advancedSectionRef: HTMLElement;
	
	// Sort settings by order and group by advanced property
	$: sortedSettings = Object.entries($settings)
		.filter(([_, setting]) => setting && setting.display)
		.sort(([_, a], [__, b]) => (a.order || 999) - (b.order || 999));
		
	$: basicSettings = sortedSettings.filter(([_, setting]) => !setting.advanced);
	$: advancedSettings = sortedSettings.filter(([_, setting]) => setting.advanced);
	$: hasErrors = Object.keys($settingsErrors).length > 0;
	$: canSave = Object.keys(formData).length > 0 && hasFormChanges() && !$settingsLoading && !hasErrors;
	// Validate fields and clear errors when they become valid
	$: {
		if (Object.keys(formData).length > 0) {
			for (const [key, value] of Object.entries(formData)) {
				if ($settingsErrors[key] && validateField(key, value)) {
					clearFieldError(key);
				}
			}
		}
	}
	
	
	
	function initializeFormData() {
		const newFormData: Record<string, string> = {};
		for (const [key, setting] of Object.entries($settings)) {
			if (setting.display) {
				newFormData[key] = setting.value;
			}
		}
		formData = newFormData;
	}
	
	function resetForm() {
		initializeFormData();
		saveAttempted = false;
	}
	
	function isFieldRequired(key: string, setting: any): boolean {
		return setting.required && (!formData[key] || formData[key] === '');
	}
	
	function getFieldError(key: string): string | null {
		return $settingsErrors[key] || null;
	}
	
	function validateField(key: string, value: string): boolean {
		const setting = $settings[key];
		if (!setting) return true;
		
		// Run the validation function if it exists
		if (setting.validate && typeof setting.validate === 'function') {
			try {
				return setting.validate(value);
			} catch (error) {
				return false;
			}
		}
		
		// Basic required field validation
		if (setting.required && (!value || value.trim() === '')) {
			return false;
		}
		
		return true;
	}
	
	function clearFieldError(key: string) {
		settingsErrors.update(errors => {
			const { [key]: removed, ...rest } = errors;
			return rest;
		});
	}
	
	function hasFormChanges(): boolean {
		for (const [key, setting] of Object.entries($settings)) {
			if (setting.display && formData[key] !== setting.value) {
				return true;
			}
		}
		return false;
	}
	
	async function handleSaveSettings(event: Event) {
		event.preventDefault();
		saveAttempted = true;
		
		if (!hasFormChanges()) {
			showMessage('No changes to save', 'info');
			return;
		}
		
		// Build object with only changed values
		const changedSettings: Record<string, string> = {};
		for (const [key, setting] of Object.entries($settings)) {
			if (setting.display && formData[key] !== setting.value) {
				changedSettings[key] = formData[key];
			}
		}
		
		try {
			const result = await updateMultipleSettings(changedSettings);
			
			if (result.success) {
				if (result.needsRestart) {
					showMessage('Settings saved, restarting JS8Call...', 'info');
					// Auto-restart after a short delay
					setTimeout(async () => {
						try {
							await restartJS8Call();
							showMessage('Settings saved and JS8Call restarted successfully', 'success');
						} catch (error) {
							console.error('Restart failed:', error);
							showMessage('Settings saved but JS8Call restart failed', 'warning');
						}
					}, 1000);
				} else {
					showMessage('Settings saved successfully', 'success');
				}
				saveAttempted = false;
			} else {
				showMessage('Some settings could not be saved - check validation errors', 'error');
			}
		} catch (error) {
			console.error('Failed to save settings:', error);
			showMessage('Failed to save settings', 'error');
		}
	}
	
	function showMessage(message: string, type: 'success' | 'error' | 'info' | 'warning') {
		toast[type](message);
	}
	
	function toggleAdvanced() {
		showAdvanced = !showAdvanced;
		
		// Scroll to advanced section when opened
		if (showAdvanced && advancedSectionRef) {
			// Use setTimeout to wait for the DOM to update and render the expanded content
			setTimeout(() => {
				advancedSectionRef.scrollIntoView({ 
					behavior: 'smooth', 
					block: 'start' 
				});
			}, 100);
		}
	}
	
	function renderFieldInput(setting: any) {
		const key = setting.setting;
		const hasError = getFieldError(key);
		const isRequired = isFieldRequired(key, setting);
		
		if (setting.options && setting.options.length > 0) {
			// Dropdown/select field
			return { type: 'select', options: setting.options };
		} else {
			// Text input field
			return { type: 'text' };
		}
	}
	
	onMount(async () => {
		try {
			await loadSettings();
			initializeFormData();
		} catch (error) {
			console.error('Failed to load settings:', error);
			showMessage('Failed to load settings', 'error');
		}
	});
	
	// Watch for settings changes to reinitialize form
	$: if (Object.keys($settings).length > 0) {
		initializeFormData();
	}
</script>

<div class="settings-page">
	<div class="settings-header">
		<h1>Settings</h1>
	</div>
	
	<!-- Toast notifications will appear in top-right corner -->
	
	{#if hasErrors}
		<div class="status-message status-error">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
				<path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
			</svg>
			Error - see details below
		</div>
	{/if}
	
	<div class="settings-content">
		<form id="settings-form" on:submit={handleSaveSettings} class="settings-form">
			<!-- Basic Settings -->
			{#each basicSettings as [key, setting] (key)}
				{@const fieldConfig = renderFieldInput(setting)}
				{@const hasError = getFieldError(key)}
				{@const isRequired = isFieldRequired(key, setting)}
				
				<div class="setting-row">
					<label for={key} class="setting-label">
						{setting.label}
						{#if setting.required}
							<span class="required-indicator">*</span>
						{/if}
					</label>
					
					{#if fieldConfig.type === 'select'}
						<select 
							id={key} 
							bind:value={formData[key]}
							class="setting-input"
							class:error={hasError}
							class:required={isRequired && saveAttempted}
						>
							{#each fieldConfig.options as option}
								<option value={option}>
									{option.charAt(0).toUpperCase() + option.slice(1)}
								</option>
							{/each}
						</select>
					{:else}
						<input 
							id={key}
							type="text"
							bind:value={formData[key]}
							class="setting-input"
							class:error={hasError}
							class:required={isRequired && saveAttempted}
							placeholder={setting.default}
						/>
					{/if}
					
					{#if hasError}
						<div class="field-error">{hasError}</div>
					{/if}
					
					{#if isRequired && saveAttempted}
						<div class="field-error">This field is required</div>
					{/if}
				</div>
			{/each}
			
			<!-- Advanced Settings Section -->
			{#if advancedSettings.length > 0}
				<div class="advanced-section" bind:this={advancedSectionRef}>
					<button
						type="button"
						class="advanced-toggle"
						on:click={toggleAdvanced}
					>
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="chevron" class:rotated={showAdvanced}>
							<polyline points="6,9 12,15 18,9"></polyline>
						</svg>
						Advanced
					</button>
					
					{#if showAdvanced}
						<div class="advanced-settings">
							{#each advancedSettings as [key, setting] (key)}
								{@const fieldConfig = renderFieldInput(setting)}
								{@const hasError = getFieldError(key)}
								{@const isRequired = isFieldRequired(key, setting)}
								
								<div class="setting-row">
									<label for={key} class="setting-label">
										{setting.label}
										{#if setting.required}
											<span class="required-indicator">*</span>
										{/if}
									</label>
									
									{#if fieldConfig.type === 'select'}
										<select 
											id={key} 
											bind:value={formData[key]}
											class="setting-input"
											class:error={hasError}
											class:required={isRequired && saveAttempted}
										>
											{#each fieldConfig.options as option}
												<option value={option}>
													{option.charAt(0).toUpperCase() + option.slice(1)}
												</option>
											{/each}
										</select>
									{:else}
										<input 
											id={key}
											type="text"
											bind:value={formData[key]}
											class="setting-input"
											class:error={hasError}
											class:required={isRequired && saveAttempted}
											placeholder={setting.default}
										/>
									{/if}
									
									{#if hasError}
										<div class="field-error">{hasError}</div>
									{/if}
									
									{#if isRequired && saveAttempted}
										<div class="field-error">This field is required</div>
									{/if}
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
		</form>
	</div>
	
	<div class="settings-footer">
		<div class="footer-actions">
			<button 
				type="button" 
				class="reset-button"
				on:click={resetForm}
				disabled={$settingsLoading || !hasFormChanges()}
			>
				Reset
			</button>
			<button 
				type="submit" 
				class="save-button"
				form="settings-form"
				on:click={handleSaveSettings}
				disabled={!canSave}
			>
				{#if $settingsLoading}
					<svg class="loading-spinner" width="16" height="16" viewBox="0 0 24 24">
						<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="60" stroke-dashoffset="60">
							<animate attributeName="stroke-dashoffset" dur="2s" values="60;0" repeatCount="indefinite"/>
						</circle>
					</svg>
					Saving...
				{:else}
					Save Settings
				{/if}
			</button>
		</div>
		
		{#if $restartRequired}
			<div class="restart-notice">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
					<path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
				</svg>
				Some changes require JS8Call to restart
			</div>
		{/if}
	</div>
</div>

<style>
	.settings-page {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: var(--main-bg, white);
	}
	
	.settings-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1.5rem 2rem 1rem;
		border-bottom: 1px solid var(--border-color, #e5e7eb);
	}
	
	.settings-header h1 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 600;
		color: var(--text-primary, #111827);
	}
	
	.status-message {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin: 1rem 2rem;
		padding: 0.75rem 1rem;
		border-radius: 0.5rem;
		font-size: 0.875rem;
		font-weight: 500;
	}
	
	.status-error {
		background: var(--danger-bg, #fee2e2);
		color: var(--danger-text, #991b1b);
		border: 1px solid var(--danger-border, #fca5a5);
	}
	
	.settings-content {
		flex: 1;
		overflow-y: auto;
		padding: 1.5rem 2rem;
	}
	
	.settings-form {
		max-width: 600px;
	}
	
	.setting-row {
		margin-bottom: 1.5rem;
	}
	
	.setting-label {
		display: block;
		margin-bottom: 0.5rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--text-primary, #374151);
	}
	
	.required-indicator {
		color: var(--danger-color, #ef4444);
		margin-left: 0.25rem;
	}
	
	.setting-input {
		width: 100%;
		padding: 0.75rem 1rem;
		border: 1px solid var(--border-color, #d1d5db);
		border-radius: 0.375rem;
		font-size: 0.875rem;
		transition: all 0.2s;
		background: var(--input-bg, white);
		color: var(--text-primary, #111827) !important;
	}
	
	.setting-input:focus {
		outline: none;
		border-color: var(--primary-color, #3b82f6);
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}
	
	.setting-input.error {
		border-color: var(--danger-color, #ef4444);
		color: #111827 !important;
	}
	
	.setting-input.required {
		border-color: var(--warning-color, #f59e0b);
		background: var(--warning-bg, #fffbeb);
		color: #111827 !important;
	}
	
	.field-error {
		margin-top: 0.25rem;
		font-size: 0.75rem;
		color: var(--danger-color, #ef4444);
	}
	
	.settings-footer {
		border-top: 1px solid var(--border-color, #e5e7eb);
		padding: 1rem 2rem;
		background: var(--footer-bg, #f9fafb);
	}
	
	.footer-actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.75rem;
		margin-bottom: 0.5rem;
	}
	
	.reset-button, .save-button {
		padding: 0.75rem 1.5rem;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.reset-button {
		background: transparent;
		color: var(--text-secondary, #6b7280);
		border: 1px solid var(--border-color, #d1d5db);
	}
	
	.reset-button:hover:not(:disabled) {
		background: var(--hover-bg, #f3f4f6);
		color: var(--text-primary, #374151);
	}
	
	.save-button {
		background: var(--primary-bg, #3b82f6);
		color: white;
		border: none;
	}
	
	.save-button:hover:not(:disabled) {
		background: var(--primary-hover, #2563eb);
	}
	
	.reset-button:disabled, .save-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.restart-notice {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
		color: var(--warning-text, #d97706);
		background: var(--warning-bg, #fffbeb);
		padding: 0.5rem 0.75rem;
		border-radius: 0.375rem;
		border: 1px solid var(--warning-border, #fed7aa);
	}
	
	.loading-spinner {
		animation: spin 1s linear infinite;
	}
	
	.advanced-section {
		margin-top: 2rem;
		border-top: 1px solid var(--border-color, #e5e7eb);
		padding-top: 1.5rem;
	}
	
	.advanced-toggle {
		background: transparent;
		border: none;
		color: var(--text-secondary, #6b7280);
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		font-weight: 500;
		padding: 0.5rem 0;
		transition: color 0.2s;
		width: 100%;
		justify-content: flex-start;
	}
	
	.advanced-toggle:hover {
		color: var(--text-primary, #374151);
	}
	
	.advanced-toggle .chevron {
		transition: transform 0.2s;
	}
	
	.advanced-toggle .chevron.rotated {
		transform: rotate(180deg);
	}
	
	.advanced-settings {
		margin-top: 1rem;
		padding-left: 0.5rem;
		border-left: 2px solid var(--border-light, #f3f4f6);
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
		.settings-header {
			padding: 1rem;
			flex-direction: column;
			align-items: flex-start;
			gap: 0.5rem;
		}
		
		.settings-content {
			padding: 1rem;
		}
		
		.settings-footer {
			padding: 1rem;
		}
		
		.footer-actions {
			flex-direction: column-reverse;
		}
		
		.reset-button, .save-button {
			width: 100%;
			justify-content: center;
		}
	}
</style>