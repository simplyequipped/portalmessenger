        
        function newChatMessage(msg) {
            newMsg = $(".original-hidden").clone();
            newMsg.attr('id', msg.id)
            newMsg.addClass('chat-msg-' + msg.type);
            newMsg.find('.chat-time').attr('data-timestamp', msg.time);
            newMsg.find('.chat-time').html(timeString(msg.time));
            newMsg.find('.chat-msg').html(msg.text);

            if ( msg.sent == null ) {
                newMsg.find('.chat-status').remove();
            }
            else {
                newMsg.find('.chat-status').html(msg.sent);
            }

            newMsg.removeClass("original-hidden");
            newMsg.appendTo(".chat-messages");
        }

        function setTxStatus(id, tx_status) {
			if ( $('#' + id).find('.chat-status').length == 0 ) {
				$('.original-hidden').find('.chat-status').clone().appendTo('#' + id)
			}
            $('#'+ id).find('.chat-status').html(tx_status);
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

        function sendMsg(msg_text) {
            socket.emit('msg', {msg: msg_text});
        }

		function setLastHeard(last_heard) {
			now = new Date();
			then = new Date(last_heard * 1000);

			last_heard_minutes = Math.floor( ((now - then) / 1000) / 60 );

			lastHeardElement = $('.last-heard');
			lastHeardElement.html(lastHeardText(last_heard_minutes));
			lastHeardElement.attr('data-last-heard', Math.floor(last_heard));
			updatePresence(last_heard_minutes);
		}

		function updatePresence(last_heard_minutes) {
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



