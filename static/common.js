		
		function urlParam(name){
			var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
			return decodeURIComponent(results[1]) || 0;
		}

		function lastHeardText(minutes) {
			var text = '';
			if ( minutes < 60 ) {
				num = minutes;
				text = String(num) + ' minute';
			}
			else if ( minutes < 60 * 24 ) {
				num = Math.floor(minutes / 60);
				text = String(num) + ' hour';
			}
			else {
				num = Math.floor(minutes / (60 * 24));
				text = String(num) + ' day';
			}

			// plural
			if ( num > 1 ) {
				text = text + 's'
			}

			return text + ' ago';
		}

