# Portal Messenger Frontend

Svelte frontend for Portal Messenger - HF radio messaging web application using pyjs8call.

## Architecture

This frontend is built with SvelteKit and TypeScript, providing a modern messaging interface that integrates with:
- **Portal Messenger Backend**: REST API for message/conversation persistence and settings storage
- **pyjs8call API**: WebSocket + REST API for real-time JS8Call integration

### Key Components

- **ConversationList**: Sidebar showing conversations with unread indicators
- **MessageView**: Chat interface for sending/receiving messages with JS8Call command templates
- **Settings**: Form for configuring both Portal Messenger and pyjs8call settings
- **Header**: Navigation and connection status indicators

### Data Flow

1. **Incoming Messages**: pyjs8call WebSocket → Store in backend → Update UI
2. **Outgoing Messages**: User input → Send via pyjs8call API → Store in backend → Update UI
3. **Settings**: UI changes → Save to backend → Apply to pyjs8call (if applicable)

## Development

Install dependencies:
```bash
npm install
```

Start development server:
```bash
npm run dev
```

The frontend expects:
- Portal Messenger Backend running on `localhost:8080` (configurable via settings)
- pyjs8call API running on `localhost:8080` (configurable via settings)

## Building

Create production build:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Configuration

The frontend reads pyjs8call API connection settings from the backend:
- `pyjs8call-api-host`: Default 'localhost'
- `pyjs8call-api-port`: Default 8080

These can be changed in the Settings page.

## Features

- Real-time messaging via WebSocket
- Message persistence and conversation management  
- JS8Call command templates in message composer
- Connection status monitoring for all services
- Responsive design for desktop and mobile
- Dark/light theme support
- Settings validation and JS8Call restart management

## Browser Support

Modern browsers with WebSocket support:
- Chrome/Edge 88+
- Firefox 86+
- Safari 14+