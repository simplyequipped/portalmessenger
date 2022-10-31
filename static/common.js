		
		function urlParam(name){
			var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
			return decodeURIComponent(results[1]) || 0;
		}

