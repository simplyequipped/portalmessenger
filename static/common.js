		
		function urlParam(name){
			var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
			return decodeURIComponent(results[1]) || 0;
		}

		function lastHeardText(minutes) {
			var text = '';

            // now (less than 1 minute)
			if ( minutes < 1 ) {
				num = null;
				text = 'Now';
			}
            // minutes
			else if ( minutes < 60 ) {
				num = minutes;
				text = String(num) + ' minute';
			}
            // hours
			else if ( minutes < 60 * 24 ) {
				num = Math.floor(minutes / 60);
				text = String(num) + ' hour';
			}
            // days
			else if ( minutes < 60 * 24 * 365 ) {
				num = Math.floor((minutes / 60) / 24);
				text = String(num) + ' day';
			}
            // over a year
			else {
				num = null;
				text = 'Never';
			}

			// handle plural
			if ( num != 1 && num != null) {
				text = text + 's'
			}

            if ( num == null ) {
                return text;
            }
            else {
			    return text + ' ago';
            }
		}

		function presenceText(minutes) {
			if ( minutes < 10 ) {
				return 'active';
			}
			else if ( minutes < 60 ) {
				return 'inactive';
			}
			else {
				return 'unknown';
			}
		}

function timeString(unix_timestamp) {
	// unix = seconds, js = milliseconds
	js_timestamp = unix_timestamp * 1000
	now = new Date();
	then = new Date(js_timestamp);
	a_day = 1000 * 60 * 60 * 24 // in milliseconds
	a_week = a_day * 7 // in milliseconds
	a_year = a_day * 365 // in milliseconds

	// always include 12-hour time with am/pm
	options = {
		'hour': 'numeric',
		'hour12': true,
		'minute': 'numeric'
	};


	// earlier this week but not into the previous week, include weekday
	if ( (now - then < a_day) && (then.getDay() == now.getDay()) ) {
		// prevent fall through to next condition
	}
	// earlier this week but not into the previous week, include weekday
	else if ( (now - then < a_week) && (then.getDay() < now.getDay()) ) {
		options.weekday = 'short';
	}
	// within a year but not into the previous year, include month and day
	else if ( (now - then < a_year) && (now.getYear() == then.getYear()) ) {
		options.month = 'short';
		options.day = 'numeric';
	}
	// over a year ago or into the previous year, include month, day and year
	//if ( (now - then >= a_year) || (now.getYear() != then.getYear()) ) {
	else {
		options.month = 'short';
		options.day = 'numeric';
		options.year = 'numeric';
	}

	return then.toLocaleString('en-US', options);
}


