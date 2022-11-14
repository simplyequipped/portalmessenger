
		// construct new station element based on given station data
		function newStation(station) {
			stationElement = $('.station.original-hidden').clone();
			stationElement.attr('name', station.username)
			stationElement.find('.chat-name').html(station.username);
			stationElement.click(stationClick)
			stationElement.removeClass('original-hidden');
			stationElement.appendTo('.content');
			setLastHeard(station.username, station.time);
		}

		// construct new conversation station element based on given username
		function newConversation(username) {
			stationElement = $('.station.original-hidden').clone();
			stationElement.attr('name', username)
			stationElement.find('.chat-name').html(username);
			stationElement.click(stationClick)
			stationElement.removeClass('original-hidden');
			stationElement.appendTo('.content');
		}

		// create or update spot stations sent from the server
		function handleSpot(station) {
			if ( findStation(station.username).length == 0 ) {
				newStation(station);
				stationElement = findStation(station.username);
				stationElement.addClass('spot');

				if ( selectedTab() == 'conversations' ) {
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

				if ( selectedTab() == 'activity' ) {
					stationElement.hide();
				}
			}
			else {
				setLastHeard(station.username, station.time);
				findStation(station.username).addClass('conversation');
			}

			if ( station.unread ) {
				markUnread(station.username);
			}
			else {
				markRead(station.username);
			}
		}

		// find a return the station DOM element based on given username 
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

		// determine and set presence based on minutes since last heard
		function updatePresence(username, last_heard_minutes) {
			setPresence(username, presenceText(last_heard_minutes));
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

		// mark station as read based on username
		function markRead(username) {
			stationChatName = findStation(username).find('.chat-name');

			if ( stationChatName.hasClass('unread') ) {
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

			if ( !stationChatName.hasClass('unread') ) {
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
            	window.location = '/chat';
			});
		}

		function conversationHover() {
			if ( selectedTab() == 'conversations' ) {
				console.log('hover');
				$(this).find('.last-heard').toggle();
				$(this).find('.icon-conversation-settings').toggle();
			}
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



