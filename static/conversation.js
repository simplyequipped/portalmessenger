
		function newConversation(username, presence) {
			newConv = $(".original-hidden").clone();
			newConv.attr("name", username)
			newConv.find(".chat-name").html(username);
			newConv.click(conversationClick)
			newConv.removeClass("original-hidden");
			newConv.appendTo(".content");
			setPresence(username, presence);
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
			currentPresence = getPresence(username);

			if ( getPresence(username) !== "none" ) {
				conv.find('.presence-indicator').removeClass("presence-" + currentPresence);
			}

			conv.find('.presence-indicator').addClass("presence-" + presence);
		}

		function conversationClick() {
		    var username = $(this).attr("name");
            console.log(username)
            
            $.post('/conversations', {user: username});
            //socket.emit('user', {user: username});
            window.location = "/chat";
		}


