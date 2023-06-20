// construct new station element based on given station data
function newStation(station) {
	stationElement = $('.station.original-hidden').clone();
	stationElement.attr('name', station.username)
	stationElement.find('.chat-name').html(station.username);
	//stationElement.click(stationClick)
	stationElement.removeClass('original-hidden');
	stationElement.appendTo('.content');
	setLastHeard(station.username, station.time);
}

// create or update spot stations sent from the server
function handleStation(station) {
	if ( findStation(station.username).length == 0 ) {
		newStation(station);
		stationElement = findStation(station.username);
		stationElement.addClass('spot');
	}
	else {
		setLastHeard(station.username, station.time);
		findStation(station.username).addClass('spot');
	}
}

// find and return the station DOM element based on given username 
function findStation(username) {
	return $(".station[name='" + username + "']");
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
}

// on click event handler for stations div
function stationClick() {
	$(this).find('.station-details').toggle();
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

