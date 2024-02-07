// construct new station element based on given station data
function newStation(station) {
	stationElement = $('.station.original-hidden').clone();
	stationElement.attr('name', station.username)
	stationElement.find('.chat-name').html(station.username);
	//stationElement.click(stationClick)
	stationElement.removeClass('original-hidden');
	stationElement.appendTo('.content');
	setLastHeard(station.username, station.time);
    setNetworkData(station);
}

// create or update stations sent from the server
function handleStation(station) {
	if ( findStation(station.username).length == 0 ) {
		newStation(station);
	}
	else {
		setLastHeard(station.username, station.time);
        setNetworkData(station);
	}
}

// find and return the station DOM element based on given username 
function findStation(username) {
	return $(".station[name='" + username + "']");
}

// update station network data
function setNetworkData(station) {
	stationElement = findStation(station.username);
    stationElement.find('.grid').html(station.grid);
    stationElement.find('.snr').html(station.snr);
    stationElement.find('.distance').html(station.distance);
    stationElement.find('.time-str').html(station.time_str);
    stationElement.find('.speed').html(station.speed);
    stationElement.find('.hearing').html(station.hearing);
    stationElement.find('.heard-by').html(station.heard_by);
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

