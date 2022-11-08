
		// construct new conversation based on given username and minutes since last heard
		function newConversation(username, last_heard, unread) {
			newConv = $(".original-hidden").clone();
			newConv.attr("name", username)
			newConv.find(".chat-name").html(username);
			newConv.click(conversationClick)
			newConv.removeClass("original-hidden");
			newConv.appendTo(".content");
			setLastHeard(username, last_heard);

			if ( unread !== undefined && unread === true) {
				markUnread(username);
			}
		}

		// find a return the conversation DOM element based on given username 
		function findConversation(username) {
			return $(".conversation[name='" + username + "']");
		}

		// get conversation presence status based on given username
		function getPresence(username) {
			conv = findConversation(username)
			if ( conv.find('.presence-indicator').hasClass("presence-active") ) {
				return "active";
			}
			else if ( conv.find(".presence-indicator").hasClass("presence-inactive") ) {
				return "inactive";
			}
			else if ( conv.find(".presence-indicator").hasClass("presence-unknown") ) {
				return "unknown";
			}
			else {
				return "none";
			}
		}

		// set conversation to given presence based on given username
		function setPresence(username, presence) {
			conv = findConversation(username);
			presenceElement = conv.find('.presence-indicator');
			currentPresence = getPresence(username);

			if ( getPresence(username) !== "none" ) {
				presenceElement.removeClass("presence-" + currentPresence);
			}
			presenceElement.addClass("presence-" + presence);
		}

		// determine and set presence based on minutes since last heard
		function updatePresence(username, last_heard_minutes) {
			setPresence(username, presenceText(last_heard_minutes));
		}

		// update converation last heard time and presence based on given
		// username and minutes since last heard
		function setLastHeard(username, last_heard) {
			now = new Date();
			then = new Date(last_heard * 1000);
			last_heard_minutes = Math.floor( ((now - then) / 1000) / 60 );

			convLastHeard = findConversation(username).find('.last-heard');
			convLastHeard.attr('data-last-heard', Math.floor(last_heard));
			convLastHeard.html(lastHeardText(last_heard_minutes));
			updatePresence(username, last_heard_minutes);
		}

		// mark conversation as read based on username
		function markRead(username) {
			conv = findConversation(username);
			chatNameElement = conv.find('.chat-name');

			if ( chatNameElement.hasClass('unread') ) {
				chatNameElement.removeClass('unread');
			}
		}

		// mark conversation as unread based on username
		function markUnread(username) {
			conv = findConversation(username);
			chatNameElement = conv.find('.chat-name');

			if ( !chatNameElement.hasClass('unread') ) {
				chatNameElement.addClass('unread');
			}
		}

		// on click event handler for conversations div
		function conversationClick() {
		    var username = $(this).attr('name');
            $.post('/stations', {user: username}, function() {
            	window.location = '/chat';
			});
		}

		// sort conversations in ascending order by last heard time
		function sortConversations() {
			var conversations = $('.conversation').not('.original-hidden');

			conversations.sort(function(convA, convB) {
				convALastHeard = parseInt( $(convA).find('.last-heard').attr('data-last-heard') );
				convBLastHeard = parseInt( $(convB).find('.last-heard').attr('data-last-heard') );
				return convBLastHeard - convALastHeard;
			});

			$('.conversation').not('.original-hidden').detach();
			conversations.appendTo('.content');
		}



