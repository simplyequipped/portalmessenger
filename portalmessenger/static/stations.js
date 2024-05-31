
// construct new station element based on given station data
function newStation(station) {
	stationElement = $('.station.original-hidden').clone();
	stationElement.attr('name', station.username);
	stationElement.find('.chat-name').html(station.username);
	stationElement.click(stationClick);
	stationElement.removeClass('original-hidden');
	setLastHeard(station.username, station.time);
    stationElement.find('.icon-delete').hide();
    stationElement.find('.icon-delete').click(stationDeleteClick);
	stationElement.appendTo('.content');
}

// create or update spot stations sent from the server
function handleSpot(station) {
	if ( findStation(station.username).length == 0 ) {
		newStation(station);
		stationElement = findStation(station.username);
		stationElement.addClass('spot');
		setLastHeard(station.username, station.time);

		if ( selectedTab() != 'activity' ) {
			stationElement.hide();
		}
	}
	else {
		setLastHeard(station.username, station.time);
		findStation(station.username).addClass('spot');
	}
}

// create or update conversation stations sent from the server
function handleConversation(station) {
	if ( findStation(station.username).length == 0 ) {
		newStation(station);
		stationElement = findStation(station.username);
		stationElement.addClass('conversation');
		setLastHeard(station.username, station.time);
	    setLastMsgHeard(station.username, station.time);

		if ( selectedTab() != 'conversations' ) {
			stationElement.hide();
		}
	}
	else {
		setLastHeard(station.username, station.time);
		setLastMsgHeard(station.username, station.time);
		findStation(station.username).addClass('conversation');
	}


	if ( station.unread ) {
		markUnread(station.username);
	}
	else {
		markRead(station.username);
	}
}

// find and return the station DOM element based on given username 
function findStation(username) {
	return $(".station[name='" + username + "']");
}

// get station presence status based on given username
function getPresence(username) {
	station = findStation(username)
	if ( station.find('.presence-indicator').hasClass("presence-active") ) {
		return "active";
	}
	else if ( station.find(".presence-indicator").hasClass("presence-inactive") ) {
		return "inactive";
	}
	else if ( station.find(".presence-indicator").hasClass("presence-unknown") ) {
		return "unknown";
	}
	else {
		return "none";
	}
}

// determine and set presence based on minutes since last heard
function updatePresence(username, last_heard_minutes) {
	setPresence(username, presenceText(last_heard_minutes));
}

// set station to given presence based on given username
function setPresence(username, presence) {
	station = findStation(username);
	presenceElement = station.find('.presence-indicator');
	currentPresence = getPresence(username);

	if ( getPresence(username) !== "none" ) {
		presenceElement.removeClass("presence-" + currentPresence);
	}
	presenceElement.addClass("presence-" + presence);
}

// update station last heard time and presence based on given
// username and minutes since last heard
function setLastHeard(username, lastHeard) {
	if ( lastHeard == null ) {
		lastHeard = 0;
	}

	now = new Date();
	then = new Date(lastHeard * 1000);
	lastHeardMinutes = Math.floor( ((now - then) / 1000) / 60 );

	stationLastHeard = findStation(username).find('.last-heard');
	stationLastHeard.attr('data-last-heard', Math.floor(lastHeard));
	stationLastHeard.html(lastHeardText(lastHeardMinutes));
	updatePresence(username, lastHeardMinutes);
}

// display station last heard time
function showLastHeard(station) {
	lastHeard = $(station).find('.last-heard').attr('data-last-heard');
    
	if ( lastHeard == null ) {
		lastHeard = 0;
	}

	now = new Date();
	then = new Date(lastHeard * 1000);
	lastHeardMinutes = Math.floor( ((now - then) / 1000) / 60 );

	$(station).find('.last-heard').html(lastHeardText(lastHeardMinutes));
}

// update station last msg time based on given
// username and minutes since last msg'd
function setLastMsgHeard(username, lastMsg) {
	stationLastHeard = findStation(username).find('.last-heard');
	stationLastHeard.attr('data-last-msg', Math.floor(lastMsg));
}

// display station last heard msg time
function showLastMsgHeard(station) {
	lastMsg = $(station).find('.last-heard').attr('data-last-msg');
    
	if ( lastMsg == null ) {
		lastMsg = 0;
	}

	now = new Date();
	then = new Date(lastMsg * 1000);
	lastMsgMinutes = Math.floor( ((now - then) / 1000) / 60 );

	$(station).find('.last-heard').html(lastHeardText(lastMsgMinutes));
}

// mark station as read based on username
function markRead(username) {
	stationChatName = findStation(username).find('.chat-name');

	if ( stationChatName.length > 0 && stationChatName.hasClass('unread') ) {
		stationChatName.removeClass('unread');
		// increment stored unread count
		unreadCount = parseInt( $('#unread-count').attr('data-unread-count') );
		unreadCount--;
		$('#unread-count').attr('data-unread-count', unreadCount);

		// update and show/hide unread count
		if ( unreadCount > 0 ) {
			$('#unread-count').html('(' + unreadCount + ')');
			$('#unread-count').show();
		}
		else {
			$('#unread-count').hide();
		}
	}
}

// mark stations as unread based on username
function markUnread(username) {
	stationChatName = findStation(username).find('.chat-name');

	if ( stationChatName.length > 0 && !stationChatName.hasClass('unread') ) {
		stationChatName.addClass('unread');
		// increment stored unread count
		unreadCount = parseInt( $('#unread-count').attr('data-unread-count') );
		unreadCount++;
		$('#unread-count').attr('data-unread-count', unreadCount);

		// update and show/hide unread count
		if ( unreadCount > 0 ) {
			$('#unread-count').html('(' + unreadCount + ')');
			$('#unread-count').show();
		}
		else {
			$('#unread-count').hide();
		}
	}
}

function selectedTab() {
	tab = $('.tab.selected').attr('id');

	if ( tab == 'tab-conversations' ) {
		return 'conversations';
	}
	else if ( tab == 'tab-activity' ) {
		return 'activity';
	}
}

// on click event handler for stations div
function stationClick() {
	var username = $(this).attr('name');
	$.post('/stations', {user: username}, function() {
		window.location = '/chat?' + $('.tab.selected').attr('id');
	});
}

// on click event handler for station delete icon
function stationDeleteClick(event) {
	var username = $(this).parent().attr('name');
    socket.emit('remove-conversation', {username: username});
    // prevent event bubble up to parent station element
    event.stopPropagation();
}

// sort stations in ascending order by last heard time
function sortStations() {
	var stations = $('.station').not('.original-hidden');

	stations.sort(function(stationA, stationB) {
		stationALastHeard = parseInt( $(stationA).find('.last-heard').attr('data-last-heard') );
		stationBLastHeard = parseInt( $(stationB).find('.last-heard').attr('data-last-heard') );
		return stationBLastHeard - stationALastHeard;
	});

	$('.station').not('.original-hidden').detach();
	stations.appendTo('.content');
}



