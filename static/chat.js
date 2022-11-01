        
        function newChatMessage(msg) {
            newMsg = $(".original-hidden").clone();
            newMsg.attr('id', msg.id)
            newMsg.addClass('chat-msg-' + msg.type);
            newMsg.find('.chat-time').html(msg.time);
            newMsg.find('.chat-msg').html(msg.text);

            if ( msg.tx_status == null ) {
                newMsg.find('.chat-status').remove();
            }
            else {
                newMsg.find('.chat-status').html(msg.tx_status);
            }

            newMsg.removeClass("original-hidden");
            newMsg.appendTo(".chat-messages");
            scrollChat();
        }

        function setTxStatus(id, tx_status) {
			if ( $('#' + id).find('chat-status').length == 0 ) {
				$('.original-hidden').find('chat-status').clone().appendTo('#' + id)
			}
            $('#'+ id).find('chat-status').html(tx_status);
        }

        function removeTxStatus(id) {
            $('#'+ id).find('chat-status').remove();
        }

        function initChat(user_data) {
            console.log(user_data.username);
            $('.chat-name').html(user_data.username);
            $('.last-heard').html('Last heard ' + user_data.heard + ' ago');
            setPresence(user_data.presence);

            $.each(user_data.history, function(index, value) {
                newChatMessage(value);
            });
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

			if ( currentPresence !== "none" ) {
				$('.presence-indicator').removeClass("presence-" + currentPresence);
			}

			$('.presence-indicator').addClass("presence-" + presence);
		}

        function sendMsg(msg_text) {
            socket.emit('tx msg', {msg: msg_text})
        }

