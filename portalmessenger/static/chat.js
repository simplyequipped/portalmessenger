function newChatMessage(msg) {
	newMsg = $(".original-hidden").clone();
	newMsg.attr('id', msg.id)
	newMsg.addClass('chat-msg-' + msg.type);
	newMsg.find('.chat-time').attr('data-timestamp', msg.time);
	newMsg.find('.chat-time').html(timeString(msg.time));
	newMsg.find('.chat-msg').html(msg.text);

	//TODO
	//if ( msg.encrypted != null ) {
	//	if ( msg.type == 'rx' ) {
	//		newMsg.find('.chat-time').prepend('<span class="encrypted-icon">&nbsp;</span>');
	//	}
	//	else if ( msg.type == 'tx' ) {
	//		newMsg.find('.chat-time').append('<span class="encrypted-icon">&nbsp;</span>');
	//	}
	//}

	if ( msg.status == 'sent' || msg.status == 'received' ) {
		newMsg.find('.chat-status').remove();
	}
	else if ( msg.status != null ) {
		upperCaseStatus = msg.status.charAt(0).toUpperCase() + msg.status.slice(1).toLowerCase();
		
		if ( msg.error != null ) {
			upperCaseStatus += ', ' + msg.error.toLowerCase();
		}
		
		newMsg.find('.chat-status').html(upperCaseStatus);
	}

	newMsg.removeClass("original-hidden");
	newMsg.appendTo(".chat-messages");
}

function setTxStatus(id, tx_status) {
	upperCaseStatus = tx_status.charAt(0).toUpperCase() + tx_status.slice(1).toLowerCase();

	if ( $('#' + id).find('.chat-status').length == 0 ) {
		$('.original-hidden').find('.chat-status').clone().appendTo('#' + id);
	}

	$('#'+ id).find('.chat-status').html(upperCaseStatus);

	if ( tx_status == 'sent' ) {
		setTimeout(function () {
			removeTxStatus(id);
		}, 5000);
	}
}

function removeTxStatus(id) {
	$('#'+ id).find('.chat-status').remove();
}

function scrollChat() {
	scrollDiv = $(".chat-messages");
	scrollDiv.scrollTop(scrollDiv.prop("scrollHeight"));
}

function getPresence() {
	if ( $('.presence-indicator').hasClass("presence-active") ) {
		return "active";
	}
	else if ( $(".presence-indicator").hasClass("presence-inactive") ) {
		return "inactive";
	}
	else if ( $(".presence-indicator").hasClass("presence-unknown") ) {
		return "unknown";
	}
	else {
		return "none";
	}
}

function setPresence(presence) {
	currentPresence = getPresence();

	if ( currentPresence != "none" ) {
		$('.presence-indicator').removeClass("presence-" + currentPresence);
	}

	$('.presence-indicator').addClass("presence-" + presence);
}

function setLastHeard(last_heard) {
	now = new Date();
	then = new Date(last_heard * 1000);

	last_heard_minutes = Math.floor( ((now - then) / 1000) / 60 );

	lastHeardElement = $('.last-heard');
	lastHeardElement.html(lastHeardText(last_heard_minutes));
	lastHeardElement.attr('data-last-heard', Math.floor(last_heard));
	setPresence(presenceText(last_heard_minutes));
}

function sortChat() {
	var messages = $('.chat-msg-rx, .chat-msg-tx')

	messages.sort(function(msgA, msgB) {
		msgATime = parseInt( $(msgA).find('.chat-time').attr('data-timestamp') );
		msgBTime = parseInt( $(msgB).find('.chat-time').attr('data-timestamp') );
		return msgATime - msgBTime;
	});

	$('.chat-msg-rx, .chat-msg-tx').detach();
	messages.appendTo('.chat-messages');
}
