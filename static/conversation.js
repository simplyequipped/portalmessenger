
		function newConversation(username) {
			newConv = $(".original-hidden").clone();
			newConv.attr("name", username)
			newConv.find(".chat-name").html(username);
			newConv.click(conversationClick)
			newConv.removeClass("original-hidden");
			newConv.appendTo(".content");
		}

		function findConversation(username) {
			return $(".conversation[name='" + username + "']");
		}

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

		function setPresence(username, presence) {
			conv = findConversation(username);
			presenceElement = conv.find('.presence-indicator');
			currentPresence = getPresence(username);

			if ( getPresence(username) !== "none" ) {
				presenceElement.removeClass("presence-" + currentPresence);
			}

			presenceElement.addClass("presence-" + presence);
		}

		function setLastHeard(username, last_heard) {
			findConversation(username).find('.last-heard').html(last_heard);
		}

		function markRead(username) {
			conv = findConversation(username);
			chatNameElement = conv.find('.chat-name');

			if ( chatNameElement.hasClass('unread') ) {
				chatNameElement.removeClass('unread');
			}
		}

		function markUnread(username) {
			conv = findConversation(username);
			chatNameElement = conv.find('.chat-name');

			if ( !chatNameElement.hasClass('unread') ) {
				chatNameElement.addClass('unread');
			}
		}

		function conversationClick() {
		    var username = $(this).attr("name");
            $.post('/conversations', {user: username}, function() {
            	window.location = "/chat";
			});
		}


